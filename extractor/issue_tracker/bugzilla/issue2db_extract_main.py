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
from extractor.util import consumer


class Issue2DbMain():

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
        self.num_processes = num_processes

        config.update({'database': db_name})
        self.config = config

        try:
            self.querier = BugzillaQuerier(self.url, self.product, self.logger)
            self.cnx = mysql.connector.connect(**self.config)
        except:
            self.logger.error("Issue2Db extract failed", exc_info=True)

    def select_repo(self):
        found = None
        cursor = self.cnx.cursor()
        query = "SELECT r.id " \
                "FROM repository r JOIN project p ON r.project_id = p.id " \
                "WHERE r.name = %s AND p.name = %s"
        arguments = [self.repo_name, self.project_name]
        cursor.execute(query, arguments)
        row = cursor.fetchone()
        cursor.close()

        if row:
            found = row[0]
        else:
            self.logger.error("the repository " + self.repo_name + " does not exist")

        return found

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

    def get_intervals(self, elements):
        elements.sort()
        chunk_size = len(elements)/self.num_processes

        if chunk_size == 0:
            chunks = [elements]
        else:
            chunks = [elements[i:i + chunk_size] for i in range(0, len(elements), chunk_size)]

        intervals = []
        for chunk in chunks:
            intervals.append(chunk)

        return intervals

    def insert_issue_data(self, repo_id, issue_tracker_id):
        if self.recover_import:
            imported = self.get_already_imported_issue_ids(issue_tracker_id, repo_id)
            issues = list(set(self.querier.get_issue_ids(None, None, self.before_date)) - set(imported))
            issues.sort()
        else:
            issues = self.querier.get_issue_ids(None, None, self.before_date)

        intervals = [i for i in self.get_intervals(issues) if len(i) > 0]

        queue_intervals = multiprocessing.JoinableQueue()
        results = multiprocessing.Queue()

        # Start consumers
        consumer.start_consumers(self.num_processes, queue_intervals, results)

        for interval in intervals:
            issue_extractor = Issue2Db(self.db_name, repo_id, issue_tracker_id, self.url, self.product, interval,
                                       self.config, self.log_path)
            queue_intervals.put(issue_extractor)

        # Add end-of-queue markers
        consumer.add_poison_pills(self.num_processes, queue_intervals)

        # Wait for all of the tasks to finish
        queue_intervals.join()

    def insert_issue_dependencies(self, repo_id, issue_tracker_id):
        issues = self.get_already_imported_issue_ids(issue_tracker_id, repo_id)
        intervals = [i for i in self.get_intervals(issues) if len(i) > 0]

        queue_intervals = multiprocessing.JoinableQueue()
        results = multiprocessing.Queue()

        # Start consumers
        consumer.start_consumers(self.num_processes, queue_intervals, results)

        for interval in intervals:
            issue_dependency_extractor = IssueDependency2Db(self.db_name, repo_id, issue_tracker_id, self.url, self.product, interval,
                                                            self.config, self.log_path)
            queue_intervals.put(issue_dependency_extractor)

        # Add end-of-queue markers
        consumer.add_poison_pills(self.num_processes, queue_intervals)

        # Wait for all of the tasks to finish
        queue_intervals.join()

    def split_issue_extraction(self):
        repo_id = self.select_repo()
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