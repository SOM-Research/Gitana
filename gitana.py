__author__ = 'valerio cosentino'

import mysql.connector
from mysql.connector import errorcode
import os
import logging
import logging.handlers
import glob
import uuid

from extractor.db.dbschema import DbSchema
from extractor.cvs.git.git2db_extract_main import Git2DbMain
from extractor.cvs.git.git2db_update import Git2DbUpdate
from extractor.issue_tracker.bugzilla.issue2db_extract_main import Issue2DbMain
from extractor.issue_tracker.bugzilla.issue2db_update import Issue2DbUpdate
from extractor.forum.eclipse.forum2db_extract_main import Forum2DbMain
from extractor.forum.eclipse.forum2db_update import Forum2DbUpdate

LOG_FOLDER_PATH = "logs"
LOG_NAME = "gitana"


class Gitana():

    def __init__(self, config, log_folder_path):
        self.config = config
        self.cnx = mysql.connector.connect(**self.config)

        if log_folder_path:
            self.create_log_folder(log_folder_path)
            self.log_folder_path = log_folder_path
        else:
            self.create_log_folder(LOG_FOLDER_PATH)
            self.log_folder_path = LOG_FOLDER_PATH

        self.log_path = self.log_folder_path + "/" + LOG_NAME + "-" + str(uuid.uuid4())[:5] + ".log"
        self.logger = logging.getLogger(self.log_path)
        fileHandler = logging.FileHandler(self.log_path, mode='w')
        formatter = logging.Formatter("%(asctime)s:%(levelname)s:%(message)s", "%Y-%m-%d %H:%M:%S")

        fileHandler.setFormatter(formatter)
        self.logger.setLevel(logging.INFO)
        self.logger.addHandler(fileHandler)

    def create_log_folder(self, name):
        if not os.path.exists(name):
            os.makedirs(name)

    def delete_previous_logs(self):
        files = glob.glob(self.log_folder_path + "/*")
        for f in files:
            try:
                os.remove(f)
            except:
                continue

    def init_db(self, db_name):
        self.logger.info("initializing db")
        db = DbSchema(self.cnx, self.logger)
        db.init_database(db_name)

    def create_project(self, db_name, project_name):
        self.logger.info("creating project")
        db = DbSchema(self.cnx, self.logger)
        db.create_project(db_name, project_name)

    def list_projects(self, db_name):
        db = DbSchema(self.cnx, self.logger)
        projects = db.list_projects(db_name)
        for p in projects:
            print p

    def import_git_data(self, db_name, project_name, repo_name, git_repo_path, before_date, import_type, references, processes):
        self.logger.info("importing git data")
        git2db = Git2DbMain(db_name, project_name,
                                   repo_name, git_repo_path, before_date, import_type, references, processes,
                                   self.config, self.logger)
        git2db.extract()

    def update_git_data(self, db_name, project_name, repo_name, git_repo_path, before_date, recover_import, import_new_references, processes):
        self.logger.info("updating git data")
        git2db = Git2DbUpdate(db_name, project_name,
                              repo_name, git_repo_path, before_date, recover_import, import_new_references, processes,
                              self.config, self.logger)
        git2db.update()

    def import_bugzilla_tracker_data(self, db_name, project_name, repo_name, url, product, before_date, recover_import, processes):
        self.logger.info("importing bugzilla data")
        issue2db = Issue2DbMain(db_name, project_name,
                                repo_name, "bugzilla", url, product, before_date, recover_import, processes,
                                self.config, self.logger)
        issue2db.extract()

    def update_bugzilla_tracker_data(self, db_name, project_name, repo_name, url, product, processes):
        self.logger.info("updating bugzilla data")
        issue2db = Issue2DbUpdate(db_name, project_name,
                                  repo_name, url, product, processes,
                                  self.config, self.logger)
        issue2db.update()

    def import_eclipse_forum_data(self, db_name, project_name, eclipse_forum_url, before_date, recover_import, processes):
        self.logger.info("importing eclipse forum data")
        forum2db = Forum2DbMain(db_name, project_name,
                                "eclipse_forum", eclipse_forum_url, before_date, recover_import, processes,
                                self.config, self.logger)
        forum2db.extract()

    def update_eclipse_forum_data(self, db_name, project_name, before_date, recover_import, processes):
        self.logger.info("importing eclipse forum data")
        forum2db = Forum2DbUpdate(db_name, project_name, before_date, recover_import, processes,
                                  self.config, self.logger)
        forum2db.update()

    def import_github_tracker_data(self, db_name, project_name, repo_name, github_repo_full_name, before_date, recover_import, tokens):
        #TODO
        print "here"
