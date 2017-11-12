#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'valerio cosentino'


from datetime import datetime
import multiprocessing

from issue2db_extract_issue import BugzillaIssue2Db
from issue2db_extract_issue_dependency import BugzillaIssueDependency2Db
from util import multiprocessing_util
from bugzilla_dao import BugzillaDao
from util.logging_util import LoggingUtil


class BugzillaIssue2DbUpdate():
    """
    This class handles the update of Bugzilla issue tracker data
    """

    NUM_PROCESSES = 3

    def __init__(self, db_name, project_name,
                 repo_name, issue_tracker_name, url, product, num_processes,
                 config, log_root_path):
        """
        :type db_name: str
        :param db_name: the name of an existing DB

        :type project_name: str
        :param project_name: the name of an existing project in the DB

        :type repo_name: str
        :param repo_name: the name of an existing repository in the DB

        :type issue_tracker_name: str
        :param issue_tracker_name: the name of the issue tracker to import

        :type url: str
        :param url: the URL of the issue tracker

        :type product: str
        :param product: the name of the product to import from the issue tracker

        :type num_processes: int
        :param num_processes: number of processes to import the data (default 3)

        :type config: dict
        :param config: the DB configuration file

        :type log_root_path: str
        :param log_root_path: the log path
        """
        self._log_path = log_root_path + "update-bugzilla-" + db_name + "-" + project_name + "-" + issue_tracker_name
        self._issue_tracker_name = issue_tracker_name
        self._url = url
        self._product = product
        self._project_name = project_name
        self._db_name = db_name
        self._repo_name = repo_name

        if num_processes:
            self._num_processes = num_processes
        else:
            self._num_processes = BugzillaIssue2DbUpdate.NUM_PROCESSES

        config.update({'database': db_name})
        self._config = config

        self._logging_util = LoggingUtil()

        self._logger = None
        self._fileHandler = None
        self._dao = None

    def _update_issue_content(self, repo_id, issue_tracker_id, intervals, url):
        # updates issues already stored in the DB
        queue_intervals = multiprocessing.JoinableQueue()
        results = multiprocessing.Queue()

        # Start consumers
        multiprocessing_util.start_consumers(self._num_processes, queue_intervals, results)

        for interval in intervals:
            issue_extractor = BugzillaIssue2Db(self._db_name, repo_id, issue_tracker_id, url, self._product, interval,
                                               self._config, self._log_path)
            queue_intervals.put(issue_extractor)

        # Add end-of-queue markers
        multiprocessing_util.add_poison_pills(self._num_processes, queue_intervals)

        # Wait for all of the tasks to finish
        queue_intervals.join()

    def _update_issue_dependency(self, repo_id, issue_tracker_id, intervals, url):
        # updates issue dependencies already stored in the DB
        queue_intervals = multiprocessing.JoinableQueue()
        results = multiprocessing.Queue()

        # Start consumers
        multiprocessing_util.start_consumers(self._num_processes, queue_intervals, results)

        for interval in intervals:
            issue_dependency_extractor = BugzillaIssueDependency2Db(self._db_name, repo_id, issue_tracker_id, url,
                                                                    self._product, interval,
                                                                    self._config, self._log_path)
            queue_intervals.put(issue_dependency_extractor)

        # Add end-of-queue markers
        multiprocessing_util.add_poison_pills(self._num_processes, queue_intervals)

        # Wait for all of the tasks to finish
        queue_intervals.join()

    def _update_issues(self):
        # updates issues
        project_id = self._dao.select_project_id(self._project_name)
        repo_id = self._dao.select_repo_id(project_id, self._repo_name)
        issue_tracker_id = self._dao.select_issue_tracker_id(repo_id, self._issue_tracker_name)
        issue_tracker_url = self._url

        if issue_tracker_id:
            cursor = self._dao.get_cursor()
            query = "SELECT i.own_id FROM issue i " \
                    "JOIN issue_tracker it ON i.issue_tracker_id = it.id " \
                    "WHERE issue_tracker_id = %s AND repo_id = %s " \
                    "ORDER BY i.own_id ASC;"
            arguments = [issue_tracker_id, repo_id]
            self._dao.execute(cursor, query, arguments)

            issues = []
            row = self._dao.fetchone(cursor)

            while row:
                issues.append(row[0])
                row = self._dao.fetchone(cursor)
            self._dao.close_cursor(cursor)

            if issues:
                intervals = [i for i in multiprocessing_util.get_tasks_intervals(issues, self._num_processes)
                             if len(i) > 0]

                self._update_issue_content(repo_id, issue_tracker_id, intervals, issue_tracker_url)
                self._update_issue_dependency(repo_id, issue_tracker_id, intervals, issue_tracker_url)

    def update(self):
        """
        updates the Bugzilla issue tracker data stored in the DB
        """
        try:
            self._logger = self._logging_util.get_logger(self._log_path)
            self._fileHandler = self._logging_util.get_file_handler(self._logger, self._log_path, "info")

            self._logger.info("BugzillaIssue2DbUpdate started")
            start_time = datetime.now()

            self._dao = BugzillaDao(self._config, self._logger)

            self._update_issues()

            end_time = datetime.now()
            minutes_and_seconds = self._logging_util.calculate_execution_time(end_time, start_time)
            self._logger.info("BugzillaIssue2DbUpdate finished after " + str(minutes_and_seconds[0]) +
                              " minutes and " + str(round(minutes_and_seconds[1], 1)) + " secs")
            self._logging_util.remove_file_handler_logger(self._logger, self._fileHandler)
        except:
            self._logger.error("BugzillaIssue2DbUpdate failed", exc_info=True)
        finally:
            if self._dao:
                self._dao.close_connection()
