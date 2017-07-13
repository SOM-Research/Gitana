#!/usr/bin/env python
# -*- coding: utf-8 -*-
from importers.vcs.git.querier_git import GitQuerier
import os
import re

# language specific regex to find all dependency target_files in the source
LANG_SPEC_REGEX = {

    # regex to parse import statements inside python source content
    #   from abc.lmn import pqr
    #   from abc.lmn import pqr as xyz
    #   import abc
    #   import abc as xyz
    'py': r'(?m)^(?:from[ ]+(\S+)[ ]+)?import[ ]+(\S+)(?:[ ]+as[ ]+\S+)?[ ]*$',

    'java': r'',
}


class Parser(object):
    """
    Parse source file for dependency information
    """

    def __init__(self, repo_path, extra_paths, logger):
        """
        initiator
        :param repo_path: directory path to git repo
        :type repo_path: str

        :param extra_paths: list of extra directories to look for target files
        :type extra_paths: list

        :param logger: logger object to log messages
        :type: logger: logging.Logger
        """
        self.repo_path = repo_path
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
                relative_path = os.path.abspath(path).replace(os.path.abspath(self.repo_path), '')
                self._logger.info('Extra path and its relative repo path: %s %s', path, relative_path)
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

            # retrieve all files for each git reference
            self.files = self._git_querier.get_files_in_ref(ref_name)

            for source_file in self.files:

                self._logger.debug('Reference and its file: %s %s', ref_name, source_file)

                target_files = self.get_dependency_for_file(ref_name, source_file)
                # do not call insert_dependencies with a empty dependency list
                if not target_files:
                    continue

                self._logger.info('Source and its dependency files: %s %s', source_file, target_files)
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

        lang_spec = LANG_SPEC_REGEX.get(file_path.split('.')[-1])
        if not lang_spec:
            self._logger.debug('File not supported: %s', file_path)
            return target_files

        regex = re.compile(lang_spec)
        source_file = self._git_querier.get_file_content(ref_name, file_path)
        for line in source_file.split('\n'):

            # strip unnecessary spaces at the start and end of line
            line = line.strip()

            if regex.match(line):
                from_module, import_module = regex.match(line).groups()
                module_path = self.get_module_file(from_module, import_module)

                if module_path:
                    target_files.append(module_path)

        return target_files

    def get_module_file(self, from_module, import_module):
        """
        :param from_module: from module name
        :type from_module: str

        :param import_module: import module name
        :type import_module: str

        :return: return dependency source file if exists else None
        """
        # walk through all target directory paths for dependency target files
        # @todo: replace / with seperator used in git repo to support multiple OS

        for source_dir in self.extra_paths:

            source_path = ''

            # cover: "from module.submodule import someclass"
            # case: module/submodule.py
            if from_module:
                source_path = from_module.split('.')

                # prepend relative extra path if exists
                if source_dir:
                    source_path = [source_dir] + source_path

                source_path = '/'.join(source_path)
                # making sure file exists
                if '%s.py' % source_path in self.files:
                    return '%s.py' % source_path

            # case: "from module.submodule import supersubmodule"
            # cover: module/submodule/supersubmodule.py
            if source_path:
                source_path = source_path + '/%s.py' % import_module

            # case: "import module"
            # cover: module.py
            else:
                # prepend relative extra path if exists
                if source_dir:
                    source_path = source_dir + '/%s.py' % import_module
                else:
                    source_path = '%s.py' % import_module

            # making sure file exists
            if source_path in self.files:
                return source_path

            self._logger.debug('Ignoring external dependency: %s', source_path)
