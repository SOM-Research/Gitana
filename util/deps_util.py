#!/usr/bin/env python
# -*- coding: utf-8 -*-
from importers.vcs.git.git_dao import GitDao
from importers.vcs.git.querier_git import GitQuerier
from util.db_util import DbUtil


class DependencyUtils(object):
    """
    Utilities for dependency extractor
    """

    def __init__(self, config, project_name, repo_name, repo_path, logger):
        """
        :type config: dict
        :param config: the DB configuration file

        :type project_name: str
        :param project_name: the name of an existing project in the DB

        :param repo_name: repo name
        :type repo_name: str

        :param repo_path: git repo path
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
            self._git_querier = GitQuerier(repo_path, logger)
        except:
            self._logger.error("DB connection failure")
            raise

    def load_all_references(self, repo_id):
        """
         load all git branches and tags into database

         :param repo_id: repo id of repo name
         :type repo_id: int
        """
        for reference in self._git_querier.get_references():
            ref_name = reference[0]
            ref_type = reference[1]
            self._git_dao.insert_reference(repo_id, ref_name, ref_type)

    def insert_repository(self):
        """
        insert repository into database
        """
        project_id = self._git_dao.select_project_id(self._project_name)
        self._git_dao.insert_repo(project_id, self._repo_name)

    def insert_dependencies(self, source_to_targets):
        """
        inserts source to target file dependencies into datatable

        :param source_to_targets: source and target files mapping
        :type source_to_targets: nested list
        """
        cursor = self._cnx.cursor()

        repo_id = self._db_util.select_repo_id(self._cnx, self._repo_name, self._logger)

        self.load_all_references(repo_id)

        for ref_name, source_file, target_files in source_to_targets:

            ref_id = self._git_dao.select_reference_id(repo_id, ref_name)

            # get source fileid by creating it if not exists
            source_file_id = self._git_dao.select_file_id(repo_id, source_file)
            if not source_file_id:
                self._git_dao.insert_file(repo_id, source_file)
                source_file_id = self._git_dao.select_file_id(repo_id, source_file)

            for target_file in target_files:

                # get target fileid by creating it if not exists
                target_file_id = self._git_dao.select_file_id(repo_id, target_file)
                if not target_file_id:
                    self._git_dao.insert_file(repo_id, target_file)
                    target_file_id = self._git_dao.select_file_id(repo_id, target_file)

                args = [repo_id, ref_id, source_file_id, target_file_id]

                query = "INSERT IGNORE INTO file_dependency VALUES (%s, %s, %s, %s)"
                cursor.execute(query, args)

        self._cnx.commit()
        cursor.close()
