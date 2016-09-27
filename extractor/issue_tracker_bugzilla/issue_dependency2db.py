#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'valerio cosentino'

import sys
sys.path.insert(0, "..//..")

import mysql.connector
from mysql.connector import errorcode
from datetime import datetime
from querier_bugzilla import BugzillaQuerier
from extractor.init_db import config_db
import getopt
import os

import logging
import logging.handlers

LOG_FOLDER = "logs"


class IssueDependency2Db():

    def __init__(self, type, url, product, db_name, repo_id, issue_tracker_id, from_issue_id, to_issue_id):
        self.create_log_folder(LOG_FOLDER)
        LOG_FILENAME = LOG_FOLDER + "/issue_dependency2db"
        self.logger = logging.getLogger(LOG_FILENAME)
        fileHandler = logging.FileHandler(LOG_FILENAME + "-" + db_name + "-" + str(from_issue_id) + "-" + str(to_issue_id) + ".log", mode='w')
        formatter = logging.Formatter("%(asctime)s:%(levelname)s:%(message)s", "%Y-%m-%d %H:%M:%S")

        fileHandler.setFormatter(formatter)
        self.logger.setLevel(logging.INFO)
        self.logger.addHandler(fileHandler)
        self.type = type
        self.url = url
        self.product = product
        self.db_name = db_name
        self.repo_id = repo_id
        self.issue_tracker_id = issue_tracker_id
        self.from_issue_id = from_issue_id
        self.to_issue_id = to_issue_id

        self.querier = BugzillaQuerier(self.url, self.product, self.logger)

        self.cnx = mysql.connector.connect(**config_db.CONFIG)
        self.set_database()

    def create_log_folder(self, name):
        if not os.path.exists(name):
            os.makedirs(name)

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
        arguments = [self.from_issue_id, self.to_issue_id, self.issue_tracker_id, self.repo_id]
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

            except:
                self.logger.error("IssueDependency2Db: Something went wrong with the following issue id: " + str(issue_id) + " - tracker id " + str(self.issue_tracker_id))

            row = cursor.fetchone()

        cursor.close()

    def set_database(self):
        cursor = self.cnx.cursor()
        use_database = "USE " + self.db_name
        cursor.execute(use_database)
        cursor.close()

    def extract(self):
        start_time = datetime.now()
        self.set_dependencies()
        end_time = datetime.now()
        self.cnx.close()

        minutes_and_seconds = divmod((end_time-start_time).total_seconds(), 60)
        self.logger.info("IssueDependency2Db: process finished after " + str(minutes_and_seconds[0])
                       + " minutes and " + str(round(minutes_and_seconds[1], 1)) + " secs")
        return


def main(argv):
    opts, args = getopt.getopt(argv, "rr", ["rr="])

    type = str(args[0])
    url = str(args[1])
    product = str(args[2])
    db_name = str(args[3])
    repo_id = int(args[4])
    issue_tracker_id = int(args[5])
    from_issue_id = int(args[6])
    to_issue_id = int(args[7])

    extractor = IssueDependency2Db(type, url, product, db_name, repo_id, issue_tracker_id, from_issue_id, to_issue_id)
    extractor.extract()

if __name__ == "__main__":
    main(sys.argv[1:])