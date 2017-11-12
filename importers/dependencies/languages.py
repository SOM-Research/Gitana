#!/usr/bin/env python
# -*- coding: utf-8 -*-
from importers.vcs.git.querier_git import GitQuerier
import os
import pprint
import re

# language specific regex to find all dependency target_files in the source
LANG_SPEC_REGEX = {

    # regex to parse import statements inside python source content
    #   from abc.lmn import pqr
    #   from abc.lmn import pqr as xyz
    #   import abc
    #   import abc as xyz
    'py': r'(?m)^(?:from[ ]+(\S+)[ ]+)?import[ ]+(\S+)(?:[ ]+as[ ]+\S+)?[ ]*$',

    'java': r'import[ ]+(\S+)',
}


class Parser(object):
    """
    Parse source file for dependency information
    """

    def __init__(self, repo_path, references, extra_paths, logger):
        """
        initiator
        :param repo_path: directory path to git repo
        :type repo_path: str

        :param references: list of git references from where source dependency info loaded. By default all.
        :type references: list

        :param extra_paths: list of extra directories to look for target files
        :type extra_paths: list

        :param logger: logger object to log messages
        :type: logger: logging.Logger
        """
        self.repo_path = repo_path
        self.references = references
        self._logger = logger
        self._git_querier = GitQuerier(repo_path, logger)

        # add git repo path also to list of extra paths
        self.extra_paths = self.consolidate_extra_paths(
            extra_paths + [repo_path])

    def consolidate_extra_paths(self, extra_paths):
        """
        filter out valid paths with respect to git repo path

        :param extra_paths: list of extra directories to look for target files
        :type extra_paths: list

        :return: list of relative paths to the git repo path
        """
        relative_paths = []

        for path in extra_paths:
            if os.path.exists(path):

                # retrieve relative path with respect to git repo path
                relative_path = os.path.abspath(path).replace(os.path.abspath(self.repo_path), '').lstrip('\\')
                self._logger.debug('Extra path and its relative repo path: %s %s', path, relative_path)
                relative_paths.append(relative_path)

        return relative_paths

    def get_all_dependencies(self):
        """
        Parse python source files for imported module dependencies
        :return: list of dependency target files for each source file
        """
        source_to_targets = []

        for ref in self._git_querier.get_references():
            ref_name = ref[0]

            self._logger.info('*' * 100)
            self._logger.info('Processing git-reference: %s', ref_name)
            self._logger.info('*' * 100)

            if self.references and ref_name not in self.references:
                continue

            # retrieve all files for each git reference
            self.files = self._git_querier.get_files_in_ref(ref_name)

            for source_file in self.files:

                target_files = self.get_dependency_for_file(ref_name, source_file)
                # do not call insert_dependencies with a empty dependency list
                if not target_files:
                    continue

                self._logger.info('Source file: %s', source_file)
                self._logger.info('Dependencies: %s', pprint.pformat(target_files, indent=4))

                source_to_targets.append([
                    ref_name,
                    source_file,
                    target_files
                ])

        return source_to_targets

    def get_dependency_for_file(self, ref_name, file_path):
        """
        :param ref_name: git reference name
        :type ref_name: str

        :param file_path: source file path
        :type file_path: str

        :return: list of dependency files for a single source file
        """
        target_files = []

        file_ext = file_path.split('.')[-1]
        lang_spec = LANG_SPEC_REGEX.get(file_ext)
        if not lang_spec:
            self._logger.debug('File not supported: %s', file_path)
            return target_files

        regex = re.compile(lang_spec)
        source_file = self._git_querier.get_file_content(ref_name, file_path)
        for line in source_file.split('\n'):

            # strip unnecessary spaces at the start and end of line
            line = line.strip()

            if regex.match(line):
                regex_groups = regex.match(line).groups()

                # Languages: java
                if len(regex_groups) == 1:
                    module_path = self.get_java_file(*regex_groups)

                # Languages: python
                elif len(regex_groups) == 2:
                    module_path = self.get_python_file(*regex_groups)

                if module_path:
                    target_files.append(module_path)

        return target_files

    def get_python_file(self, from_module, import_module):
        """
        :param from_module: from module name
        :type from_module: str

        :param import_module: import module name
        :type import_module: str

        :return: return dependency source file if exists else None
        """
        # walk through all target directory paths for dependency target files
        # @todo: replace / with separator used in git repo to support multiple OS

        for source_dir in self.extra_paths:

            # convert windows source dir path to linux one
            source_dir = source_dir.replace('\\', '/')

            source_path = ''

            # cover: "from module.submodule import someclass"
            # case: module/submodule.py
            if from_module:
                source_path = from_module.split('.')

                # prepend relative extra path if exists
                if source_dir:
                    source_path.insert(0, source_dir)

                source_path = '/'.join(source_path)
                # making sure file exists
                if '%s.py' % source_path in self.files:
                    return '%s.py' % source_path

            # case: "from module.submodule import supersubmodule"
            # cover: module/submodule/supersubmodule.py
            if source_path:
                source_path = [
                    source_path + '/%s.py' % import_module,
                    source_path + '/%s/__init__.py' % import_module]

            # case: "import module"
            # cover: module.py
            else:
                # prepend relative extra path if exists

                # case: "import module.submodule"
                # cover: module.submodule.py
                import_module = import_module.replace('.', '/')

                if source_dir:
                    source_path = [
                        source_dir + '/%s.py' % import_module,
                        source_dir + '/%s/__init__.py' % import_module]
                else:
                    source_path = [
                        '%s.py' % import_module,
                        '%s/__init__.py' % import_module]

            # making sure file exists
            for sp in source_path:
                if sp in self.files:
                    return sp

            self._logger.debug('Ignoring external dependency: %s', source_path)

    def get_java_file(self, import_module):
        """
        :param import_module: import module name
        :type import_module: str

        :return: return dependency source file if exists else None
        """
        # walk through all target directory paths for dependency target files
        for source_dir in self.extra_paths:

            # convert windows source dir path to linux one
            source_dir = source_dir.replace('\\', '/')

            # convert import string "com.company.proj.logger.LoggerUtil;"
            # to com/company/proj/logger/LoggerUtil.java
            source_path = '%s.java' % import_module.replace('.', '/').replace(';', '')

            # making sure file exists
            # self._logger.info('File: %s Files: %s', source_dir + '/' + source_path, self.files)
            source_path = source_dir + '/' + source_path
            if source_path in self.files:
                return source_path

            self._logger.debug('Ignoring external dependency: %s', source_path)
