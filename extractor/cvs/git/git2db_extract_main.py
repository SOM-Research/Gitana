#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'valerio cosentino'

import mysql.connector
from mysql.connector import errorcode
from datetime import datetime
import multiprocessing
import sys
import time
sys.path.insert(0, "..//..//..")

from querier_git import GitQuerier
from git2db_extract_reference import Git2DbReference
from extractor.util import consumer

#do not import patches
LIGHT_IMPORT_TYPE = 1
#import patches but not at line level
MEDIUM_IMPORT_TYPE = 2
#import patches also at line level
FULL_IMPORT_TYPE = 3


class Git2DbMain():

    def __init__(self, db_name, project_name,
                 repo_name, git_repo_path, before_date, import_type, references, num_processes,
                 config, logger):
        self.logger = logger
        self.log_path = self.logger.name.rsplit('.', 1)[0]
        self.git_repo_path = git_repo_path
        self.project_name = project_name
        self.db_name = db_name
        self.repo_name = repo_name
        self.before_date = before_date
        self.import_type = import_type

        self.references = references
        self.num_processes = num_processes

        config.update({'database': db_name})
        self.config = config

        try:
            self.querier = GitQuerier(git_repo_path, self.logger)
            self.cnx = mysql.connector.connect(**self.config)
        except Exception, e:
            self.logger.error("Git2Db extract failed", exc_info=True)

    def select_project(self):
        cursor = self.cnx.cursor()
        query = "SELECT id " \
                "FROM project " \
                "WHERE name = %s"
        arguments = [self.project_name]
        cursor.execute(query, arguments)
        id = cursor.fetchone()[0]
        cursor.close()
        return id

    def insert_repo(self, project_id):
        cursor = self.cnx.cursor()
        query = "INSERT IGNORE INTO repository " \
                "VALUES (%s, %s, %s)"
        arguments = [None, project_id, self.repo_name]
        cursor.execute(query, arguments)
        self.cnx.commit()

        query = "SELECT id " \
                "FROM repository " \
                "WHERE name = %s AND project_id = %s"
        arguments = [self.repo_name, project_id]
        cursor.execute(query, arguments)
        id = cursor.fetchone()[0]
        cursor.close()
        return id

    def get_info_contribution(self):
        project_id = self.select_project()
        repo_id = self.insert_repo(project_id)
        self.cnx.close()

        queue_references = multiprocessing.JoinableQueue()
        results = multiprocessing.Queue()

        # Start consumers
        consumer.start_consumers(self.num_processes, queue_references, results)

        for reference in self.querier.get_references():
            if self.references:
                if reference[0] in self.references:
                    git_ref_extractor = Git2DbReference(self.db_name, repo_id, self.git_repo_path,
                                                        self.before_date, self.import_type, reference[0], "",
                                                        self.config, self.log_path)

                    queue_references.put(git_ref_extractor)
            else:
                git_ref_extractor = Git2DbReference(self.db_name, repo_id, self.git_repo_path,
                                                    self.before_date, self.import_type, reference[0], "",
                                                    self.config, self.log_path)

                queue_references.put(git_ref_extractor)

        # Add end-of-queue markers
        consumer.add_poison_pills(self.num_processes, queue_references)

        # Wait for all of the tasks to finish
        queue_references.join()

    def extract(self):
        try:
            start_time = datetime.now()
            self.get_info_contribution()
            end_time = datetime.now()
            minutes_and_seconds = divmod((end_time-start_time).total_seconds(), 60)
            self.logger.info("Git2Db extract finished after " + str(minutes_and_seconds[0])
                         + " minutes and " + str(round(minutes_and_seconds[1], 1)) + " secs")
        except Exception, e:
            self.logger.error("Git2Db extract failed", exc_info=True)