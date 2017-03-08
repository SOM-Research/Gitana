#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'valerio cosentino'

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

    LOG_FOLDER_PATH = "logs"
    LOG_NAME = "gitana"
    STACKOVERFLOW_TYPE = 'stackoverflow'
    ECLIPSE_FORUM_TYPE = 'eclipse_forum'
    GITHUB_TYPE = 'github'
    BUGZILLA_TYPE = 'bugzilla'
    SLACK_TYPE = 'slack'

    def __init__(self, config, log_folder_path):
        self._config = config

        if log_folder_path:
            self.create_log_folder(log_folder_path)
            self._log_folder_path = log_folder_path
        else:
            self.create_log_folder(self.LOG_FOLDER_PATH)
            self._log_folder_path = self.LOG_FOLDER_PATH

        self._log_path = self._log_folder_path + "/" + Gitana.LOG_NAME + "-"

    def create_log_folder(self, name):
        if not os.path.exists(name):
            os.makedirs(name)

    def delete_previous_logs(self):
        files = glob.glob(self._log_folder_path + "/*")
        for f in files:
            try:
                os.remove(f)
            except:
                continue

    def init_db(self, db_name):
        db = DbSchema(self._config, self._log_path)
        db.init_database(db_name)

    def create_project(self, db_name, project_name):
        db = DbSchema(self._config, self._log_path)
        db.create_project(db_name, project_name)

    def list_projects(self, db_name):
        db = DbSchema(self._config, self._log_path)
        projects = db.list_projects(db_name)
        for p in projects:
            print p

    def import_git_data(self, db_name, project_name, repo_name, git_repo_path, before_date, import_type, references, processes):
        git2db = Git2DbMain(db_name, project_name,
                                   repo_name, git_repo_path, before_date, import_type, references, processes,
                                   self._config, self._log_path)
        git2db.extract()

    def update_git_data(self, db_name, project_name, repo_name, git_repo_path, before_date, processes):
        git2db = Git2DbUpdate(db_name, project_name,
                              repo_name, git_repo_path, before_date, processes,
                              self._config, self._log_path)
        git2db.update()

    def import_bugzilla_tracker_data(self, db_name, project_name, repo_name, issue_tracker_name, url, product, before_date, processes):
        issue2db = BugzillaIssue2DbMain(db_name, project_name,
                                repo_name, Gitana.BUGZILLA_TYPE, issue_tracker_name, url, product, before_date, processes,
                                self._config, self._log_path)
        issue2db.extract()

    def update_bugzilla_tracker_data(self, db_name, project_name, repo_name, issue_tracker_name, url, product, processes):
        issue2db = BugzillaIssue2DbUpdate(db_name, project_name,
                                  repo_name, issue_tracker_name, url, product, processes,
                                  self._config, self._log_path)
        issue2db.update()

    def import_eclipse_forum_data(self, db_name, project_name, forum_name, eclipse_forum_url, before_date, processes):
        forum2db = EclipseForum2DbMain(db_name, project_name,
                                Gitana.ECLIPSE_FORUM_TYPE, forum_name, eclipse_forum_url, before_date, processes,
                                self._config, self._log_path)
        forum2db.extract()

    def update_eclipse_forum_data(self, db_name, project_name, forum_name, eclipse_forum_url, processes):
        forum2db = EclipseForum2DbUpdate(db_name, project_name, forum_name, eclipse_forum_url, processes,
                                  self._config, self._log_path)
        forum2db.update()

    def import_stackoverflow_data(self, db_name, project_name, forum_name, search_query, before_date, tokens):
        stackoverflow2db = StackOverflow2DbMain(db_name, project_name,
                                                Gitana.STACKOVERFLOW_TYPE, forum_name, search_query, before_date, tokens,
                                                self._config, self._log_path)
        stackoverflow2db.extract()

    def update_stackoverflow_data(self, db_name, project_name, forum_name, tokens):
        stackoverflow2db = StackOverflow2DbUpdate(db_name, project_name, forum_name, tokens,
                                                  self._config, self._log_path)
        stackoverflow2db.update()

    def import_slack_data(self, db_name, project_name, instant_messaging_name, before_date, channels, tokens):
        slack2db = Slack2DbMain(db_name, project_name,
                                Gitana.SLACK_TYPE, instant_messaging_name, before_date, channels, tokens,
                                self._config, self._log_path)
        slack2db.extract()

    def update_slack_data(self, db_name, project_name, instant_messaging_name, tokens):
        slack2db = Slack2DbUpdate(db_name, project_name, instant_messaging_name, tokens,
                                  self._config, self._log_path)
        slack2db.update()

    def import_github_tracker_data(self, db_name, project_name, repo_name, issue_tracker_name, github_repo_full_name, before_date, tokens):
        github2db = GitHubIssue2DbMain(db_name, project_name, repo_name, Gitana.GITHUB_TYPE, issue_tracker_name, github_repo_full_name, before_date, tokens,
                                       self._config, self._log_path)
        github2db.extract()

    def update_github_tracker_data(self, db_name, project_name, repo_name, issue_tracker_name, github_repo_full_name, tokens):
        github2db = GitHubIssue2DbUpdate(db_name, project_name, repo_name, issue_tracker_name, github_repo_full_name, tokens,
                                         self._config, self._log_path)
        github2db.update()
