#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'valerio cosentino'

from datetime import datetime
import multiprocessing

from querier_git import GitQuerier
from git2db_extract_reference import Git2DbReference
from util import multiprocessing_util
from git_dao import GitDao

#do not import patches
LIGHT_IMPORT_TYPE = 1
#import patches but not at line level
MEDIUM_IMPORT_TYPE = 2
#import patches also at line level
FULL_IMPORT_TYPE = 3


class Git2DbMain():

    NUM_PROCESSES = 10

    def __init__(self, db_name, project_name,
                 repo_name, git_repo_path, before_date, import_type, references, num_processes,
                 config, logger):
        self.logger = logger
        self.log_path = self.logger.name.rsplit('.', 1)[0] + "-" + project_name
        self.git_repo_path = git_repo_path
        self.project_name = project_name
        self.db_name = db_name
        self.repo_name = repo_name
        self.before_date = before_date
        self.import_type = import_type

        self.references = references

        if num_processes:
            self.num_processes = num_processes
        else:
            self.num_processes = Git2DbMain.NUM_PROCESSES

        config.update({'database': db_name})
        self.config = config

        try:
            self.querier = GitQuerier(git_repo_path, self.logger)
            self.dao = GitDao(self.config, self.logger)
        except Exception, e:
            self.logger.error("Git2Db extract failed", exc_info=True)

    def get_info_contribution(self, repo_id):

        queue_references = multiprocessing.JoinableQueue()
        results = multiprocessing.Queue()

        # Start consumers
        multiprocessing_util.start_consumers(self.num_processes, queue_references, results)

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
        multiprocessing_util.add_poison_pills(self.num_processes, queue_references)

        # Wait for all of the tasks to finish
        queue_references.join()

    def extract(self):
        try:
            start_time = datetime.now()
            project_id = self.dao.select_project_id(self.project_name)
            self.dao.insert_repo(project_id, self.repo_name)
            repo_id = self.dao.select_repo_id(self.repo_name)
            self.dao.close_connection()

            #info contribution does not need a connection to the db
            self.get_info_contribution(repo_id)

            self.dao.restart_connection()
            self.dao.fix_commit_parent_table(repo_id)
            self.dao.close_connection()
            end_time = datetime.now()
            minutes_and_seconds = divmod((end_time-start_time).total_seconds(), 60)
            self.logger.info("Git2DbMain finished after " + str(minutes_and_seconds[0])
                         + " minutes and " + str(round(minutes_and_seconds[1], 1)) + " secs")
        except Exception, e:
            self.logger.error("Git2DbMain failed", exc_info=True)