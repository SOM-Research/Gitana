#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'valerio cosentino'

"""
Gitana imports and digests the data of Git repositories, issue trackers, Q&A web-sites and Instant messaging services to a relational database
in order to ease browsing and querying activities with standard SQL syntax and tools. It also provides support
to generate project activity reports and perform complex network analysis.
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
from exporters.report.report_exporter import ActivityReportExporter
from exporters.graph.graph_exporter import GraphExporter


class Gitana():
    """
    This is the main class you instanciate to use Gitana functionalities
    """

    LOG_FOLDER_PATH = "logs"
    LOG_NAME = "gitana"
    STACKOVERFLOW_TYPE = 'stackoverflow'
    ECLIPSE_FORUM_TYPE = 'eclipse_forum'
    GITHUB_TYPE = 'github'
    BUGZILLA_TYPE = 'bugzilla'
    SLACK_TYPE = 'slack'

    def __init__(self, config, log_folder_path=None):
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

    def add_git_tables(self, db_name):
        """
        :type db_name: str
        :param db_name: the name of the DB to initialize

        initializes git tables if they do not exist
        """
        db = DbSchema(db_name, self._config, self._log_path)
        db.add_git_tables()

    def add_issue_tracker_tables(self, db_name):
        """
        :type db_name: str
        :param db_name: the name of the DB to initialize

        initializes issue tracker tables if they do not exist
        """
        db = DbSchema(db_name, self._config, self._log_path)
        db.add_issue_tracker_tables()

    def add_instant_messaging_tables(self, db_name):
        """
        :type db_name: str
        :param db_name: the name of the DB to initialize

        initializes instant messaging tables if they do not exist
        """
        db = DbSchema(db_name, self._config, self._log_path)
        db.add_instant_messaging_tables()

    def add_forum_tables(self, db_name):
        """
        :type db_name: str
        :param db_name: the name of the DB to initialize

        initializes forum tables if they do not exist
        """
        db = DbSchema(db_name, self._config, self._log_path)
        db.add_forum_tables()

    def init_db(self, db_name, init_git=True, init_issue_tracker=True, init_forum=True, init_instant_messaging=True):
        """
        initializes the Gitana DB schema

        :type db_name: str
        :param db_name: the name of the DB to initialize

        :type init_git: bool
        :param init_git: if True, it initializes the tables containing git data

        :type init_issue_tracker: bool
        :param init_issue_tracker: if True, it initializes the tables containing issue tracker data

        :type init_forum: bool
        :param init_forum: if True, it initializes the tables containing forum data

        :type init_instant_messaging: bool
        :param init_instant_messaging: if True, it initializes the tables containing instant messaging data
        """
        db = DbSchema(db_name, self._config, self._log_path)
        db.init_database(init_git, init_issue_tracker, init_forum, init_instant_messaging)

    def create_project(self, db_name, project_name):
        """
        inserts a project in the DB

        :type db_name: str
        :param db_name: the name of an existing DB

        :type project_name: str
        :param project_name: the name of the project to create. It cannot be null
        """
        db = DbSchema(db_name, self._config, self._log_path)
        db.create_project(project_name)

    def create_repository(self, db_name, project_name, repo_name):
        """
        inserts a repository in the DB

        :type db_name: str
        :param db_name: the name of an existing DB

        :type project_name: str
        :param project_name: the name of an existing project

        :type repo_name: str
        :param repo_name: the name of the repository to insert
        """
        db = DbSchema(db_name, self._config, self._log_path)
        db.create_repository(project_name, repo_name)

    def list_projects(self, db_name):
        """
        lists all projects contained in the DB

        :type db_name: str
        :param db_name: the name of the DB
        """
        db = DbSchema(db_name, self._config, self._log_path)
        projects = db.list_projects()
        for p in projects:
            print p

    def import_git_data(self, db_name, project_name, repo_name, git_repo_path, import_type=1, references=None, before_date=None, processes=5):
        """
        imports Git data to the DB

        :type db_name: str
        :param db_name: the name of an existing DB

        :type project_name: str
        :param project_name: the name of an existing project in the DB

        :type repo_name: str
        :param repo_name: the name of the repository to import. It cannot be null

        :type git_repo_path: str
        :param git_repo_path: the local path of the repository. It cannot be null

        :type import_type: int
        :param import_type: 1 = do not import patch content, 2 = import patch content but not at line level, 3 = import patch content at line level, the default type will be 1

        :type references: list str
        :param references: list of references (branches and tags) to import. It can be null or ["ref-name-1", .., "ref-name-n"]

        :type before_date: str
        :param before_date: import data before date (YYYY-mm-dd). It can be null

        :type processes: int
        :param processes: number of processes to import the data. If null, the default number of processes is used (5)
        """
        git2db = Git2DbMain(db_name, project_name,
            repo_name, git_repo_path, before_date, import_type, references, processes,
            self._config, self._log_path)
        git2db.extract()

    def update_git_data(self, db_name, project_name, repo_name, git_repo_path, before_date=None, processes=5):
        """
        updates the Git data stored in the DB

        :type db_name: str
        :param db_name: the name of an existing DB

        :type project_name: str
        :param project_name: the name of an existing project in the DB

        :type repo_name: str
        :param repo_name: the name of an existing repository in the DB to update

        :type git_repo_path: str
        :param git_repo_path: the path of the repository. It cannot be null

        :type before_date: str
        :param before_date: import data before date (YYYY-mm-dd). It can be null

        :type processes: int
        :param processes: number of processes to import the data. If null, the default number of processes is used (5)
        """
        git2db = Git2DbUpdate(db_name, project_name,
            repo_name, git_repo_path, before_date, processes,
            self._config, self._log_path)
        git2db.update()

    def import_bugzilla_issue_data(self, db_name, project_name, repo_name, issue_tracker_name, url, product, before_date=None, processes=3):
        """
        imports Bugzilla issue data to the DB

        :type db_name: str
        :param db_name: the name of an existing DB

        :type project_name: str
        :param project_name: the name of an existing project in the DB

        :type repo_name: str
        :param repo_name: the name of an existing repository in the DB

        :type issue_tracker_name: str
        :param issue_tracker_name: the name of the issue tracker to import. It cannot be null

        :type url: str
        :param url: the URL of the issue tracker. It cannot be null

        :type product: str
        :param product: the name of the product used in the issue tracker. It cannot be null

        :type before_date: str
        :param before_date: import data before date (YYYY-mm-dd). It can be null

        :type processes: int
        :param processes: number of processes to import the data. If null, the default number of processes is used (3)
        """
        issue2db = BugzillaIssue2DbMain(
            db_name, project_name, repo_name, Gitana.BUGZILLA_TYPE,
            issue_tracker_name, url, product, before_date, processes,
            self._config, self._log_path)
        issue2db.extract()

    def update_bugzilla_issue_data(self, db_name, project_name, repo_name, issue_tracker_name, url, product, processes=3):
        """
        updates the Bugzilla issue data stored in the DB

        :type db_name: str
        :param db_name: the name of an existing DB

        :type project_name: str
        :param project_name: the name of an existing project in the DB

        :type repo_name: str
        :param repo_name: the name of an existing repository in the DB

        :type issue_tracker_name: str
        :param issue_tracker_name: the name of an existing issue tracker in the DB to update

        :type url: str
        :param url: the URL of the issue tracker. It cannot be null

        :type product: str
        :param product: the name of the product used in the issue tracker. It cannot be null

        :type processes: int
        :param processes: number of processes to import the data. If null, the default number of processes is used (3)
        """
        issue2db = BugzillaIssue2DbUpdate(
            db_name, project_name, repo_name, issue_tracker_name, url,
            product, processes, self._config, self._log_path)
        issue2db.update()

    def import_eclipse_forum_data(self, db_name, project_name, forum_name, eclipse_forum_url, before_date=None, processes=2):
        """
        imports Eclipse forum data to the DB

        :type db_name: str
        :param db_name: the name of an existing DB

        :type project_name: str
        :param project_name: the name of an existing project in the DB

        :type forum_name: str
        :param forum_name: the name of the forum to import. It cannot be null

        :type eclipse_forum_url: str
        :param eclipse_forum_url: the URL of the forum. It cannot be null

        :type before_date: str
        :param before_date: import data before date (YYYY-mm-dd). It can be null

        :type processes: int
        :param processes: number of processes to import the data. If null, the default number of processes is used (2)
        """
        forum2db = EclipseForum2DbMain(
            db_name, project_name, Gitana.ECLIPSE_FORUM_TYPE, forum_name,
            eclipse_forum_url, before_date, processes, self._config, self._log_path)
        forum2db.extract()

    def update_eclipse_forum_data(self, db_name, project_name, forum_name, eclipse_forum_url, processes=2):
        """
        updates the Eclipse forum data stored in the DB

        :type db_name: str
        :param db_name: the name of an existing DB

        :type project_name: str
        :param project_name: the name of an existing project in the DB

        :type forum_name: str
        :param forum_name: the name of an existing forum in the DB to update

        :type eclipse_forum_url: str
        :param eclipse_forum_url: the URL of the forum. It cannot be null

        :type processes: int
        :param processes: number of processes to import the data. If null, the default number of processes is used (2)
        """
        forum2db = EclipseForum2DbUpdate(
            db_name, project_name, forum_name, eclipse_forum_url, processes,
            self._config, self._log_path)
        forum2db.update()

    def import_stackoverflow_data(self, db_name, project_name, forum_name, search_query, tokens, before_date=None):
        """
        imports Stackoverflow data to the DB

        :type db_name: str
        :param db_name: the name of an existing DB

        :type project_name: str
        :param project_name: the name of an existing project in the DB

        :type forum_name: str
        :param forum_name: the name of the forum to import. It cannot be null

        :type search_query: str
        :param search_query: retrieves Stackoverflow questions labeled with a given string. It cannot be null

        :type tokens: list str
        :param tokens: list of Stackoverflow tokens. It cannot be null

        :type before_date: str
        :param before_date: import data before date (YYYY-mm-dd). It can be null
        """
        stackoverflow2db = StackOverflow2DbMain(
            db_name, project_name, Gitana.STACKOVERFLOW_TYPE, forum_name,
            search_query, before_date, tokens, self._config, self._log_path)
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
        :param tokens: list of Stackoverflow tokens. It cannot be null
        """
        stackoverflow2db = StackOverflow2DbUpdate(
            db_name, project_name, forum_name, tokens,
            self._config, self._log_path)
        stackoverflow2db.update()

    def import_slack_data(self, db_name, project_name, instant_messaging_name, tokens, before_date=None, channels=None):
        """
        imports Slack data to the DB

        :type db_name: str
        :param db_name: the name of an existing DB

        :type project_name: str
        :param project_name: the name of an existing project in the DB

        :type instant_messaging_name: str
        :param instant_messaging_name: the name of the instant messaging to import. It cannot be null

        :type tokens: list str
        :param tokens: list of Slack tokens. It cannot be null

        :type before_date: str
        :param before_date: import data before date (YYYY-mm-dd). It can be null

        :type channels: list str
        :param channels: list of channels to import. It can be null or ["channel-name-1", .., "channel-name-n"]
        """
        slack2db = Slack2DbMain(
            db_name, project_name,
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
        :param tokens: list of Slack tokens. It cannot be null
        """
        slack2db = Slack2DbUpdate(
            db_name, project_name, instant_messaging_name, tokens,
            self._config, self._log_path)
        slack2db.update()

    def import_github_issue_data(self, db_name, project_name, repo_name, issue_tracker_name, github_repo_full_name, tokens, before_date=None):
        """
        imports GitHub issue data to the DB

        :type db_name: str
        :param db_name: the name of an existing DB

        :type project_name: str
        :param project_name: the name of an existing project in the DB

        :type repo_name: str
        :param repo_name: the name of an existing repository in the DB

        :type issue_tracker_name: str
        :param issue_tracker_name: the name of the issue tracker to import. It cannot be null

        :type github_repo_full_name: str
        :param github_repo_full_name: full name of the GitHub repository. It cannot be null

        :type tokens: list str
        :param tokens: list of GitHub tokens. It cannot be null

        :type before_date: str
        :param before_date: import data before date (YYYY-mm-dd). It can be null
        """
        github2db = GitHubIssue2DbMain(
            db_name, project_name, repo_name, Gitana.GITHUB_TYPE, issue_tracker_name,
            github_repo_full_name, before_date, tokens, self._config, self._log_path)
        github2db.extract()

    def update_github_issue_data(self, db_name, project_name, repo_name, issue_tracker_name, github_repo_full_name, tokens):
        """
        updates GitHub issue data stored in the DB

        :type db_name: str
        :param db_name: the name of an existing DB

        :type project_name: str
        :param project_name: the name of an existing project in the DB

        :type repo_name: str
        :param repo_name: the name of an existing repository in the DB

        :type issue_tracker_name: str
        :param issue_tracker_name: the name of an existing issue tracker to update

        :type github_repo_full_name: str
        :param github_repo_full_name: full name of the GitHub repository. It cannot be null

        :type tokens: list str
        :param tokens: list of GitHub tokens. It cannot be null
        """
        github2db = GitHubIssue2DbUpdate(
            db_name, project_name, repo_name, issue_tracker_name, github_repo_full_name, tokens,
            self._config, self._log_path)
        github2db.update()

    def export_graph(self, db_name, settings_path, output_path):
        """
        exports the data stored in the Gitana DB to a graph (gexf format)

        :type db_name: str
        :param db_name: the name of an existing DB

        :type settings_path: str
        :param settings_path: the path of the JSON that drives the export process

        :type output_path: str
        :param output_path: the path where to export the graph
        """
        exporter = GraphExporter(self._config, db_name, self._log_path)
        exporter.export(output_path, settings_path)

    def export_activity_report(self, db_name, settings_path, output_path):
        """
        exports the data stored in the Gitana DB to an HTML report

        :type db_name: str
        :param db_name: the name of an existing DB

        :type settings_path: str
        :param settings_path: the path of the JSON that drives the export process

        :type output_path: str
        :param output_path: the path where to export the report
        """
        exporter = ActivityReportExporter(self._config, db_name, self._log_path)
        exporter.export(output_path, settings_path)
