#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'valerio cosentino'

"""
Gitana exports and digests the data of a Git repository, issue trackers and Q&A web-sites to a relational database
in order to ease browsing and querying activities with standard SQL syntax and tools.
"""

import os
import glob

from importers.db.dbschema import DbSchema
from importers.vcs.git.git2db_extract_main import Git2DbMain
from importers.vcs.git.git2db_update import Git2DbUpdate
from importers.issue_tracker.bugzilla.issue2db_extract_main import BugzillaIssue2DbMain
from importers.issue_tracker.bugzilla.issue2db_update import BugzillaIssue2DbUpdate
from importers.issue_tracker.github.issue2db_extract_main import GitHubIssue2DbMain
from importers.issue_tracker.github.issue2db_update import GitHubIssue2DbUpdate
from importers.forum.eclipse.forum2db_extract_main import EclipseForum2DbMain
from importers.forum.eclipse.forum2db_update import EclipseForum2DbUpdate
from importers.forum.stackoverflow.stackoverflow2db_extract_main import StackOverflow2DbMain
from importers.forum.stackoverflow.stackoverflow2db_update import StackOverflow2DbUpdate
from importers.instant_messaging.slack.slack2db_extract_main import Slack2DbMain
from importers.instant_messaging.slack.slack2db_update import Slack2DbUpdate


class Gitana():
    """
    This class represents the facade of the tool
    """

    LOG_FOLDER_PATH = "logs"
    LOG_NAME = "gitana"
    STACKOVERFLOW_TYPE = 'stackoverflow'
    ECLIPSE_FORUM_TYPE = 'eclipse_forum'
    GITHUB_TYPE = 'github'
    BUGZILLA_TYPE = 'bugzilla'
    SLACK_TYPE = 'slack'

    def __init__(self, config, log_folder_path):
        """
        :type config: dict
        :param config: the DB configuration file

        :type log_folder_path: str
        :param log_folder_path: the log folder path
        """
        self._config = config

        if log_folder_path:
            self.create_log_folder(log_folder_path)
            self._log_folder_path = log_folder_path
        else:
            self.create_log_folder(self.LOG_FOLDER_PATH)
            self._log_folder_path = self.LOG_FOLDER_PATH

        self._log_path = self._log_folder_path + "/" + Gitana.LOG_NAME + "-"

    def create_log_folder(self, name):
        """
        creates the log folder

        :type name: str
        :param name: the log folder path
        """
        if not os.path.exists(name):
            os.makedirs(name)

    def delete_previous_logs(self):
        """
        deletes the content of the log folder
        """
        files = glob.glob(self._log_folder_path + "/*")
        for f in files:
            try:
                os.remove(f)
            except:
                continue

    def init_db(self, db_name):
        """
        initializes the Gitana DB schema

        :type db_name: str
        :param db_name: the name of the DB to initialize
        """
        db = DbSchema(self._config, self._log_path)
        db.init_database(db_name)

    def create_project(self, db_name, project_name):
        """
        inserts a project in the DB

        :type db_name: str
        :param db_name: the name of an existing DB

        :type project_name: str
        :param project_name: the name of the project to create
        """
        db = DbSchema(self._config, self._log_path)
        db.create_project(db_name, project_name)

    def list_projects(self, db_name):
        """
        lists all projects contained in the DB

        :type db_name: str
        :param db_name: the name of the DB
        """
        db = DbSchema(self._config, self._log_path)
        projects = db.list_projects(db_name)
        for p in projects:
            print p

    def import_git_data(self, db_name, project_name, repo_name, git_repo_path, before_date, import_type, references, processes):
        """
        imports Git data to the DB

        :type db_name: str
        :param db_name: the name of an existing DB

        :type project_name: str
        :param project_name: the name of an existing project in the DB

        :type repo_name: str
        :param repo_name: the name of the repository to import

        :type git_repo_path: str
        :param git_repo_path: the path of the repository

        :type before_date: str
        :param before_date: import data before date (YYYY-mm-dd)

        :type import_type: int
        :param import_type: 1 = do not import patch content, 2 = import patch content but not at line level, 3 = import patch content at line level

        :type references: list str
        :param references: list of references (branches and tags) to import

        :type processes: int
        :param processes: number of processes to import the data (default 10)
        """
        git2db = Git2DbMain(db_name, project_name,
                                   repo_name, git_repo_path, before_date, import_type, references, processes,
                                   self._config, self._log_path)
        git2db.extract()

    def update_git_data(self, db_name, project_name, repo_name, git_repo_path, before_date, processes):
        """
        updates the Git data stored in the DB

        :type db_name: str
        :param db_name: the name of an existing DB

        :type project_name: str
        :param project_name: the name of an existing project in the DB

        :type repo_name: str
        :param repo_name: the name of an existing repository in the DB to update

        :type git_repo_path: str
        :param git_repo_path: the path of the repository

        :type before_date: str
        :param before_date: import data before date (YYYY-mm-dd)

        :type processes: int
        :param processes: number of processes to import the data (default 10)
        """
        git2db = Git2DbUpdate(db_name, project_name,
                              repo_name, git_repo_path, before_date, processes,
                              self._config, self._log_path)
        git2db.update()

    def import_bugzilla_tracker_data(self, db_name, project_name, repo_name, issue_tracker_name, url, product, before_date, processes):
        """
        imports Bugzilla issue tracker data to the DB

        :type db_name: str
        :param db_name: the name of an existing DB

        :type project_name: str
        :param project_name: the name of an existing project in the DB

        :type repo_name: str
        :param repo_name: the name of an existing repository in the DB

        :type issue_tracker_name: str
        :param issue_tracker_name: the name of the issue tracker to import

        :type url: str
        :param url: the URL of the issue tracker

        :type product: str
        :param product: the name of the product used in the issue tracker

        :type before_date: str
        :param before_date: import data before date (YYYY-mm-dd)

        :type processes: int
        :param processes: number of processes to import the data (default 5)
        """
        issue2db = BugzillaIssue2DbMain(db_name, project_name,
                                repo_name, Gitana.BUGZILLA_TYPE, issue_tracker_name, url, product, before_date, processes,
                                self._config, self._log_path)
        issue2db.extract()

    def update_bugzilla_tracker_data(self, db_name, project_name, repo_name, issue_tracker_name, url, product, processes):
        """
        updates the Bugzilla issue tracker data stored in the DB

        :type db_name: str
        :param db_name: the name of an existing DB

        :type project_name: str
        :param project_name: the name of an existing project in the DB

        :type repo_name: str
        :param repo_name: the name of an existing repository in the DB

        :type issue_tracker_name: str
        :param issue_tracker_name: the name of an existing issue tracker in the DB to update

        :type url: str
        :param url: the URL of the issue tracker

        :type product: str
        :param product: the name of the product used in the issue tracker

        :type processes: int
        :param processes: number of processes to import the data (default 5)
        """
        issue2db = BugzillaIssue2DbUpdate(db_name, project_name,
                                  repo_name, issue_tracker_name, url, product, processes,
                                  self._config, self._log_path)
        issue2db.update()

    def import_eclipse_forum_data(self, db_name, project_name, forum_name, eclipse_forum_url, before_date, processes):
        """
        imports Eclipse forum data to the DB

        :type db_name: str
        :param db_name: the name of an existing DB

        :type project_name: str
        :param project_name: the name of an existing project in the DB

        :type forum_name: str
        :param forum_name: the name of the forum to import

        :type eclipse_forum_url: str
        :param eclipse_forum_url: the URL of the forum

        :type before_date: str
        :param before_date: import data before date (YYYY-mm-dd)

        :type processes: int
        :param processes: number of processes to import the data (default 2)
        """
        forum2db = EclipseForum2DbMain(db_name, project_name,
                                Gitana.ECLIPSE_FORUM_TYPE, forum_name, eclipse_forum_url, before_date, processes,
                                self._config, self._log_path)
        forum2db.extract()

    def update_eclipse_forum_data(self, db_name, project_name, forum_name, eclipse_forum_url, processes):
        """
        updates the Eclipse forum data stored in the DB

        :type db_name: str
        :param db_name: the name of an existing DB

        :type project_name: str
        :param project_name: the name of an existing project in the DB

        :type forum_name: str
        :param forum_name: the name of an existing forum in the DB to update

        :type eclipse_forum_url: str
        :param eclipse_forum_url: the URL of the forum

        :type processes: int
        :param processes: number of processes to import the data (default 2)
        """
        forum2db = EclipseForum2DbUpdate(db_name, project_name, forum_name, eclipse_forum_url, processes,
                                  self._config, self._log_path)
        forum2db.update()

    def import_stackoverflow_data(self, db_name, project_name, forum_name, search_query, before_date, tokens):
        """
        imports Stackoverflow data to the DB

        :type db_name: str
        :param db_name: the name of an existing DB

        :type project_name: str
        :param project_name: the name of an existing project in the DB

        :type forum_name: str
        :param forum_name: the name of the forum to import

        :type search_query: str
        :param search_query: retrieves Stackoverflow questions labeled with a given string

        :type before_date: str
        :param before_date: import data before date (YYYY-mm-dd)

        :type tokens: list str
        :param tokens: list of Stackoverflow tokens
        """
        stackoverflow2db = StackOverflow2DbMain(db_name, project_name,
                                                Gitana.STACKOVERFLOW_TYPE, forum_name, search_query, before_date, tokens,
                                                self._config, self._log_path)
        stackoverflow2db.extract()

    def update_stackoverflow_data(self, db_name, project_name, forum_name, tokens):
        """
        updates Stackoverflow data stored in the DB

        :type db_name: str
        :param db_name: the name of an existing DB

        :type project_name: str
        :param project_name: the name of an existing project in the DB

        :type forum_name: str
        :param forum_name: the name of an existing forum in the DB to update

        :type tokens: list str
        :param tokens: list of Stackoverflow tokens
        """
        stackoverflow2db = StackOverflow2DbUpdate(db_name, project_name, forum_name, tokens,
                                                  self._config, self._log_path)
        stackoverflow2db.update()

    def import_slack_data(self, db_name, project_name, instant_messaging_name, before_date, channels, tokens):
        """
        imports Slack data to the DB

        :type db_name: str
        :param db_name: the name of an existing DB

        :type project_name: str
        :param project_name: the name of an existing project in the DB

        :type instant_messaging_name: str
        :param instant_messaging_name: the name of the instant messaging to import

        :type before_date: str
        :param before_date: import data before date (YYYY-mm-dd)

        :type channels: list str
        :param channels: list of channels to import

        :type tokens: list str
        :param tokens: list of Slack tokens
        """
        slack2db = Slack2DbMain(db_name, project_name,
                                Gitana.SLACK_TYPE, instant_messaging_name, before_date, channels, tokens,
                                self._config, self._log_path)
        slack2db.extract()

    def update_slack_data(self, db_name, project_name, instant_messaging_name, tokens):
        """
        updates Slack data stored in the DB

        :type db_name: str
        :param db_name: the name of an existing DB

        :type project_name: str
        :param project_name: the name of an existing project in the DB

        :type instant_messaging_name: str
        :param instant_messaging_name: the name of an existing instant messaging in the DB to update

        :type tokens: list str
        :param tokens: list of Slack tokens
        """
        slack2db = Slack2DbUpdate(db_name, project_name, instant_messaging_name, tokens,
                                  self._config, self._log_path)
        slack2db.update()

    def import_github_tracker_data(self, db_name, project_name, repo_name, issue_tracker_name, github_repo_full_name, before_date, tokens):
        """
        imports GitHub issue tracker data to the DB

        :type db_name: str
        :param db_name: the name of an existing DB

        :type project_name: str
        :param project_name: the name of an existing project in the DB

        :type repo_name: str
        :param repo_name: the name of an existing repository in the DB

        :type issue_tracker_name: str
        :param issue_tracker_name: the name of the issue tracker to import

        :type github_repo_full_name: str
        :param github_repo_full_name: full name of the GitHub repository

        :type before_date: str
        :param before_date: import data before date (YYYY-mm-dd)

        :type tokens: list str
        :param tokens: list of GitHub tokens
        """
        github2db = GitHubIssue2DbMain(db_name, project_name, repo_name, Gitana.GITHUB_TYPE, issue_tracker_name, github_repo_full_name, before_date, tokens,
                                       self._config, self._log_path)
        github2db.extract()

    def update_github_tracker_data(self, db_name, project_name, repo_name, issue_tracker_name, github_repo_full_name, tokens):
        """
        updates GitHub issue tracker data stored in the DB

        :type db_name: str
        :param db_name: the name of an existing DB

        :type project_name: str
        :param project_name: the name of an existing project in the DB

        :type repo_name: str
        :param repo_name: the name of an existing repository in the DB

        :type issue_tracker_name: str
        :param issue_tracker_name: the name of an existing issue tracker to update

        :type github_repo_full_name: str
        :param github_repo_full_name: full name of the GitHub repository

        :type tokens: list str
        :param tokens: list of GitHub tokens
        """
        github2db = GitHubIssue2DbUpdate(db_name, project_name, repo_name, issue_tracker_name, github_repo_full_name, tokens,
                                         self._config, self._log_path)
        github2db.update()
