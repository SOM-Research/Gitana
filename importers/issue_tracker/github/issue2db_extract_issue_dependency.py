#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'valerio cosentino'

from datetime import datetime

from querier_github import GitHubQuerier
from github_dao import GitHubDao
from util.logging_util import LoggingUtil


class GitHubIssueDependency2Db(object):
    """
    This class inserts the dependencies between GitHub issues
    """

    def __init__(self, db_name,
                 repo_id, issue_tracker_id, url, interval, token,
                 config, log_root_path):
        """
        :type db_name: str
        :param db_name: the name of an existing DB

        :type repo_id: int
        :param repo_id: the id of an existing repository in the DB

        :type issue_tracker_id: int
        :param issue_tracker_id: the id of an existing issue tracker in the DB

        :type url: str
        :param url: full name of the GitHub repository

        :type interval: list int
        :param interval: a list of issue ids to import

        :type token: str
        :param token: a GitHub token

        :type config: dict
        :param config: the DB configuration file

        :type log_root_path: str
        :param log_root_path: the log path
        """
        self._log_root_path = log_root_path
        self._url = url
        self._db_name = db_name
        self._repo_id = repo_id
        self._issue_tracker_id = issue_tracker_id
        self._interval = interval
        self._token = token
        self._config = config

        self._logging_util = LoggingUtil()
        self._fileHandler = None
        self._logger = None
        self._querier = None
        self._dao = None

    def __call__(self):
        try:
            log_path = self._log_root_path + "-issue2db-dependency" + str(self._interval[0]) + \
                       "-" + str(self._interval[-1])
            self._logger = self._logging_util.get_logger(log_path)
            self._fileHandler = self._logging_util.get_file_handler(self._logger, log_path, "info")

            self._querier = GitHubQuerier(self._url, self._token, self._logger)
            self._dao = GitHubDao(self._config, self._logger)
            self.extract()
        except Exception:
            self._logger.error("GitHubIssueDependency2Db failed", exc_info=True)

    def _extract_issue_dependencies(self):
        # inserts issue dependency
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

                comments = [self._querier.get_issue_body(issue)] + [self._querier.get_issue_comment_body(comment)
                                                                    for comment in
                                                                    self._querier.get_issue_comments(issue)]

                for c in comments:
                    if c:
                        referenced_issues = self._querier.get_referenced_issues(c)
                        for ri in referenced_issues:
                            referenced_issue_id = self._dao.select_issue_id(ri, self._issue_tracker_id, self._repo_id)
                            self._dao.insert_issue_dependency(referenced_issue_id, issue_own_id,
                                                              self._dao.get_issue_dependency_type_id("related"))

            except Exception:
                self._logger.error("something went wrong with the following issue id: " + str(issue_id) +
                                   " - tracker id " + str(self._issue_tracker_id), exc_info=True)

            row = self._dao.fetchone(cursor)

        self._dao.close_cursor(cursor)

    def extract(self):
        """
        extracts GitHub issue dependency data and stores it in the DB
        """
        try:
            self._logger.info("GitHubIssueDependency2Db started")
            start_time = datetime.now()

            self._extract_issue_dependencies()

            end_time = datetime.now()
            minutes_and_seconds = self._logging_util.calculate_execution_time(end_time, start_time)
            self._logger.info("GitHubIssueDependency2Db finished after " + str(minutes_and_seconds[0]) +
                              " minutes and " + str(round(minutes_and_seconds[1], 1)) + " secs")
            self._logging_util.remove_file_handler_logger(self._logger, self._fileHandler)
        except Exception:
            self._logger.error("GitHubIssueDependency2Db failed", exc_info=True)
        finally:
            if self._dao:
                self._dao.close_connection()
