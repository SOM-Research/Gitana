#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'valerio cosentino'

import sys
sys.path.insert(0, "..//..")

import mysql.connector
from mysql.connector import errorcode
from datetime import datetime
from querier_git import GitQuerier
from extractor.init_db import config_db
from subprocess import *
import logging
import logging.handlers
import glob
import os

LOG_FOLDER = "logs"

#do not import patches
LIGHT_IMPORT_TYPE = 1
#import patches but not at line level
MEDIUM_IMPORT_TYPE = 2
#import patches also at line level
FULL_IMPORT_TYPE = 3

#select the references (tags or branches) to import
REFERENCES = []
#REFERENCES = ["0.7.0", "0.7.1", "0.7.2", "0.7.3", "0.7.4", "0.8.0", "0.9.0",
#              "0.10.0", "1.0.0", "1.0.1", "1.1.2", "1.1.3", "1.1.4", "2.0.0",
#              "0.10.1_RC4", "0.10.2_RC5", "0.8.1_RC4", "0.8.2_RC4", "0.9.1_RC4", "0.9.2_RC3", "1.0.2_RC4", "1.1.0_RC4", "1.2.0M5"]

PROCESSES = 30 #30 len(REFERENCES)


class Git2DbMain():

    def __init__(self, project_name, db_name, repo_name, git_repo_path, before_date, import_last_commit, import_type):
        self.create_log_folder(LOG_FOLDER)
        LOG_FILENAME = LOG_FOLDER + "/git2db_main"
        self.delete_previous_logs(LOG_FOLDER)
        self.logger = logging.getLogger(LOG_FILENAME)
        fileHandler = logging.FileHandler(LOG_FILENAME + "-" + db_name + ".log", mode='w')
        formatter = logging.Formatter("%(asctime)s:%(levelname)s:%(message)s", "%Y-%m-%d %H:%M:%S")

        fileHandler.setFormatter(formatter)
        self.logger.setLevel(logging.INFO)
        self.logger.addHandler(fileHandler)

        self.git_repo_path = git_repo_path
        self.project_name = project_name
        self.db_name = db_name
        self.repo_name = repo_name
        self.before_date = before_date
        self.import_last_commit = import_last_commit
        self.import_type = import_type
        self.querier = GitQuerier(git_repo_path, self.logger)

        self.cnx = mysql.connector.connect(**config_db.CONFIG)
        self.set_database()

    def create_log_folder(self, name):
        if not os.path.exists(name):
            os.makedirs(name)

    def delete_previous_logs(self, path):
        files = glob.glob(path + "/*")
        for f in files:
            try:
                os.remove(f)
            except:
                continue

    def insert_project(self):
        cursor = self.cnx.cursor()
        query = "INSERT IGNORE INTO project " \
                "VALUES (%s, %s)"
        arguments = [None, self.project_name]
        cursor.execute(query, arguments)
        self.cnx.commit()

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
        project_id = self.insert_project()
        repo_id = self.insert_repo(project_id)

        processes = []
        counter = 0
        for reference in self.querier.get_references():
            if REFERENCES:
                if reference[0] in REFERENCES:
                    p = Popen(['python', 'git2db_reference.py', str(repo_id), reference[0], self.db_name, self.git_repo_path,
                              str(self.before_date), str(self.import_last_commit), str(self.import_type), str(counter), "", "--encoding", "utf-8"])
                    processes.append(p)
            else:
                p = Popen(['python', 'git2db_reference.py', str(repo_id), reference[0], self.db_name, self.git_repo_path,
                           str(self.before_date), str(self.import_last_commit), str(self.import_type), str(counter), "", "--encoding", "utf-8"])
                processes.append(p)

            while len(processes) == PROCESSES:
                for p in processes:
                    p.poll()
                    if p.returncode is not None:
                        processes.remove(p)

            counter += 1

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

    def extract(self):
        start_time = datetime.now()
        self.get_info_contribution()
        self.querier.add_no_treated_extensions_to_log()
        end_time = datetime.now()
        self.cnx.close()

        minutes_and_seconds = divmod((end_time-start_time).total_seconds(), 60)
        self.logger.info("Git2Db: process finished after " + str(minutes_and_seconds[0])
                     + " minutes and " + str(round(minutes_and_seconds[1], 1)) + " secs")
        return


def main():
    a = Git2DbMain(config_db.PROJECT_NAME, config_db.DB_NAME, config_db.REPO_NAME, config_db.GIT_REPO_PATH, "", False, 1)
    a.extract()

if __name__ == "__main__":
    main()