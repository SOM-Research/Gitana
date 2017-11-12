#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'valerio cosentino'

from datetime import datetime

from querier_bugzilla import BugzillaQuerier
from bugzilla_dao import BugzillaDao
from util.logging_util import LoggingUtil


class BugzillaIssueDependency2Db(object):
    """
    This class inserts the dependencies between Bugzilla issues
    """

    def __init__(self, db_name,
                 repo_id, issue_tracker_id, url, product, interval,
                 config, log_root_path):
        """
        :type db_name: str
        :param db_name: the name of an existing DB

        :type repo_id: int
        :param repo_id: the id of an existing repository in the DB

        :type issue_tracker_id: int
        :param issue_tracker_id: the id of an existing issue tracker in the DB

        :type url: str
        :param url: the URL of the bugzilla issue tracker

        :type product: str
        :param product: the name of the product in the bugzilla issue tracker

        :type interval: list int
        :param interval: a list of issue ids to import

        :type config: dict
        :param config: the DB configuration file

        :type log_root_path: str
        :param log_root_path: the log path
        """
        self._log_root_path = log_root_path
        self._url = url
        self._product = product
        self._db_name = db_name
        self._repo_id = repo_id
        self._issue_tracker_id = issue_tracker_id
        self._interval = interval
        self._logging_util = LoggingUtil()
        self._config = config
        self._filehandler = None
        self._logger = None
        self._querier = None
        self._dao = None

    def __call__(self):
        try:
            log_path = self._log_root_path + "-issue2db-dependency" + \
                       str(self._interval[0]) + "-" + str(self._interval[-1])
            self._logger = self._logging_util.get_logger(log_path)
            self._filehandler = self._logging_util.get_file_handler(self._logger, log_path, "info")

            self._querier = BugzillaQuerier(self._url, self._product, self._logger)
            self._dao = BugzillaDao(self._config, self._logger)
            self.extract()
        except Exception:
            self._logger.error("Issue2Db failed", exc_info=True)
        finally:
            if self._dao:
                self._dao.close_connection()

    def _extract_single_issue_dependency(self, issue_id, data, type):
        # inserts issue dependency
        extracted = None
        if isinstance(data, int):
            extracted = data
        else:
            if "show_bug" in data:
                extracted = data.split("?id=")[1]

        if extracted:
            dependent_issue = self._dao.select_issue_id(extracted, self._issue_tracker_id, self._repo_id)
            if dependent_issue:
                self._dao.insert_issue_dependency(issue_id, dependent_issue, type)

    def _extract_issue_dependency(self, issue_id, obj, type):
        # processes issue dependencies
        if isinstance(obj, list):
            for issue in obj:
                self._extract_single_issue_dependency(issue_id, issue, type)
        else:
            self._extract_single_issue_dependency(issue_id, obj, type)

    def _is_duplicated(self, issue):
        flag = True
        try:
            issue.dupe_of
        except:
            flag = False

        return flag

    def _set_dependencies(self):
        cursor = self._dao.get_cursor()
        query = "SELECT i.id FROM issue i " \
                "JOIN issue_tracker it ON i.issue_tracker_id = it.id " \
                "WHERE i.id >= %s AND i.id <= %s AND issue_tracker_id = %s AND repo_id = %s"
        arguments = [self._interval[0], self._interval[-1], self._issue_tracker_id, self._repo_id]
        self._dao.execute(cursor, query, arguments)

        row = self._dao.fetchone(cursor)

        while row:
            try:
                issue_id = row[0]
                issue_own_id = self._dao.select_issue_own_id(issue_id, self._issue_tracker_id, self._repo_id)
                issue = self._querier.get_issue(issue_own_id)

                if issue.blocks:
                    self._extract_issue_dependency(issue_id, self._querier.get_issue_blocks(issue),
                                                   self._dao.get_issue_dependency_type_id("block"))

                if issue.depends_on:
                    self._extract_issue_dependency(issue_id, self._querier.get_issue_depends_on(issue),
                                                   self._dao.get_issue_dependency_type_id("depends"))

                if issue.see_also:
                    self._extract_issue_dependency(issue_id, self._querier.get_issue_see_also(issue),
                                                   self._dao.get_issue_dependency_type_id("related"))

                if self._is_duplicated(issue):
                    if issue.dupe_of:
                        self._extract_issue_dependency(issue_id, self._querier.get_issue_dupe_of(issue),
                                                       self._dao.get_issue_dependency_type_id("duplicated"))

            except Exception:
                self._logger.error("something went wrong with the following issue id: " +
                                   str(issue_id) + " - tracker id " + str(self._issue_tracker_id),
                                   exc_info=True)

            row = self._dao.fetchone(cursor)

        self._dao.close_cursor(cursor)

    def extract(self):
        """
        extracts Bugzilla issue dependency data and stores it in the DB
        """
        try:
            self._logger.info("BugzillaIssueDependency2Db started")
            start_time = datetime.now()
            self._set_dependencies()

            end_time = datetime.now()
            minutes_and_seconds = self._logging_util.calculate_execution_time(end_time, start_time)
            self._logger.info("BugzillaIssueDependency2Db finished after " + str(minutes_and_seconds[0]) +
                              " minutes and " + str(round(minutes_and_seconds[1], 1)) + " secs")
            self._logging_util.remove_file_handler_logger(self._logger, self._filehandler)
        except Exception:
            self._logger.error("BugzillaIssueDependency2Db failed", exc_info=True)
