#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'valerio cosentino'

from datetime import datetime
import multiprocessing

from querier_git import GitQuerier
from extractor.cvs.git.git2db_extract_reference import Git2DbReference
from util import multiprocessing_util
from git_dao import GitDao


class Git2DbUpdate():

    NUM_PROCESSES = 10

    def __init__(self, db_name, project_name,
                 repo_name, issue_tracker_name, git_repo_path, before_date,
                 num_processes, config, logger):
        self.logger = logger
        self.log_path = self.logger.name.rsplit('.', 1)[0] + "-" + project_name
        self.git_repo_path = git_repo_path
        self.issue_tracker_name = issue_tracker_name
        self.project_name = project_name
        self.db_name = db_name
        self.repo_name = repo_name
        self.before_date = before_date
        self.existing_refs = []

        if num_processes:
            self.num_processes = num_processes
        else:
            self.num_processes = Git2DbUpdate.NUM_PROCESSES

        config.update({'database': db_name})
        self.config = config

        try:
            self.querier = GitQuerier(git_repo_path, self.logger)
            self.dao = GitDao(self.config, self.logger)
        except:
            self.logger.error("Git2Db update failed", exc_info=True)

    def update_existing_references(self, repo_id, import_type):
        cursor = self.dao.get_cursor()
        query = "SELECT c.sha, lc.ref_id " \
                "FROM commit c " \
                "JOIN (SELECT ref_id, max(commit_id) as last_commit_id_in_ref FROM commit_in_reference WHERE repo_id = %s GROUP BY ref_id) as lc " \
                "ON c.id = lc.last_commit_id_in_ref"
        arguments = [repo_id]
        self.dao.execute(cursor, query, arguments)

        queue_references = multiprocessing.JoinableQueue()
        results = multiprocessing.Queue()

        # Start consumers
        multiprocessing_util.start_consumers(self.num_processes, queue_references, results)

        row = self.dao.fetchone(cursor)
        while row:
            sha = row[0]
            ref_id = row[1]
            row = self.dao.fetchone(cursor)

            ref_name = self.dao.select_reference_name(repo_id, ref_id)

            for reference in self.querier.get_references():
                reference_name = reference[0]
                if reference_name == ref_name:
                    self.existing_refs.append(ref_name)

                    git_ref_extractor = Git2DbReference(self.db_name, repo_id, self.git_repo_path,
                                                        self.before_date, import_type, reference[0], sha,
                                                        self.config, self.log_path)

                    queue_references.put(git_ref_extractor)
                    break

        self.dao.close_cursor(cursor)

        # Add end-of-queue markers
        multiprocessing_util.add_poison_pills(self.num_processes, queue_references)

        # Wait for all of the tasks to finish
        queue_references.join()

    def update_repo(self, repo_id, import_type):
        self.update_existing_references(repo_id, import_type)
        self.dao.close_connection()

    def get_import_type(self, repo_id):
        import_type = 1
        import_type += self.dao.line_detail_table_is_empty(repo_id) + self.dao.file_modification_patch_is_empty(repo_id)
        return import_type

    def update(self):
        try:
            start_time = datetime.now()
            project_id = self.dao.select_project_id(self.project_name)
            repo_id = self.dao.select_repo_id(self.repo_name)
            self.update_repo(repo_id, self.get_import_type(repo_id))
            self.dao.restart_connection()
            self.dao.fix_commit_parent_table(repo_id)
            end_time = datetime.now()
            minutes_and_seconds = divmod((end_time-start_time).total_seconds(), 60)
            self.logger.info("Git2DbUpdate finished after " + str(minutes_and_seconds[0])
                         + " minutes and " + str(round(minutes_and_seconds[1], 1)) + " secs")
        except:
            self.logger.error("Git2DbUpdate failed", exc_info=True)