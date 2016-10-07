#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'valerio cosentino'

import mysql.connector
from mysql.connector import errorcode
from datetime import datetime
import multiprocessing
import sys
sys.path.insert(0, "..//..//..")

from issue2db_extract_issue import Issue2Db
from issue2db_extract_issue_dependency import IssueDependency2Db
from querier_bugzilla import BugzillaQuerier
from extractor.util import multiprocessing_util
from extractor.util.db_util import DbUtil


class Issue2DbMain():

    NUM_PROCESSES = 10

    def __init__(self, db_name, project_name,
                 repo_name, type, url, product, before_date, recover_import, num_processes,
                 config, logger):
        self.logger = logger
        self.log_path = self.logger.name.rsplit('.', 1)[0] + "-" + project_name
        self.type = type
        self.url = url
        self.product = product
        self.project_name = project_name
        self.db_name = db_name
        self.repo_name = repo_name
        self.before_date = before_date
        self.recover_import = recover_import

        if num_processes:
            self.num_processes = num_processes
        else:
            self.num_processes = Issue2DbMain.NUM_PROCESSES

        self.db_util = DbUtil()

        config.update({'database': db_name})
        self.config = config

        try:
            self.querier = BugzillaQuerier(self.url, self.product, self.logger)
            self.cnx = mysql.connector.connect(**self.config)
        except:
            self.logger.error("Issue2Db extract failed", exc_info=True)

    def insert_issue_tracker(self, repo_id):
        cursor = self.cnx.cursor()
        query = "INSERT IGNORE INTO issue_tracker " \
                "VALUES (%s, %s, %s, %s)"
        arguments = [None, repo_id, self.url, self.type]
        cursor.execute(query, arguments)
        self.cnx.commit()

        query = "SELECT id " \
                "FROM issue_tracker " \
                "WHERE url = %s"
        arguments = [self.url]
        cursor.execute(query, arguments)

        row = cursor.fetchone()
        cursor.close()

        if row:
            found = row[0]
        else:
            self.logger("no issue tracker linked to " + str(self.url))

        return found

    def get_already_imported_issue_ids(self, issue_tracker_id, repo_id):
        issue_ids = []
        cursor = self.cnx.cursor()
        query = "SELECT i.id FROM issue i " \
                "JOIN issue_tracker it ON i.issue_tracker_id = it.id " \
                "WHERE issue_tracker_id = %s AND repo_id = %s " \
                "ORDER BY i.id ASC;"
        arguments = [issue_tracker_id, repo_id]
        cursor.execute(query, arguments)
        row = cursor.fetchone()

        while row:
            own_id = row[0]
            issue_ids.append(own_id)
            row = cursor.fetchone()

        cursor.close()

        return issue_ids

    def pass_list_as_argument(self, elements):
        return '-'.join([str(e) for e in elements])

    def insert_issue_data(self, repo_id, issue_tracker_id):
        if self.recover_import:
            imported = self.get_already_imported_issue_ids(issue_tracker_id, repo_id)
            issues = list(set(self.querier.get_issue_ids(None, None, self.before_date)) - set(imported))
            issues.sort()
        else:
            issues = self.querier.get_issue_ids(None, None, self.before_date)

        intervals = [i for i in multiprocessing_util.get_tasks_intervals(issues, self.num_processes) if len(i) > 0]

        queue_intervals = multiprocessing.JoinableQueue()
        results = multiprocessing.Queue()

        # Start consumers
        multiprocessing_util.start_consumers(self.num_processes, queue_intervals, results)

        for interval in intervals:
            issue_extractor = Issue2Db(self.db_name, repo_id, issue_tracker_id, self.url, self.product, interval,
                                       self.config, self.log_path)
            queue_intervals.put(issue_extractor)

        # Add end-of-queue markers
        multiprocessing_util.add_poison_pills(self.num_processes, queue_intervals)

        # Wait for all of the tasks to finish
        queue_intervals.join()

    def insert_issue_dependencies(self, repo_id, issue_tracker_id):
        issues = self.get_already_imported_issue_ids(issue_tracker_id, repo_id)
        intervals = [i for i in multiprocessing_util.get_tasks_intervals(issues, self.num_processes) if len(i) > 0]

        queue_intervals = multiprocessing.JoinableQueue()
        results = multiprocessing.Queue()

        # Start consumers
        multiprocessing_util.start_consumers(self.num_processes, queue_intervals, results)

        for interval in intervals:
            issue_dependency_extractor = IssueDependency2Db(self.db_name, repo_id, issue_tracker_id, self.url, self.product, interval,
                                                            self.config, self.log_path)
            queue_intervals.put(issue_dependency_extractor)

        # Add end-of-queue markers
        multiprocessing_util.add_poison_pills(self.num_processes, queue_intervals)

        # Wait for all of the tasks to finish
        queue_intervals.join()

    def split_issue_extraction(self):
        project_id = self.db_util.select_project_id(self.cnx, self.project_name, self.logger)
        repo_id = self.db_util.select_repo_id(self.cnx, project_id, self.repo_name, self.logger)
        issue_tracker_id = self.insert_issue_tracker(repo_id)
        self.insert_issue_data(repo_id, issue_tracker_id)

        #TO-CHECK if cnx is not reinitialized, the issues stored in the db are not retrieved
        self.cnx = mysql.connector.connect(**self.config)

        self.insert_issue_dependencies(repo_id, issue_tracker_id)

    def extract(self):
        try:
            start_time = datetime.now()
            self.split_issue_extraction()
            self.cnx.close()
            end_time = datetime.now()

            minutes_and_seconds = divmod((end_time-start_time).total_seconds(), 60)
            self.logger.info("Issue2Db extract finished after " + str(minutes_and_seconds[0])
                         + " minutes and " + str(round(minutes_and_seconds[1], 1)) + " secs")
        except:
            self.logger.error("Issue2Db extract failed", exc_info=True)