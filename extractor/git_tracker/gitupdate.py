#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'valerio cosentino'

import sys
sys.path.insert(0, "..//..")

import mysql.connector
from mysql.connector import errorcode
from querier_git import GitQuerier
from datetime import datetime
import git2db_main
from extractor.init_db import config_db
import logging
import logging.handlers
from subprocess import *
import glob
import os

BEFORE_DATE = ""
IMPORT_LAST_COMMIT = False
IMPORT_NEW_REFERENCES = True
LOG_FOLDER = "logs"


class GitUpdate():

    def __init__(self, db_name, repo_name, git_repo_path, before_date, import_last_commit):
        self.create_log_folder(LOG_FOLDER)
        LOG_FILENAME = LOG_FOLDER + "/gitupdate"
        self.delete_previous_logs(LOG_FOLDER)
        self.logger = logging.getLogger(LOG_FILENAME)
        fileHandler = logging.FileHandler(LOG_FILENAME + "-" + db_name + ".log", mode='w')
        formatter = logging.Formatter("%(asctime)s:%(levelname)s:%(message)s", "%Y-%m-%d %H:%M:%S")

        fileHandler.setFormatter(formatter)
        self.logger.setLevel(logging.INFO)
        self.logger.addHandler(fileHandler)

        self.git_repo_path = git_repo_path
        self.db_name = db_name
        self.repo_name = repo_name
        self.before_date = before_date
        self.import_last_commit = import_last_commit
        self.existing_refs = []
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

        processes = []
        counter = 0
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

                    p = Popen(['python', 'git2db_reference.py', str(repo_id), reference_name, self.db_name, self.git_repo_path,
                               str(self.before_date), str(self.import_last_commit), str(import_type), str(counter), sha])

                    processes.append(p)

                    while len(processes) == git2db_main.PROCESSES:
                        for p in processes:
                            p.poll()
                            if p.returncode is not None:
                                processes.remove(p)

                    break

            counter += 1

        while processes:
            for p in processes:
                p.poll()
                if p.returncode is not None:
                    processes.remove(p)

        cursor.close()
        return

    def add_new_references(self, repo_id, import_type):
        processes = []
        counter = 0

        for reference in self.querier.get_references():
            reference_name = reference[0]
            if reference_name not in self.existing_refs and reference_name != "origin/HEAD":
                p = Popen(['python', 'git2db_reference.py', str(repo_id), reference_name, self.db_name, self.git_repo_path,
                           str(self.before_date), str(self.import_last_commit), str(import_type), str(counter), ""])
                processes.append(p)

                while len(processes) == git2db_main.PROCESSES:
                    for p in processes:
                        p.poll()
                        if p.returncode is not None:
                            processes.remove(p)

            counter += 1

        while processes:
            for p in processes:
                p.poll()
                if p.returncode:
                    processes.remove(p)

        return

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

        if IMPORT_NEW_REFERENCES:
            self.add_new_references(repo_id, import_type)
        return

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

    def set_database(self):
        cursor = self.cnx.cursor()
        use_database = "USE " + self.db_name
        cursor.execute(use_database)
        cursor.close()

    def update(self):
        start_time = datetime.now()
        repo_id = self.select_repo_id(self.repo_name)

        self.update_repo(repo_id, self.get_import_type(repo_id))
        end_time = datetime.now()
        self.cnx.close()
        minutes_and_seconds = divmod((end_time-start_time).total_seconds(), 60)
        self.logger.info("UpdateDb: process finished after " + str(minutes_and_seconds[0])
                     + " minutes and " + str(round(minutes_and_seconds[1], 1)) + " secs")
        return


def main():
    a = GitUpdate(config_db.DB_NAME, config_db.REPO_NAME, config_db.GIT_REPO_PATH, BEFORE_DATE, IMPORT_LAST_COMMIT)
    a.update()

if __name__ == "__main__":
    main()