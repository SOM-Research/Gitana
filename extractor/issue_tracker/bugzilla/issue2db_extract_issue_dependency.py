#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'valerio cosentino'

from datetime import datetime

from querier_bugzilla import BugzillaQuerier
from bugzilla_dao import BugzillaDao
from util.logging_util import LoggingUtil


class BugzillaIssueDependency2Db(object):

    def __init__(self, db_name,
                 repo_id, issue_tracker_id, url, product, interval,
                 config, log_path):
        self.log_path = log_path
        self.url = url
        self.product = product
        self.db_name = db_name
        self.repo_id = repo_id
        self.issue_tracker_id = issue_tracker_id
        self.interval = interval
        self.fileHandler = None
        config.update({'database': db_name})
        self.logging_util = LoggingUtil()
        self.config = config

    def __call__(self):
        log_filename = self.log_path + "-issue2db-dependency" + str(self.interval[0]) + "-" + str(self.interval[-1])
        self.logger = self.logging_util.get_logger(log_filename)
        self.fileHandler = self.logging_util.get_file_handler(self.logger, log_filename, "info")

        try:
            self.querier = BugzillaQuerier(self.url, self.product, self.logger)
            self.dao = BugzillaDao(self.config, self.logger)
            self.extract()
        except Exception, e:
            self.logger.error("Issue2Db failed", exc_info=True)

    def extract_single_issue_dependency(self, issue_id, data, type):
        extracted = None
        if isinstance(data, int):
            extracted = data
        else:
            if "show_bug" in data:
                extracted = data.split("?id=")[1]

        if extracted:
            dependent_issue = self.select_issue_id(extracted)
            if dependent_issue:
                self.dao.insert_issue_dependency(issue_id, dependent_issue, type)

    def extract_issue_dependency(self, issue_id, obj, type):
        if isinstance(obj, list):
            for issue in obj:
                self.extract_single_issue_dependency(issue_id, issue, type)
        else:
            self.extract_single_issue_dependency(issue_id, obj, type)

    def is_duplicated(self, issue):
        flag = True
        try:
            issue.dupe_of
        except:
            flag = False

        return flag

    def set_dependencies(self):
        cursor = self.dao.get_cursor()
        query = "SELECT i.id FROM issue i " \
                "JOIN issue_tracker it ON i.issue_tracker_id = it.id " \
                "WHERE i.id >= %s AND i.id <= %s AND issue_tracker_id = %s AND repo_id = %s"
        arguments = [self.interval[0], self.interval[-1], self.issue_tracker_id, self.repo_id]
        self.dao.execute(cursor, query, arguments)

        row = self.dao.fetchone(cursor)

        while row:
            try:
                issue_id = row[0]
                issue_own_id = self.select_issue_own_id(issue_id)
                issue = self.querier.get_issue(issue_own_id)

                if issue.blocks:
                    self.extract_issue_dependency(issue_id, self.querier.get_issue_blocks(issue), self.dao.get_issue_dependency_type_id("block"))

                if issue.depends_on:
                    self.extract_issue_dependency(issue_id, self.querier.get_issue_depends_on(issue), self.dao.get_issue_dependency_type_id("depends"))

                if issue.see_also:
                    self.extract_issue_dependency(issue_id, self.querier.get_issue_see_also(issue), self.dao.get_issue_dependency_type_id("related"))

                if self.is_duplicated(issue):
                    if issue.dupe_of:
                        self.extract_issue_dependency(issue_id, self.querier.get_issue_dupe_of(issue), self.dao.get_issue_dependency_type_id("duplicated"))

            except Exception, e:
                self.logger.error("something went wrong with the following issue id: " + str(issue_id) + " - tracker id " + str(self.issue_tracker_id), exc_info=True)

            row = self.dao.fetchone(cursor)

        self.dao.close_cursor(cursor)

    def extract(self):
        try:
            start_time = datetime.now()
            self.set_dependencies()
            end_time = datetime.now()
            self.dao.close_connection()

            minutes_and_seconds = divmod((end_time-start_time).total_seconds(), 60)
            self.logger.info("BugzillaIssueDependency2Db finished after " + str(minutes_and_seconds[0])
                           + " minutes and " + str(round(minutes_and_seconds[1], 1)) + " secs")
            self.logging_util.remove_file_handler_logger(self.logger, self.fileHandler)
        except Exception, e:
            self.logger.error("BugzillaIssueDependency2Db failed", exc_info=True)