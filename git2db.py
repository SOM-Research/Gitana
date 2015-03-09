__author__ = 'atlanmod'

import mysql.connector
from mysql.connector import errorcode
import re
from datetime import datetime
from gitquerier import GitQuerier
from analyse_reference_thread import AnalyseReferenceThread

MAX_THREADS_FOR_REFERENCES = 5

class Git2Db():

    def __init__(self, db_name, git_repo_path, before_date, logger):
        self.logger = logger
        self.git_repo_path = git_repo_path
        self.db_name = db_name
        self.before_date = before_date

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

    def insert_repo(self):
        cursor = self.cnx.cursor()

        query = "INSERT IGNORE INTO " + self.db_name + ".repository " \
                "VALUES (%s, %s)"
        arguments = [None, self.db_name]
        cursor.execute(query, arguments)
        self.cnx.commit()

        query = "SELECT id " \
                "FROM " + self.db_name + ".repository " \
                "WHERE name = %s"
        arguments = [self.db_name]
        cursor.execute(query, arguments)
        id = cursor.fetchone()[0]

        cursor.close()
        return id

    def get_info_contribution(self):
        querier = GitQuerier(self.git_repo_path, self.logger)
        repo_id = self.insert_repo()

        workers = []
        counter = 0

        for reference in querier.get_references():
            if counter <= MAX_THREADS_FOR_REFERENCES:
                ref_name = reference[0]
                ref_type = reference[1]

                worker = AnalyseReferenceThread(ref_name, ref_type, repo_id, self.before_date, self.git_repo_path, self.db_name, self.logger)
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

        self.fix_commit_parent_table(repo_id)
        querier.add_no_treated_extensions_to_log()

        return

    def fix_commit_parent_table(self, repo_id):
        cursor = self.cnx.cursor()

        query_select = "SELECT parent_sha " \
                       "FROM " + self.db_name + ".commit_parent " \
                       "WHERE parent_id IS NULL AND repo_id = %s"
        arguments = [repo_id]
        cursor.execute(query_select, arguments)
        row = cursor.fetchone()
        while row:
            parent_sha = row[0]
            parent_id = self.select_commit(parent_sha)
            query_update = "UPDATE " + self.db_name + ".commit_parent " \
                           "SET parent_id = %s " \
                           "WHERE parent_id IS NULL AND parent_sha = %s AND repo_id = %s "
            arguments = [parent_id, parent_sha, repo_id]
            cursor.execute(query_update, arguments)
            self.cnx.commit()
            row = cursor.fetchone()

        cursor.close()
        return

    def extract(self):
        start_time = datetime.now()
        self.get_info_contribution()
        self.cnx.close()
        end_time = datetime.now()

        minutes_and_seconds = divmod((end_time-start_time).total_seconds(), 60)
        self.logger.info("Git2Db: process finished after " + str(minutes_and_seconds[0])
                     + " minutes and " + str(round(minutes_and_seconds[1], 1)) + " secs")
        return