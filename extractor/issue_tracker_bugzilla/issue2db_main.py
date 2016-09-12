__author__ = 'valerio cosentino'

import mysql.connector
from mysql.connector import errorcode
from datetime import datetime
from querier_bugzilla import BugzillaQuerier
from extractor.init_db import config_db
from subprocess import *
import logging
import logging.handlers
import glob
import os

TYPE = "bugzilla"
URL = "https://bugs.eclipse.org/bugs/xmlrpc.cgi"
PRODUCT = "papyrus"
BEFORE_DATE = None
RECOVER_IMPORT = False

PROCESSES = 10


class Issue2DbMain():

    def __init__(self, db_name, repo_name, type, url, product, before_date, recover_import):
        LOG_FILENAME = "logs/issue2db_main"
        self.delete_previous_logs("logs")
        self.logger = logging.getLogger(LOG_FILENAME)
        fileHandler = logging.FileHandler(LOG_FILENAME + "-" + db_name + ".log", mode='w')
        formatter = logging.Formatter("%(asctime)s:%(levelname)s:%(message)s", "%Y-%m-%d %H:%M:%S")

        fileHandler.setFormatter(formatter)
        self.logger.setLevel(logging.INFO)
        self.logger.addHandler(fileHandler)

        self.type = type
        self.url = url
        self.db_name = db_name
        self.repo_name = repo_name
        self.before_date = before_date
        self.recover_import = recover_import

        self.querier = BugzillaQuerier(url, product, self.logger)

        self.cnx = mysql.connector.connect(**config_db.CONFIG)
        self.set_database()
        self.set_settings()

    def delete_previous_logs(self, path):
        files = glob.glob(path + "/*")
        for f in files:
            os.remove(f)

    def select_repo(self):
        cursor = self.cnx.cursor()
        query = "SELECT id " \
                "FROM repository " \
                "WHERE name = %s"
        arguments = [self.repo_name]
        cursor.execute(query, arguments)
        id = cursor.fetchone()[0]
        cursor.close()
        return id

    def insert_issue_tracker(self, repo_id):
        cursor = self.cnx.cursor()
        query = "INSERT IGNORE INTO issue_tracker " \
                "VALUES (%s, %s, %s, %s)"
        arguments = [None, repo_id, self.url, self.type]
        cursor.execute(query, arguments)
        self.cnx.commit()

        query = "SELECT id " \
                "FROM issue_tracker " \
                "WHERE url = %s"
        arguments = [self.url]
        cursor.execute(query, arguments)
        id = cursor.fetchone()[0]
        cursor.close()
        return id

    def get_already_imported_issue_ids(self, issue_tracker_id):
        issue_ids = []
        cursor = self.cnx.cursor()
        query = "SELECT id FROM issue WHERE issue_tracker_id = %s"
        arguments = [issue_tracker_id]
        cursor.execute(query, arguments)
        row = cursor.fetchone()

        while row:
            issue_ids.append(row[0])
            row = cursor.fetchone()
        cursor.close()

        return issue_ids

    def pass_list_as_argument(self, elements):
        return '-'.join([str(e) for e in elements])

    def get_intervals(self, elements):
        chunk_size = len(elements)/PROCESSES

        if chunk_size == 0:
            chunks = [elements]
        else:
            chunks = [elements[i:i + chunk_size] for i in range(0, len(elements), chunk_size)]

        intervals = []
        for chunk in chunks:
            intervals.append((chunk[0], chunk[-1]))

        return intervals

    def split_issue_extraction(self):
        repo_id = self.select_repo()
        issue_tracker_id = self.insert_issue_tracker(repo_id)
        if self.recover_import:
            imported = self.get_already_imported_issue_ids(issue_tracker_id)
            issues = list(set(self.querier.get_issue_ids(None, None)) - set(imported))
            issues.sort()
        else:
            issues = self.querier.get_issue_ids(None, None)

        self.cnx.close()

        intervals = self.get_intervals([id for id in issues])

        processes = []
        for interval in intervals:
            p = Popen(['python', 'issue2db.py', self.type, URL, PRODUCT, self.db_name, str(repo_id), str(issue_tracker_id), str(interval[0]), str(interval[1])])
            processes.append(p)

            while len(processes) == PROCESSES:
                for p in processes:
                    p.poll()
                    if p.returncode is not None:
                        processes.remove(p)

        while processes:
            for p in processes:
                p.poll()
                if p.returncode is not None:
                    processes.remove(p)

        return

    def set_database(self):
        cursor = self.cnx.cursor()
        use_database = "USE " + self.db_name
        cursor.execute(use_database)
        cursor.close()

    def set_settings(self):
        cursor = self.cnx.cursor()
        cursor.execute("set global innodb_file_format = BARRACUDA")
        cursor.execute("set global innodb_file_format_max = BARRACUDA")
        cursor.execute("set global innodb_large_prefix = ON")
        cursor.execute("set global character_set_server = utf8")
        cursor.close()

    def extract(self):
        start_time = datetime.now()
        self.split_issue_extraction()
        end_time = datetime.now()
        self.cnx.close()

        minutes_and_seconds = divmod((end_time-start_time).total_seconds(), 60)
        self.logger.info("Issue2Db: process finished after " + str(minutes_and_seconds[0])
                     + " minutes and " + str(round(minutes_and_seconds[1], 1)) + " secs")
        return


def main():
    a = Issue2DbMain(config_db.DB_NAME, config_db.REPO_NAME, TYPE, URL, PRODUCT, BEFORE_DATE, RECOVER_IMPORT)
    a.extract()

if __name__ == "__main__":
    main()