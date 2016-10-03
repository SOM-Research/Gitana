#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'valerio cosentino'

from datetime import datetime
import multiprocessing
import mysql.connector
from mysql.connector import errorcode
import sys
sys.path.insert(0, "..//..//..")

from querier_git import GitQuerier
from extractor.cvs.git.git2db_extract_reference import Git2DbReference
from extractor.util import consumer

BEFORE_DATE = ""
IMPORT_LAST_COMMIT = False
IMPORT_NEW_REFERENCES = True


class Git2DbUpdate():

    def __init__(self, db_name, project_name,
                 repo_name, git_repo_path, before_date, import_last_commit, import_new_references,
                 num_processes, config, logger):
        self.logger = logger
        self.log_path = self.logger.name.rsplit('.', 1)[0] + "-" + project_name
        self.git_repo_path = git_repo_path
        self.project_name = project_name
        self.db_name = db_name
        self.repo_name = repo_name
        self.before_date = before_date
        self.import_last_commit = import_last_commit
        self.import_new_references = import_new_references
        self.existing_refs = []

        self.num_processes = num_processes

        config.update({'database': db_name})
        self.config = config

        try:
            self.querier = GitQuerier(git_repo_path, self.logger)
            self.cnx = mysql.connector.connect(**self.config)
        except:
            self.logger.error("Git2Db update failed", exc_info=True)

    def array2string(self, array):
        return ','.join(str(x) for x in array)

    def select_repo_id(self, repo_name):
        cursor = self.cnx.cursor()
        query = "SELECT id FROM repository WHERE name = %s"
        arguments = [repo_name]
        cursor.execute(query, arguments)

        row = cursor.fetchone()
        cursor.close()
        repo_id = 0
        if row:
            repo_id = row[0]

        return repo_id

    def select_reference_name(self, repo_id, ref_id):
        cursor = self.cnx.cursor()
        query = "SELECT name " \
                "FROM reference " \
                "WHERE id = %s and repo_id = %s"
        arguments = [ref_id, repo_id]
        cursor.execute(query, arguments)
        name = cursor.fetchone()[0]
        cursor.close()
        return name

    def update_existing_references(self, repo_id, import_type):
        cursor = self.cnx.cursor()
        query = "SELECT c.sha, lc.ref_id " \
                "FROM commit c " \
                "JOIN (SELECT ref_id, max(commit_id) as last_commit_id_in_ref FROM commit_in_reference WHERE repo_id = %s GROUP BY ref_id) as lc " \
                "ON c.id = lc.last_commit_id_in_ref"
        arguments = [repo_id]
        cursor.execute(query, arguments)

        queue_references = multiprocessing.JoinableQueue()
        results = multiprocessing.Queue()

        # Start consumers
        consumer.start_consumers(self.num_processes, queue_references, results)

        row = cursor.fetchone()
        while row:
            sha = row[0]
            ref_id = row[1]
            row = cursor.fetchone()

            ref_name = self.select_reference_name(repo_id, ref_id)

            for reference in self.querier.get_references():
                reference_name = reference[0]
                if reference_name == ref_name:
                    self.existing_refs.append(ref_name)

                    git_ref_extractor = Git2DbReference(self.db_name, repo_id, self.git_repo_path,
                                                        self.before_date, import_type, reference[0], sha,
                                                        self.config, self.log_path)

                    queue_references.put(git_ref_extractor)
                    break

        cursor.close()

        # Add end-of-queue markers
        consumer.add_poison_pills(self.num_processes, queue_references)

        # Wait for all of the tasks to finish
        queue_references.join()

    def add_new_references(self, repo_id, import_type):
        queue_references = multiprocessing.JoinableQueue()
        results = multiprocessing.Queue()

        # Start consumers
        consumer.start_consumers(self.num_processes, queue_references, results)

        for reference in self.querier.get_references():
            reference_name = reference[0]
            if reference_name not in self.existing_refs and reference_name != "origin/HEAD":
                git_ref_extractor = Git2DbReference(self.db_name, repo_id, self.git_repo_path,
                                                    self.before_date, import_type, reference[0], "",
                                                    self.config, self.log_path)

                queue_references.put(git_ref_extractor)

        # Add end-of-queue markers
        consumer.add_poison_pills(self.num_processes, queue_references)

        # Wait for all of the tasks to finish
        queue_references.join()

    def delete_commit(self, commit_id, repo_id):
        cursor = self.cnx.cursor()
        query = "DELETE FROM commit WHERE id = %s AND repo_id = %s"
        arguments = [commit_id, repo_id]
        cursor.execute(query, arguments)
        self.cnx.commit()
        cursor.close()

    def delete_commit_parent(self, commit_id, repo_id):
        cursor = self.cnx.cursor()
        query = "DELETE FROM commit_parent WHERE commit_id = %s AND repo_id = %s"
        arguments = [commit_id, repo_id]
        cursor.execute(query, arguments)
        self.cnx.commit()
        cursor.close()

    def delete_commit_in_reference(self, commit_id, repo_id):
        cursor = self.cnx.cursor()
        query = "DELETE FROM commit_in_reference WHERE commit_id = %s AND repo_id = %s"
        arguments = [commit_id, repo_id]
        cursor.execute(query, arguments)
        self.cnx.commit()
        cursor.close()

    def delete_file_modification(self, commit_id):
        cursor = self.cnx.cursor()
        query = "DELETE FROM file_modification WHERE commit_id = %s"
        arguments = [commit_id]
        cursor.execute(query, arguments)
        self.cnx.commit()
        cursor.close()

    def delete_line_details(self, file_modification_ids):
        cursor = self.cnx.cursor()
        query = "DELETE FROM line_detail WHERE file_modification_id IN (" + self.array2string(file_modification_ids) + ")"
        cursor.execute(query)
        self.cnx.commit()
        cursor.close()

    def delete_file_related_info(self, commit_id):
        cursor = self.cnx.cursor()
        query = "SELECT id, file_id " \
                "FROM file_modification f " \
                "WHERE commit_id = %s"
        arguments = [commit_id]
        cursor.execute(query, arguments)

        row = cursor.fetchone()

        file_modification_ids = []
        while row:
            file_modification_ids.append(row[0])
            row = cursor.fetchone()
        cursor.close()

        if file_modification_ids:
            self.delete_line_details(file_modification_ids)
        self.delete_file_modification(commit_id)

    def delete_last_commit_info(self, repo_id):
        cursor = self.cnx.cursor()
        query = "SELECT MAX(id) as last_commit_id " \
                "FROM commit c " \
                "WHERE repo_id = %s"
        arguments = [repo_id]
        cursor.execute(query, arguments)

        row = cursor.fetchone()
        cursor.close()
        if row:
            last_commit_id = row[0]
            self.delete_commit(last_commit_id, repo_id)
            self.delete_commit_in_reference(last_commit_id, repo_id)
            self.delete_commit_parent(last_commit_id, repo_id)
            self.delete_file_related_info(last_commit_id)

    def update_repo(self, repo_id, import_type):
        if self.import_last_commit:
            self.delete_last_commit_info(repo_id)

        self.update_existing_references(repo_id, import_type)
        self.cnx.close()
        if self.import_new_references:
            self.add_new_references(repo_id, import_type)

    def line_detail_table_is_empty(self, repo_id):
        cursor = self.cnx.cursor()
        query = "SELECT COUNT(*) " \
                "FROM commit c " \
                "JOIN file_modification fm ON c.id = fm.commit_id " \
                "JOIN line_detail l ON fm.id = l.file_modification_id " \
                "WHERE l.content IS NOT NULL AND repo_id = %s"
        arguments = [repo_id]
        cursor.execute(query, arguments)

        row = cursor.fetchone()
        count = 0
        if row:
            count = int(row[0])

        cursor.close()

        return int(count > 0)

    def file_modification_patch_is_empty(self, repo_id):
        cursor = self.cnx.cursor()
        query = "SELECT COUNT(*) " \
                "FROM commit c " \
                "JOIN file_modification fm ON c.id = fm.commit_id " \
                "WHERE patch IS NOT NULL and repo_id = %s"
        arguments = [repo_id]
        cursor.execute(query, arguments)

        row = cursor.fetchone()
        count = 0
        if row:
            count = int(row[0])

        cursor.close()

        return int(count > 0)

    def get_import_type(self, repo_id):
        import_type = 1
        import_type += self.line_detail_table_is_empty(repo_id) + self.file_modification_patch_is_empty(repo_id)
        return import_type

    def update(self):
        try:
            start_time = datetime.now()
            repo_id = self.select_repo_id(self.repo_name)

            self.update_repo(repo_id, self.get_import_type(repo_id))
            end_time = datetime.now()
            minutes_and_seconds = divmod((end_time-start_time).total_seconds(), 60)
            self.logger.info("Git2Db update finished after " + str(minutes_and_seconds[0])
                         + " minutes and " + str(round(minutes_and_seconds[1], 1)) + " secs")
        except:
            self.logger.error("Git2Db update failed", exc_info=True)