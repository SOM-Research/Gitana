#!/usr/bin/env python
# -*- coding: utf-8 -*-
from util.db_util import DbUtil
from importers.vcs.git.git_dao import GitDao


class DependencyUtils(object):
    """
    Utilities for dependency extractor
    """

    def __init__(self, config, project_name, repo_name, logger):
        """
        :type config: dict
        :param config: the DB configuration file

        :type project_name: str
        :param project_name: the name of an existing project in the DB

        :param repo_name: repo name
        :type repo_name: str

        :type logger: logger object to log messages
        :param logger: logging.Logger
        """
        try:
            self._config = config
            self._project_name = project_name
            self._repo_name = repo_name
            self._logger = logger
            self._db_util = DbUtil()
            self._cnx = self._db_util.get_connection(self._config)
            self._git_dao = GitDao(config, logger)
        except:
            self._logger.error("DB connection failure")
            raise

    def insert_repository(self):
        """
        insert repository into database
        """
        project_id = self._git_dao.select_project_id(self._project_name)
        self._git_dao.insert_repo(project_id, self._repo_name)

    def insert_dependencies(self, source_file, target_files):
        """
        inserts source to target file dependencies into datatable
        :param source_file: source file path
        :type source_file: str

        :param target_files: list of dependency target files
        :type target_files: list
        """
        cursor = self._cnx.cursor()

        repo_id = self._db_util.select_repo_id(self._cnx, self._repo_name, self._logger)

        # get source fileid by creating it if not exists
        source_file_id = self._git_dao.select_file_id(repo_id, source_file)
        if not source_file_id:
            self._git_dao.insert_file(repo_id, source_file)
            source_file_id = self._git_dao.select_file_id(repo_id, source_file)

        query = "INSERT IGNORE INTO file_dependency(repo_id, source_file_id, target_file_id) VALUES (%s, %s, %s)"

        for target_file in target_files:

            # get target fileid by creating it if not exists
            target_file_id = self._git_dao.select_file_id(repo_id, target_file)
            if not target_file_id:
                self._git_dao.insert_file(repo_id, target_file)
                target_file_id = self._git_dao.select_file_id(repo_id, target_file)

            args = [repo_id, source_file_id, target_file_id]
            cursor.execute(query, args)

        self._cnx.commit()
        cursor.close()
