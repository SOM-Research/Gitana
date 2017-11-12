#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'valerio cosentino'

from datetime import datetime
import multiprocessing

from querier_git import GitQuerier
from importers.vcs.git.git2db_extract_reference import Git2DbReference
from util import multiprocessing_util
from git_dao import GitDao
from util.logging_util import LoggingUtil


class Git2DbUpdate():
    """
    This class handles the update of Git data
    """

    NUM_PROCESSES = 5

    def __init__(self, db_name, project_name,
                 repo_name, git_repo_path, before_date,
                 num_processes, config, log_root_path):
        """
        :type db_name: str
        :param db_name: the name of an existing DB

        :type project_name: str
        :param project_name: the name of an existing project in the DB

        :type repo_name: str
        :param repo_name: the name of the Git repository to import

        :type git_repo_path: str
        :param git_repo_path: the local path of the Git repository

        :type before_date: str
        :param before_date: import data before date (YYYY-mm-dd)

        :type num_processes: int
        :param num_processes: number of processes to import the data (default 5)

        :type config: dict
        :param config: the DB configuration file

        :type log_root_path: str
        :param log_root_path: the log path
        """
        self._log_path = log_root_path + "import-git-" + db_name + "-" + project_name + "-" + repo_name
        self._git_repo_path = git_repo_path
        self._project_name = project_name
        self._db_name = db_name
        self._repo_name = repo_name
        self._before_date = before_date
        self._existing_refs = []

        if num_processes:
            self._num_processes = num_processes
        else:
            self._num_processes = Git2DbUpdate.NUM_PROCESSES

        config.update({'database': db_name})
        self._config = config

        self._logging_util = LoggingUtil()

        self._logger = None
        self._fileHandler = None
        self._querier = None
        self._dao = None

    def _update_existing_references(self, repo_id, import_type):
        # updates existing references in the DB
        cursor = self._dao.get_cursor()
        query = "SELECT c.sha, lc.ref_id " \
                "FROM commit c " \
                "JOIN (SELECT ref_id, max(commit_id) as last_commit_id_in_ref " \
                "FROM commit_in_reference WHERE repo_id = %s GROUP BY ref_id) as lc " \
                "ON c.id = lc.last_commit_id_in_ref"
        arguments = [repo_id]
        self._dao.execute(cursor, query, arguments)

        queue_references = multiprocessing.JoinableQueue()
        results = multiprocessing.Queue()

        # Start consumers
        multiprocessing_util.start_consumers(self._num_processes, queue_references, results)

        row = self._dao.fetchone(cursor)
        while row:
            sha = row[0]
            ref_id = row[1]
            row = self._dao.fetchone(cursor)

            ref_name = self._dao.select_reference_name(repo_id, ref_id)

            for reference in self._querier.get_references():
                reference_name = reference[0]
                if reference_name == ref_name:
                    self._existing_refs.append(ref_name)

                    git_ref_extractor = Git2DbReference(self._db_name, repo_id, self._git_repo_path,
                                                        self._before_date, import_type, reference[0], sha,
                                                        self._config, self._log_path)

                    queue_references.put(git_ref_extractor)
                    break

        self._dao.close_cursor(cursor)

        # Add end-of-queue markers
        multiprocessing_util.add_poison_pills(self._num_processes, queue_references)

        # Wait for all of the tasks to finish
        queue_references.join()

    def _update_repo(self, repo_id, import_type):
        # updates Git data
        self._update_existing_references(repo_id, import_type)

    def _get_import_type(self, repo_id):
        # gets import type
        import_type = 1
        import_type += \
            self._dao.line_detail_table_is_empty(repo_id) + self._dao.file_modification_patch_is_empty(repo_id)
        return import_type

    def update(self):
        """
        updates the Git data stored in the DB
        """
        try:
            self._logger = self._logging_util.get_logger(self._log_path)
            self._fileHandler = self._logging_util.get_file_handler(self._logger, self._log_path, "info")

            self._logger.info("Git2DbUpdate started")
            start_time = datetime.now()

            self._querier = GitQuerier(self._git_repo_path, self._logger)
            self._dao = GitDao(self._config, self._logger)

            repo_id = self._dao.select_repo_id(self._repo_name)
            self._update_repo(repo_id, self._get_import_type(repo_id))
            self._dao.restart_connection()
            self._dao.fix_commit_parent_table(repo_id)

            end_time = datetime.now()
            minutes_and_seconds = self._logging_util.calculate_execution_time(end_time, start_time)
            self._logger.info("Git2DbUpdate finished after " + str(minutes_and_seconds[0]) +
                              " minutes and " + str(round(minutes_and_seconds[1], 1)) + " secs")
            self._logging_util.remove_file_handler_logger(self._logger, self._fileHandler)
        except:
            self._logger.error("Git2DbUpdate failed", exc_info=True)
        finally:
            if self._dao:
                self._dao.close_connection()
