__author__ = 'atlanmod'

import threading
import mysql.connector
from mysql.connector import errorcode
from gitquerier import GitQuerier
from analyse_commit_thread import AnalyseCommitThread

MAX_THREADS_FOR_COMMITS = 200

class AnalyseReferenceThread(threading.Thread):

    def __init__(self, ref_name, ref_type, repo_id, before_date, git_repo_path, db_name, logger):
        super(AnalyseReferenceThread, self).__init__()
        self.ref_name = ref_name
        self.ref_type = ref_type
        self.repo_id = repo_id
        self.before_date = before_date
        self.git_repo_path = git_repo_path
        self.db_name = db_name
        self.logger = logger

        CONFIG = {
            'user': 'root',
            'password': 'root',
            'host': 'localhost',
            'port': '3306',
            'raise_on_warnings': False,
            'charset': 'utf8',
            'buffered': True
        }

        self.cnx = mysql.connector.connect(**CONFIG)

    def run(self):
        self.analyse_reference(self.ref_name, self.ref_type, self.repo_id, self.before_date)
        self.cnx.close()

    def analyse_reference(self, ref_name, ref_type, repo_id, before_date):
        querier = GitQuerier(self.git_repo_path, self.logger)

        if before_date:
            commits = querier.collect_all_commits_before_date(ref_name, before_date)
        else:
            commits = querier.collect_all_commits(ref_name)

        self.insert_reference(repo_id, ref_name, ref_type)
        self.analyse_commits(commits, ref_name, repo_id)

    def analyse_commits(self, commits, ref, repo_id):
        ref_id = self.select_reference_id(repo_id, ref)

        workers = []

        counter = 0

        for c in commits:
            if counter <= MAX_THREADS_FOR_COMMITS:
                self.logger.info("Git2Db: analysing reference: " + ref + " -- commit " + str(commits.index(c)+1) + "/" + str(len(commits)) + " -- " + c.message)
                worker = AnalyseCommitThread(c.hexsha, ref_id, repo_id, self.git_repo_path, self.db_name, self.logger)
                workers.append(worker)

                counter += 1
            else:
                for w in workers:
                    w.start()

                for w in workers:
                    w.join()

                counter = 0
                workers = []

        if workers:
            for w in workers:
                    w.start()

            for w in workers:
                w.join()

            workers = []

        return

    def insert_reference(self, repo_id, ref_name, ref_type):
        cursor = self.cnx.cursor()

        query = "INSERT IGNORE INTO " + self.db_name + ".reference " \
                "VALUES (%s, %s, %s, %s)"
        arguments = [None, repo_id, ref_name, ref_type]
        cursor.execute(query, arguments)
        self.cnx.commit()

        cursor.close()
        return

    def select_reference_name(self, repo_id, ref_id):
        cursor = self.cnx.cursor()

        query = "SELECT name" \
                "FROM " + self.db_name + ".reference " \
                "WHERE id = %s and repo_id = %s"
        arguments = [ref_id, repo_id]
        cursor.execute(query, arguments)
        name = cursor.fetchone()[0]

        cursor.close()
        return name

    def select_reference_id(self, repo_id, ref_name):
        cursor = self.cnx.cursor()

        query = "SELECT id " \
                "FROM " + self.db_name + ".reference " \
                "WHERE name = %s and repo_id = %s"
        arguments = [ref_name, repo_id]
        cursor.execute(query, arguments)
        id = cursor.fetchone()[0]

        cursor.close()
        return id