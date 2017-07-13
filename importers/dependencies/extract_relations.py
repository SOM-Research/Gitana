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

        # set database key-val pair in config dict
        self._config['database'] = db_name

        self._logging_util = LoggingUtil()
        log_path = log_path + "extract-relations-" + db_name + ".log"
        self._logger = self._logging_util.get_logger(log_path)
        self._fileHandler = self._logging_util.get_file_handler(self._logger, log_path, "info")

    def load_dependencies(self, repo_path, references, extra_paths):
        """
        Extract and load dependency info

        :param repo_path: directory path to git repo
        :type repo_path: str

        :param references: list of git references from where source dependency info loaded. By default all.
        :type references: list

        :param extra_paths: additional directory paths inside git repo to look for dependency target files
        :type extra_paths: list
        """
        if not os.path.exists(repo_path):
            self._logger.error('Invalid repository path: %s', repo_path)
            return

        dep_utils = DependencyUtils(self._config, self._project_name, self._repo_name,
                                    repo_path, self._logger)
        dep_utils.insert_repository()

        source_parser = Parser(repo_path, references, extra_paths, self._logger)
        source_to_targets = source_parser.get_all_dependencies()
        dep_utils.insert_dependencies(source_to_targets)
