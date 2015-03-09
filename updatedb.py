__author__ = 'atlanmod'

import mysql.connector
from mysql.connector import errorcode
from gitquerier import GitQuerier
from datetime import datetime
from git2db import Git2Db
from analyse_reference_thread import AnalyseReferenceThread
from git import *
import config


class UpdateDb():

    def __init__(self, db_name, git_repo_path, before_date, logger):
        self.logger = logger
        self.git_repo_path = git_repo_path
        self.db_name = db_name
        self.before_date = before_date
        self.existing_refs = []
        self.querier = GitQuerier(git_repo_path, logger)

        self.cnx = mysql.connector.connect(**config.CONFIG)

    def select_repo_id(self, repo_name):
        cursor = self.cnx.cursor()
        query = "SELECT id FROM " + self.db_name + ".repository WHERE name = %s"
        arguments = [repo_name]
        cursor.execute(query, arguments)

        row = cursor.fetchone()
        cursor.close()
        repo_id = 0
        if row:
            repo_id = row[0]

        return repo_id

    def update_from_commit_in_ref(self, sha, git2db, ref_id, repo_id):
        ref = git2db.select_reference(repo_id, ref_id)
        ref_name = ref[0]
        ref_type = ref[1]

        #counter threads for references
        counter = 0
        #worker threads for reference
        workers = []
        for reference in self.querier.get_references():
            reference_name = reference[0]
            if reference_name == ref_name:
                #if the counter is less or equal to the maximum value, the process keeps adding workers to the list "workers"
                if counter <= config.MAX_THREADS_FOR_REFERENCES:
                    self.existing_refs.append(ref_name)

                    worker = AnalyseReferenceThread(ref_name, ref_type, repo_id, sha, self.before_date, self.git_repo_path, self.db_name, self.logger)
                    workers.append(worker)
                    counter += 1
                #if the counter is greater than the maximum value, the process executes the threads in the list "workers"
                else:
                    for w in workers:
                        w.start()

                    for w in workers:
                        w.join()

                    counter = 0
                    workers = []
        #check whether in the list "workers" there are still some threads to execute
        if workers:
            for w in workers:
                    w.start()

            for w in workers:
                w.join()

            workers = []
        return

    def update_existing_references(self, git2db, repo_id):
        cursor = self.cnx.cursor()
        query = "SELECT c.sha, lc.ref_id " \
                "FROM " + self.db_name + ".commit c " \
                "JOIN (SELECT ref_id, max(commit_id) as last_commit_id_in_ref FROM " + self.db_name + ".commit_in_reference WHERE repo_id = %s GROUP BY ref_id) as lc " \
                "ON c.id = lc.last_commit_id_in_ref"
        arguments = [repo_id]
        cursor.execute(query, arguments)

        row = cursor.fetchone()
        while row:
            sha = row[0]
            ref_id = row[1]
            self.update_from_commit_in_ref(sha, git2db, ref_id, repo_id)
            row = cursor.fetchone()
        cursor.close()
        return

    def add_new_references(self, repo_id):
        workers = []
        counter = 0
        for reference in self.querier.get_references():
            reference_name = reference[0]
            reference_type = reference[1]
            if reference_name not in self.existing_refs and reference_name != "origin/HEAD":
                #if the counter is less or equal to the maximum value, the process keeps adding workers to the list "workers"
                if counter <= config.MAX_THREADS_FOR_REFERENCES:
                    worker = AnalyseReferenceThread(reference_name, reference_type, repo_id,
                                                    None, self.before_date, self.git_repo_path, self.db_name, self.logger)
                    workers.append(worker)

                    counter += 1
                #if the counter is greater than the maximum value, the process executes the threads in the list "workers"
                else:
                    for w in workers:
                        w.start()

                    for w in workers:
                        w.join()

                    counter = 0
                    workers = []
        #check whether in the list "workers" there are still some threads to execute
        if workers:
            for w in workers:
                    w.start()

            for w in workers:
                w.join()

            workers = []

        return

    def update_repo(self, repo_id):
        git2db = Git2Db(self.db_name, self.git_repo_path, None, self.logger)
        self.update_existing_references(git2db, repo_id)
        self.add_new_references(repo_id)
        return

    def update(self):
        start_time = datetime.now()
        repo_id = self.select_repo_id(self.db_name)
        self.update_repo(repo_id)
        end_time = datetime.now()
        minutes_and_seconds = divmod((end_time-start_time).total_seconds(), 60)
        self.logger.info("UpdateDb: process finished after " + str(minutes_and_seconds[0])
                     + " minutes and " + str(round(minutes_and_seconds[1], 1)) + " secs")
        return