#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'valerio cosentino'

#deprecated. Please use issue2db_main
import mysql.connector
from mysql.connector import errorcode
from datetime import datetime
import multiprocessing
import sys
sys.path.insert(0, "..//..//..")

from issue2db_extract_issue import Issue2Db
from issue2db_extract_issue_dependency import IssueDependency2Db
from extractor.util import consumer


class Issue2DbUpdate():

    def __init__(self, db_name, project_name,
                 repo_name, url, product, num_processes,
                 config, logger):

        self.logger = logger
        self.log_path = self.logger.name.rsplit('.', 1)[0]
        self.url = url
        self.product = product
        self.project_name = project_name
        self.db_name = db_name
        self.repo_name = repo_name
        self.num_processes = num_processes

        config.update({'database': db_name})
        self.config = config

        try:
            self.cnx = mysql.connector.connect(**self.config)
        except:
            self.logger.error("Issue2Db update failed", exc_info=True)

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
        chunk_size = len(elements)/self.num_processes

        if chunk_size == 0:
            chunks = [elements]
        else:
            chunks = [elements[i:i + chunk_size] for i in range(0, len(elements), chunk_size)]

        intervals = []
        for chunk in chunks:
            intervals.append(chunk)

        return intervals

    def update_issue_content(self, repo_id, issue_tracker_id, intervals):
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

    def update_issue_dependency(self, repo_id, issue_tracker_id, intervals):
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

    def update_issues(self):
        repo_id = self.select_repo()
        issue_tracker_id = self.select_issue_tracker(repo_id, self.url)

        cursor = self.cnx.cursor()
        query = "SELECT i.own_id FROM issue i " \
                "JOIN issue_tracker it ON i.issue_tracker_id = it.id " \
                "WHERE issue_tracker_id = %s AND repo_id = %s " \
                "ORDER BY i.own_id ASC;"
        arguments = [issue_tracker_id, repo_id]
        cursor.execute(query, arguments)

        issues = []
        row = cursor.fetchone()

        while row:
            issues.append(row[0])
            row = cursor.fetchone()
        cursor.close()

        if issues:
            intervals = [i for i in self.get_intervals(issues) if len(i) > 0]

            self.update_issue_content(repo_id, issue_tracker_id, intervals)
            self.update_issue_dependency(repo_id, issue_tracker_id, intervals)

    def update(self):
        try:
            start_time = datetime.now()
            self.update_issues()
            end_time = datetime.now()
            self.cnx.close()

            minutes_and_seconds = divmod((end_time-start_time).total_seconds(), 60)
            self.logger.info("Issue2Db update finished after " + str(minutes_and_seconds[0])
                         + " minutes and " + str(round(minutes_and_seconds[1], 1)) + " secs")
        except:
            self.logger.error("Issue2Db update failed", exc_info=True)