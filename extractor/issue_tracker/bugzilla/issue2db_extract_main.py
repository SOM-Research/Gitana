#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'valerio cosentino'

from datetime import datetime
import multiprocessing
import sys
sys.path.insert(0, "..//..//..")

from issue2db_extract_issue import BugzillaIssue2Db
from issue2db_extract_issue_dependency import BugzillaIssueDependency2Db
from querier_bugzilla import BugzillaQuerier
from extractor.util import multiprocessing_util
from bugzilla_dao import BugzillaDao


class BugzillaIssue2DbMain():

    NUM_PROCESSES = 5

    def __init__(self, db_name, project_name,
                 repo_name, type, issue_tracker_name, url, product, before_date, num_processes,
                 config, logger):
        self.logger = logger
        self.log_path = self.logger.name.rsplit('.', 1)[0] + "-" + project_name
        self.type = type
        self.url = url
        self.product = product
        self.project_name = project_name
        self.db_name = db_name
        self.issue_tracker_name = issue_tracker_name
        self.repo_name = repo_name
        self.before_date = before_date

        if num_processes:
            self.num_processes = num_processes
        else:
            self.num_processes = BugzillaIssue2DbMain.NUM_PROCESSES

        config.update({'database': db_name})
        self.config = config

        try:
            self.querier = BugzillaQuerier(self.url, self.product, self.logger)
            self.dao = BugzillaDao(self.config, self.logger)
        except:
            self.logger.error("Issue2Db extract failed", exc_info=True)

    def pass_list_as_argument(self, elements):
        return '-'.join([str(e) for e in elements])

    def insert_issue_data(self, repo_id, issue_tracker_id):
        imported = self.dao.get_already_imported_issue_ids(issue_tracker_id, repo_id)
        issues = list(set(self.querier.get_issue_ids(None, None, self.before_date)) - set(imported))
        issues.sort()

        intervals = [i for i in multiprocessing_util.get_tasks_intervals(issues, self.num_processes) if len(i) > 0]

        queue_intervals = multiprocessing.JoinableQueue()
        results = multiprocessing.Queue()

        # Start consumers
        multiprocessing_util.start_consumers(self.num_processes, queue_intervals, results)

        for interval in intervals:
            issue_extractor = BugzillaIssue2Db(self.db_name, repo_id, issue_tracker_id, self.url, self.product, interval,
                                       self.config, self.log_path)
            queue_intervals.put(issue_extractor)

        # Add end-of-queue markers
        multiprocessing_util.add_poison_pills(self.num_processes, queue_intervals)

        # Wait for all of the tasks to finish
        queue_intervals.join()

    def insert_issue_dependencies(self, repo_id, issue_tracker_id):
        issues = self.dao.get_already_imported_issue_ids(issue_tracker_id, repo_id)
        intervals = [i for i in multiprocessing_util.get_tasks_intervals(issues, self.num_processes) if len(i) > 0]

        queue_intervals = multiprocessing.JoinableQueue()
        results = multiprocessing.Queue()

        # Start consumers
        multiprocessing_util.start_consumers(self.num_processes, queue_intervals, results)

        for interval in intervals:
            issue_dependency_extractor = BugzillaIssueDependency2Db(self.db_name, repo_id, issue_tracker_id, self.url, self.product, interval,
                                                            self.config, self.log_path)
            queue_intervals.put(issue_dependency_extractor)

        # Add end-of-queue markers
        multiprocessing_util.add_poison_pills(self.num_processes, queue_intervals)

        # Wait for all of the tasks to finish
        queue_intervals.join()

    def split_issue_extraction(self):
        project_id = self.dao.select_project_id(self.project_name)
        repo_id = self.dao.select_repo_id(project_id, self.repo_name)
        issue_tracker_id = self.dao.insert_issue_tracker(repo_id, self.issue_tracker_name, self.url, self.type)
        self.insert_issue_data(repo_id, issue_tracker_id)

        self.dao.restart_connection()
        self.insert_issue_dependencies(repo_id, issue_tracker_id)

    def extract(self):
        try:
            start_time = datetime.now()
            self.split_issue_extraction()
            self.dao.close_connection()
            end_time = datetime.now()

            minutes_and_seconds = divmod((end_time-start_time).total_seconds(), 60)
            self.logger.info("BugzillaIssue2DbMain finished after " + str(minutes_and_seconds[0])
                         + " minutes and " + str(round(minutes_and_seconds[1], 1)) + " secs")
        except:
            self.logger.error("BugzillaIssue2DbMain failed", exc_info=True)