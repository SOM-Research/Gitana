__author__ = 'atlanmod'

import mysql.connector
from mysql.connector import errorcode
from gitquerier import GitQuerier
from datetime import datetime
from git2db import Git2Db
from git import *


class UpdateDb():

    def __init__(self, db_name, git_repo_path, before_date, logger):
        self.logger = logger
        self.git_repo_path = git_repo_path
        self.db_name = db_name
        self.before_date = before_date
        self.existing_refs = []
        self.querier = GitQuerier(git_repo_path, logger)

        CONFIG = {
            'user': 'root',
            'password': 'root',
            'host': 'localhost',
            'port': '3306',
            'database': db_name,
            'raise_on_warnings': False,
            'buffered': True
        }

        self.cnx = mysql.connector.connect(**CONFIG)

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

    def update_from_commit_in_ref(self, sha, git2db, ref_id, repo_id):
        ref_name = git2db.select_reference_name(repo_id, ref_id)

        for reference in self.querier.get_references():
            reference_name = reference[0]
            if reference_name == ref_name:
                self.existing_refs.append(ref_name)

                if self.before_date:
                    commits = self.querier.collect_all_commits_after_sha_before_date(reference_name, sha, self.before_date)
                else:
                    commits = self.querier.collect_all_commits_after_sha(reference_name, sha)

                if not commits:
                    if self.before_date:
                        self.logger.warning("UpdateDb: no commits to analyse after sha: " + str(sha) + " and before date: " + self.before_date)
                    else:
                        self.logger.warning("UpdateDb: no commits to analyse after sha: " + str(sha))
                else:
                    git2db.analyse_commits(commits, reference_name, repo_id)
        return

    def update_existing_references(self, git2db, repo_id):
        cursor = self.cnx.cursor()
        query = "SELECT c.sha, lc.ref_id " \
                "FROM commit c " \
                "JOIN (SELECT ref_id, max(commit_id) as last_commit_id_in_ref FROM commit_in_reference WHERE repo_id = %s GROUP BY ref_id) as lc " \
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

    def add_new_references(self, git2db, repo_id):
        for reference in self.querier.get_references():
            reference_name = reference[0]
            reference_type = reference[1]
            if reference_name not in self.existing_refs and reference_name != "origin/HEAD":
                if self.before_date:
                    commits = self.querier.collect_all_commits_before_date(reference_name, self.before_date)
                else:
                    commits = self.querier.collect_all_commits(reference_name)
                git2db.analyse_reference(reference_name, reference_type, repo_id)
                git2db.analyse_commits(commits, reference_name, repo_id)
        return

    def update_repo(self, repo_id):
        git2db = Git2Db(self.db_name, self.git_repo_path, None, self.logger)
        self.update_existing_references(git2db, repo_id)
        self.add_new_references(git2db, repo_id)
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