#!/usr/bin/env python
# -*- coding: utf-8 -*-
from importers.dependencies.languages import Parser
from util.deps_util import DependencyUtils
from util.logging_util import LoggingUtil
import os


class DependencyExtractor(object):
    """
    Extract dependency information for all repo files
    and load into the mysql datatables
    """

    def __init__(self, config, db_name, project_name, repo_name, log_path):
        """
        initializer
        :param config: mysql database config dict
        :type config: dict

        :param log_path: log file path
        :type log_path: str

        :param db_name: mysql database name
        :type db_name: str

        :type project_name: str
        :param project_name: the name of an existing project in the DB

        :param repo_name: git repo name
        :type repo_name: str

        :type log_path: str
        :param log_path: the log path
        """
        self._config = config
        self._project_name = project_name
        self._repo_name = repo_name

        # set database key-val pair in config dict so that to avoid
        #   ProgrammingError: 1046 (3D000): No database selected
        self._config['database'] = db_name

        self._logging_util = LoggingUtil()
        log_path = log_path + "extract-relations-" + db_name + ".log"
        self._logger = self._logging_util.get_logger(log_path)
        self._fileHandler = self._logging_util.get_file_handler(self._logger, log_path, "debug")

    def load_dependencies(self, git_repo_path, extra_paths=[]):
        """
        Extract and load dependency info

        :param git_repo_path: directory path to git repo
        :type git_repo_path: str

        :param extra_paths: additional directory paths inside git repo to look for dependency target files
        :type extra_paths: list
        """
        if not os.path.exists(git_repo_path):
            self._logger.error('Invalid repository path: %s', git_repo_path)
            return

        # exclude invalid and external directories to the repository path
        abs_paths = [git_repo_path]
        for path in extra_paths:
            if os.path.exists(path) and os.path.abspath(git_repo_path) in os.path.abspath(path):
                abs_paths.append(path)
            else:
                self._logger.warn('Ignoring invalid extra-path directory: %s', path)

        source_parser = Parser(self._logger)
        dep_utils = DependencyUtils(self._config, self._project_name, self._repo_name, self._logger)
        dep_utils.insert_repository()

        for dirt, _, files in os.walk(git_repo_path):
            for _file in files:
                source_file = os.path.join(dirt, _file)
                target_files = source_parser.get_dependencies(source_file, abs_paths)

                # do not call insert_dependencies with a empty dependency list
                if not target_files:
                    continue

                self._logger.info('source file: %s and its dependency files: %s', source_file, target_files)
                dep_utils.insert_dependencies(source_file, target_files)
