#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'valerio cosentino'

#deprecated. Please use issue2db_main

import mysql.connector
from mysql.connector import errorcode
from datetime import datetime
from extractor.init_db import config_db
import logging
import logging.handlers
from subprocess import *
import glob
import os

import sys
sys.path.insert(0, "..//..")

TYPE = "bugzilla"
URL = "https://bugs.eclipse.org/bugs/xmlrpc.cgi"
PRODUCT = "papyrus"
BEFORE_DATE = None
LOG_FOLDER = "logs"

PROCESSES = 30

# DEPRECATED. This script updates only the issues already stored in the db.
# Please, use the issue2db_main script


def _instance_method_alias(obj, arg):
    obj.get_info_issue(arg)
    return


class IssueUpdate():

    def __init__(self, db_name, repo_name, type, url, product, before_date):
        self.create_log_folder(LOG_FOLDER)
        LOG_FILENAME = LOG_FOLDER + "/issueupdate"
        self.delete_previous_logs(LOG_FOLDER)
        self.logger = logging.getLogger(LOG_FILENAME)
        fileHandler = logging.FileHandler(LOG_FILENAME + "-" + db_name + ".log", mode='w')
        formatter = logging.Formatter("%(asctime)s:%(levelname)s:%(message)s", "%Y-%m-%d %H:%M:%S")

        fileHandler.setFormatter(formatter)
        self.logger.setLevel(logging.INFO)
        self.logger.addHandler(fileHandler)

        self.type = type
        self.url = url
        self.product = product
        self.db_name = db_name
        self.repo_name = repo_name
        self.before_date = before_date

        self.cnx = mysql.connector.connect(**config_db.CONFIG)
        self.set_database()
        self.set_settings()

    def create_log_folder(self, name):
        if not os.path.exists(name):
            os.makedirs(name)

    def delete_previous_logs(self, path):
        files = glob.glob(path + "/*")
        for f in files:
            try:
                os.remove(f)
            except:
                continue

    def select_repo(self):
        cursor = self.cnx.cursor()
        query = "SELECT id " \
                "FROM repository " \
                "WHERE name = %s"
        arguments = [self.repo_name]
        cursor.execute(query, arguments)
        id = cursor.fetchone()[0]
        cursor.close()
        return id

    def select_issue_tracker(self, repo_id, url):
        found = None
        cursor = self.cnx.cursor()
        query = "SELECT id " \
                "FROM issue_tracker " \
                "WHERE repo_id = %s AND url = %s"
        arguments = [repo_id, url]
        cursor.execute(query, arguments)
        row = cursor.fetchone()
        cursor.close()

        if row:
            found = row[0]

        return found

    def get_intervals(self, elements):
        chunk_size = len(elements)/PROCESSES

        if chunk_size == 0:
            chunks = [elements]
        else:
            chunks = [elements[i:i + chunk_size] for i in range(0, len(elements), chunk_size)]

        intervals = []
        for chunk in chunks:
            intervals.append((chunk[0], chunk[-1]))

        return intervals

    def update_issues(self):
        repo_id = self.select_repo()
        issue_tracker_id = self.select_issue_tracker(repo_id, self.url)

        cursor = self.cnx.cursor()
        query = "SELECT id " \
                "FROM issue " \
                "WHERE issue_tracker_id = %s"
        arguments = [issue_tracker_id]
        cursor.execute(query, arguments)

        issues = []
        row = cursor.fetchone()

        while row:
            issues.append(row[0])
            row = cursor.fetchone()
        cursor.close()

        if issues:
            intervals = self.get_intervals([id for id in issues])
            processes = []
            for interval in intervals:
                p = Popen(['python', 'issue2db.py', self.type, self.url, self.product, self.db_name, str(repo_id), str(issue_tracker_id), str(interval[0]), str(interval[1])])
                processes.append(p)

                while len(processes) == PROCESSES:
                    for p in processes:
                        p.poll()
                        if p.returncode is not None:
                            processes.remove(p)

        while processes:
            for p in processes:
                p.poll()
                if p.returncode is not None:
                    processes.remove(p)

        return

    def set_settings(self):
        cursor = self.cnx.cursor()
        cursor.execute("set global innodb_file_format = BARRACUDA")
        cursor.execute("set global innodb_file_format_max = BARRACUDA")
        cursor.execute("set global innodb_large_prefix = ON")
        cursor.execute("set global character_set_server = utf8")
        cursor.close()

    def set_database(self):
        cursor = self.cnx.cursor()
        use_database = "USE " + self.db_name
        cursor.execute(use_database)
        cursor.close()

    def update(self):
        start_time = datetime.now()
        self.update_issues()
        end_time = datetime.now()
        self.cnx.close()

        minutes_and_seconds = divmod((end_time-start_time).total_seconds(), 60)
        self.logger.info("Issue2Db: process finished after " + str(minutes_and_seconds[0])
                     + " minutes and " + str(round(minutes_and_seconds[1], 1)) + " secs")
        return


def main():
    a = IssueUpdate(config_db.DB_NAME, config_db.REPO_NAME, TYPE, URL, PRODUCT, BEFORE_DATE)
    a.update()

if __name__ == "__main__":
    main()