#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import re

# language specific regex to find all dependency modules in the source
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

    def __init__(self, logger):
        """
        initiator
        :param logger: logger object to log messages
        :type: logger: logging.Logger
        """
        self._logger = logger

    def get_dependencies(self, file_path, extra_paths):
        """
        Parse python source files for imported module dependencies
        :return: list of imported dependency module files

        :param file_path: source file path
        :type file_path: str

        :param extra_paths: list of extra directories to look for target files
        :type extra_paths: list
        """
        modules = []

        file_ext = file_path.split('.')[-1]
        if file_ext not in LANG_SPEC_REGEX:
            self._logger.warn('%s file not yet supported.', file_path)
            return modules

        regex = re.compile(LANG_SPEC_REGEX[file_ext])
        source_file = open(file_path)
        for line in source_file.readlines():

            if regex.match(line):
                from_module, import_module = regex.match(line).groups()
                module_path = self.get_module_file(from_module, import_module, extra_paths)

                if module_path:
                    modules.append(module_path)

        source_file.close()
        return modules

    def get_module_file(self, from_module, import_module, extra_paths):
        """
        :param from_module: from module name
        :type from_module: str

        :param import_module: import module name
        :type import_module: str

        :param extra_paths: additional directory paths inside git repo to look for dependency target files
        :type extra_paths: list

        :return: return dependency source file if exists else None
        """
        # walk through all target directory paths for dependency target files
        for source_dir in extra_paths:

            source_path = ''
            if from_module:
                # cover: "from module.submodule import supersubmodule"
                # case: module/submodule.py
                source_path = os.path.join(
                    source_dir,
                    os.path.join(*from_module.split('.')))
                if os.path.exists('%s.py' % source_path):
                    return '%s.py' % source_path

            if source_path:
                # case: "from module.submodule import supersubmodule"
                # cover: module/submodule/supersubmodule.py
                source_path = os.path.join(source_path, '%s.py' % import_module)
            else:
                # case: "import module"
                # cover: module.py
                source_path = os.path.join(source_dir, '%s.py' % import_module)

            if os.path.exists(source_path):
                return source_path

            self._logger.debug('Ignoring external dependency file: %s', source_path)
