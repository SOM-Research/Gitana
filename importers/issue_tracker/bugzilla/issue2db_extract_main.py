#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'valerio cosentino'

from datetime import datetime
import multiprocessing

from issue2db_extract_issue import BugzillaIssue2Db
from issue2db_extract_issue_dependency import BugzillaIssueDependency2Db
from querier_bugzilla import BugzillaQuerier
from util import multiprocessing_util
from bugzilla_dao import BugzillaDao
from util.logging_util import LoggingUtil


class BugzillaIssue2DbMain():

    NUM_PROCESSES = 5

    def __init__(self, db_name, project_name,
                 repo_name, type, issue_tracker_name, url, product, before_date, num_processes,
                 config, log_root_path):

        self._log_path = log_root_path + "import-bugzilla-" + db_name + "-" + project_name + "-" + issue_tracker_name
        self._type = type
        self._url = url
        self._product = product
        self._project_name = project_name
        self._db_name = db_name
        self._issue_tracker_name = issue_tracker_name
        self._repo_name = repo_name
        self._before_date = before_date

        if num_processes:
            self._num_processes = num_processes
        else:
            self._num_processes = BugzillaIssue2DbMain.NUM_PROCESSES

        config.update({'database': db_name})
        self._config = config

        self._logging_util = LoggingUtil()

        self._logger = None
        self._fileHandler = None
        self._querier = None
        self._dao = None

    def _pass_list_as_argument(self, elements):
        return '-'.join([str(e) for e in elements])

    def _insert_issue_data(self, repo_id, issue_tracker_id):
        imported = self._dao.get_already_imported_issue_ids(issue_tracker_id, repo_id)
        issues = list(set(self._querier.get_issue_ids(self._before_date)) - set(imported))
        issues.sort()

        intervals = [i for i in multiprocessing_util.get_tasks_intervals(issues, self._num_processes) if len(i) > 0]

        queue_intervals = multiprocessing.JoinableQueue()
        results = multiprocessing.Queue()

        # Start consumers
        multiprocessing_util.start_consumers(self._num_processes, queue_intervals, results)

        for interval in intervals:
            issue_extractor = BugzillaIssue2Db(self._db_name, repo_id, issue_tracker_id, self._url, self._product, interval,
                                       self._config, self._log_path)
            queue_intervals.put(issue_extractor)

        # Add end-of-queue markers
        multiprocessing_util.add_poison_pills(self._num_processes, queue_intervals)

        # Wait for all of the tasks to finish
        queue_intervals.join()

    def _insert_issue_dependencies(self, repo_id, issue_tracker_id):
        issues = self._dao.get_already_imported_issue_ids(issue_tracker_id, repo_id)
        intervals = [i for i in multiprocessing_util.get_tasks_intervals(issues, self._num_processes) if len(i) > 0]

        queue_intervals = multiprocessing.JoinableQueue()
        results = multiprocessing.Queue()

        # Start consumers
        multiprocessing_util.start_consumers(self._num_processes, queue_intervals, results)

        for interval in intervals:
            issue_dependency_extractor = BugzillaIssueDependency2Db(self._db_name, repo_id, issue_tracker_id, self._url, self._product, interval,
                                                            self._config, self._log_path)
            queue_intervals.put(issue_dependency_extractor)

        # Add end-of-queue markers
        multiprocessing_util.add_poison_pills(self._num_processes, queue_intervals)

        # Wait for all of the tasks to finish
        queue_intervals.join()

    def _split_issue_extraction(self):
        project_id = self._dao.select_project_id(self._project_name)
        repo_id = self._dao.select_repo_id(project_id, self._repo_name)
        issue_tracker_id = self._dao.insert_issue_tracker(repo_id, self._issue_tracker_name, self._type)
        self._insert_issue_data(repo_id, issue_tracker_id)

        self._dao.restart_connection()
        self._insert_issue_dependencies(repo_id, issue_tracker_id)

    def extract(self):
        try:
            self._logger = self._logging_util.get_logger(self._log_path)
            self._fileHandler = self._logging_util.get_file_handler(self._logger, self._log_path, "info")

            self._logger.info("BugzillaIssue2DbMain started")
            start_time = datetime.now()

            self._querier = BugzillaQuerier(self._url, self._product, self._logger)
            self._dao = BugzillaDao(self._config, self._logger)

            self._split_issue_extraction()

            end_time = datetime.now()
            minutes_and_seconds = self._logging_util.calculate_execution_time(end_time, start_time)
            self._logger.info("BugzillaIssue2DbMain finished after " + str(minutes_and_seconds[0])
                         + " minutes and " + str(round(minutes_and_seconds[1], 1)) + " secs")
            self._logging_util.remove_file_handler_logger(self._logger, self._fileHandler)
        except:
            self._logger.error("BugzillaIssue2DbMain failed", exc_info=True)
        finally:
            if self._dao:
                self._dao.close_connection()