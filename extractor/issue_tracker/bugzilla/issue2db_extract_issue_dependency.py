#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'valerio cosentino'

import mysql.connector
from mysql.connector import errorcode
from datetime import datetime
import logging
import logging.handlers
import sys
sys.path.insert(0, "..//..//..")

from querier_bugzilla import BugzillaQuerier


class IssueDependency2Db(object):

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
        config.update({'database': db_name})
        self.config = config

    def __call__(self):
        LOG_FILENAME = self.log_path + "-issue2db-dependency"
        self.logger = logging.getLogger(LOG_FILENAME)
        fileHandler = logging.FileHandler(LOG_FILENAME + "-" + str(self.interval[0]) + "-" + str(self.interval[-1]) + ".log", mode='w')
        formatter = logging.Formatter("%(asctime)s:%(levelname)s:%(message)s", "%Y-%m-%d %H:%M:%S")

        fileHandler.setFormatter(formatter)
        self.logger.setLevel(logging.INFO)
        self.logger.addHandler(fileHandler)

        try:
            self.querier = BugzillaQuerier(self.url, self.product, self.logger)
            self.cnx = mysql.connector.connect(**self.config)
            self.extract()
        except Exception, e:
            self.logger.error("Issue2Db failed", exc_info=True)

    def insert_issue_dependency(self, issue_source_id, issue_target_id, type):
        cursor = self.cnx.cursor()
        query = "INSERT IGNORE INTO issue_dependency " \
                "VALUES (%s, %s, %s)"
        arguments = [issue_source_id, issue_target_id, type]
        cursor.execute(query, arguments)
        self.cnx.commit()
        cursor.close()

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
                self.insert_issue_dependency(issue_id, dependent_issue, type)

    def select_issue_own_id(self, issue_id):
        found = None
        cursor = self.cnx.cursor()
        query = "SELECT i.own_id " \
                "FROM issue i JOIN issue_tracker it ON i.issue_tracker_id = it.id " \
                "WHERE i.id = %s AND issue_tracker_id = %s AND repo_id = %s"
        arguments = [issue_id, self.issue_tracker_id, self.repo_id]
        cursor.execute(query, arguments)

        row = cursor.fetchone()
        cursor.close()

        if row:
            found = row[0]

        return found

    def select_issue_id(self, issue_own_id):
        found = None
        cursor = self.cnx.cursor()
        query = "SELECT id FROM issue WHERE own_id = %s AND issue_tracker_id = %s"
        arguments = [issue_own_id, self.issue_tracker_id]
        cursor.execute(query, arguments)

        row = cursor.fetchone()
        cursor.close()

        if row:
            found = row[0]

        return found

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
        cursor = self.cnx.cursor()
        query = "SELECT i.id FROM issue i " \
                "JOIN issue_tracker it ON i.issue_tracker_id = it.id " \
                "WHERE i.id >= %s AND i.id <= %s AND issue_tracker_id = %s AND repo_id = %s"
        arguments = [self.interval[0], self.interval[-1], self.issue_tracker_id, self.repo_id]
        cursor.execute(query, arguments)

        row = cursor.fetchone()

        while row:
            try:
                issue_id = row[0]
                issue_own_id = self.select_issue_own_id(issue_id)
                issue = self.querier.get_issue(issue_own_id)

                if issue.blocks:
                    self.extract_issue_dependency(issue_id, issue.blocks, "block")

                if issue.depends_on:
                    self.extract_issue_dependency(issue_id, issue.depends_on, "depends")

                if issue.see_also:
                    self.extract_issue_dependency(issue_id, issue.see_also, "related")

                if self.is_duplicated(issue):
                    if issue.dupe_of:
                        self.extract_issue_dependency(issue_id, issue.dupe_of, "duplicated")

            except Exception, e:
                self.logger.error("something went wrong with the following issue id: " + str(issue_id) + " - tracker id " + str(self.issue_tracker_id), exc_info=True)

            row = cursor.fetchone()

        cursor.close()

    def extract(self):
        try:
            start_time = datetime.now()
            self.set_dependencies()
            end_time = datetime.now()
            self.cnx.close()

            minutes_and_seconds = divmod((end_time-start_time).total_seconds(), 60)
            self.logger.info("process finished after " + str(minutes_and_seconds[0])
                           + " minutes and " + str(round(minutes_and_seconds[1], 1)) + " secs")
        except Exception, e:
            self.logger.error("Issue2Db failed", exc_info=True)