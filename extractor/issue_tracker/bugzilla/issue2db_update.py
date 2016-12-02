#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'valerio cosentino'


from datetime import datetime
import multiprocessing

from issue2db_extract_issue import BugzillaIssue2Db
from issue2db_extract_issue_dependency import BugzillaIssueDependency2Db
from util import multiprocessing_util
from bugzilla_dao import BugzillaDao


class BugzillaIssue2DbUpdate():

    NUM_PROCESSES = 5

    def __init__(self, db_name, project_name,
                 repo_name, issue_tracker_name, url, product, num_processes,
                 config, logger):

        self.logger = logger
        self.log_path = self.logger.name.rsplit('.', 1)[0] + "-" + project_name
        self.issue_tracker_name = issue_tracker_name
        self.url = url
        self.product = product
        self.project_name = project_name
        self.db_name = db_name
        self.repo_name = repo_name

        if num_processes:
            self.num_processes = num_processes
        else:
            self.num_processes = BugzillaIssue2DbUpdate.NUM_PROCESSES



        config.update({'database': db_name})
        self.config = config

        try:
            self.dao = BugzillaDao(self.config, self.logger)
        except:
            self.logger.error("Issue2Db update failed", exc_info=True)

    def update_issue_content(self, repo_id, issue_tracker_id, intervals, url):
        queue_intervals = multiprocessing.JoinableQueue()
        results = multiprocessing.Queue()

        # Start consumers
        multiprocessing_util.start_consumers(self.num_processes, queue_intervals, results)

        for interval in intervals:
            issue_extractor = BugzillaIssue2Db(self.db_name, repo_id, issue_tracker_id, url, self.product, interval,
                                       self.config, self.log_path)
            queue_intervals.put(issue_extractor)

        # Add end-of-queue markers
        multiprocessing_util.add_poison_pills(self.num_processes, queue_intervals)

        # Wait for all of the tasks to finish
        queue_intervals.join()

    def update_issue_dependency(self, repo_id, issue_tracker_id, intervals, url):
        queue_intervals = multiprocessing.JoinableQueue()
        results = multiprocessing.Queue()

        # Start consumers
        multiprocessing_util.start_consumers(self.num_processes, queue_intervals, results)

        for interval in intervals:
            issue_dependency_extractor = BugzillaIssueDependency2Db(self.db_name, repo_id, issue_tracker_id, url, self.product, interval,
                                                 self.config, self.log_path)
            queue_intervals.put(issue_dependency_extractor)

        # Add end-of-queue markers
        multiprocessing_util.add_poison_pills(self.num_processes, queue_intervals)

        # Wait for all of the tasks to finish
        queue_intervals.join()

    def update_issues(self):
        project_id = self.dao.select_project_id(self.project_name)
        repo_id = self.dao.select_repo_id(project_id, self.repo_name)
        issue_tracker_id = self.dao.select_issue_tracker_id(repo_id, self.issue_tracker_name)
        issue_tracker_url = self.url

        cursor = self.dao.get_cursor()
        query = "SELECT i.own_id FROM issue i " \
                "JOIN issue_tracker it ON i.issue_tracker_id = it.id " \
                "WHERE issue_tracker_id = %s AND repo_id = %s " \
                "ORDER BY i.own_id ASC;"
        arguments = [issue_tracker_id, repo_id]
        self.dao.execute(cursor, query, arguments)

        issues = []
        row = self.dao.fetchone(cursor)

        while row:
            issues.append(row[0])
            row = self.dao.fetchone(cursor)
        self.dao.close_cursor(cursor)

        if issues:
            intervals = [i for i in multiprocessing_util.get_tasks_intervals(issues, self.num_processes) if len(i) > 0]

            self.update_issue_content(repo_id, issue_tracker_id, intervals, issue_tracker_url)
            self.update_issue_dependency(repo_id, issue_tracker_id, intervals, issue_tracker_url)

    def update(self):
        try:
            start_time = datetime.now()
            self.update_issues()
            end_time = datetime.now()
            self.dao.close_connection()

            minutes_and_seconds = divmod((end_time-start_time).total_seconds(), 60)
            self.logger.info("BugzillaIssue2DbUpdate finished after " + str(minutes_and_seconds[0])
                         + " minutes and " + str(round(minutes_and_seconds[1], 1)) + " secs")
        except:
            self.logger.error("BugzillaIssue2DbUpdate failed", exc_info=True)