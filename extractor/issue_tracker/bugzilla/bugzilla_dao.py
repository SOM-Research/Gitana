#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'valerio cosentino'

from util.db_util import DbUtil


class BugzillaDao():

    def __init__(self, config, logger):
        self.config = config
        self.logger = logger
        self.db_util = DbUtil()
        try:
            self.cnx = self.db_util.get_connection(self.config)
        except:
            self.logger.error("BugzillaDao failed", exc_info=True)

    def select_issue_tracker_id(self, repo_id, issue_tracker_name):
        return self.db_util.select_issue_tracker_id(self.cnx, issue_tracker_name, self.logger)

    def insert_issue_comment(self, own_id, position, type, issue_id, body, votes, author_id, created_at):
        cursor = self.cnx.cursor()
        query = "INSERT IGNORE INTO message " \
                "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
        arguments = [None, own_id, position, type, issue_id, 0, 0, body, votes, author_id, created_at]
        cursor.execute(query, arguments)
        self.cnx.commit()
        cursor.close()

    def select_event_type(self, name):
        cursor = self.cnx.cursor()
        query = "SELECT id FROM issue_event_type WHERE name = %s"
        arguments = [name]
        cursor.execute(query, arguments)
        row = cursor.fetchone()
        found = None
        if row:
            found = row[0]
        cursor.close()

        return found

    def insert_issue_event(self, issue_id, event_type_id, detail, creator_id, created_at, target_user_id):
        cursor = self.cnx.cursor()
        query = "INSERT IGNORE INTO issue_event " \
                "VALUES (%s, %s, %s, %s, %s, %s, %s)"
        arguments = [None, issue_id, event_type_id, detail, creator_id, created_at, target_user_id]
        cursor.execute(query, arguments)
        self.cnx.commit()
        cursor.close()

    def insert_issue_commit_dependency(self, issue_id, commit_id):
        cursor = self.cnx.cursor()
        query = "INSERT IGNORE INTO issue_commit_dependency " \
                "VALUES (%s, %s)"
        arguments = [issue_id, commit_id]
        cursor.execute(query, arguments)
        self.cnx.commit()
        cursor.close()

    def insert_event_type(self, name):
        cursor = self.cnx.cursor()
        query = "INSERT IGNORE INTO issue_event_type " \
                "VALUES (%s, %s)"
        arguments = [None, name]
        cursor.execute(query, arguments)
        self.cnx.commit()
        cursor.close()

    def insert_issue_tracker(self, repo_id, issue_tracker_name, type):
        return self.db_util.insert_issue_tracker(self.cnx, repo_id, issue_tracker_name, type, self.logger)

    def get_already_imported_issue_ids(self, issue_tracker_id, repo_id):
        issue_ids = []
        cursor = self.cnx.cursor()
        query = "SELECT i.id FROM issue i " \
                "JOIN issue_tracker it ON i.issue_tracker_id = it.id " \
                "WHERE issue_tracker_id = %s AND repo_id = %s " \
                "ORDER BY i.id ASC;"
        arguments = [issue_tracker_id, repo_id]
        cursor.execute(query, arguments)
        row = cursor.fetchone()

        while row:
            own_id = row[0]
            issue_ids.append(own_id)
            row = cursor.fetchone()

        cursor.close()

        return issue_ids

    def get_message_type_id(self, message_type):
        return self.db_util.get_message_type_id(self.cnx, message_type)

    def insert_issue_dependency(self, issue_source_id, issue_target_id, type):
        cursor = self.cnx.cursor()
        query = "INSERT IGNORE INTO issue_dependency " \
                "VALUES (%s, %s, %s)"
        arguments = [issue_source_id, issue_target_id, type]
        cursor.execute(query, arguments)
        self.cnx.commit()
        cursor.close()

    def select_project_id(self, project_name):
        return self.db_util.select_project_id(self.cnx, project_name, self.logger)

    def select_issue_own_id(self, issue_id):
        found = None
        cursor = self.cnx.cursor()
        query = "SELECT i.own_id " \
                "FROM issue i JOIN issue_tracker it ON i.issue_tracker_id = it.id " \
                "WHERE i.id = %s AND issue_tracker_id = %s AND repo_id = %s"
        arguments = [issue_id, self.issue_tracker_id, self.repo_id]
        cursor.execute(query, arguments)

        row = cursor.fetchone()
        cursor.close()

        if row:
            found = row[0]

        return found

    def get_issue_dependency_type_id(self, name):
        return self.db_util.get_issue_dependency_type_id(self.cnx, name)

    def select_commit(self, sha, repo_id):
        found = None
        cursor = self.cnx.cursor()
        query = "SELECT id " \
                "FROM commit " \
                "WHERE sha = %s AND repo_id = %s"
        arguments = [sha, repo_id]
        cursor.execute(query, arguments)
        row = cursor.fetchone()
        cursor.close()

        if row:
            found = row[0]

        return found

    def select_issue_id(self, issue_own_id, issue_tracker_id, repo_id):
        found = None
        cursor = self.cnx.cursor()
        query = "SELECT i.id FROM issue i " \
                "JOIN issue_tracker it ON i.issue_tracker_id = it.id " \
                "WHERE own_id = %s AND issue_tracker_id = %s AND repo_id = %s"
        arguments = [issue_own_id, issue_tracker_id, repo_id]
        cursor.execute(query, arguments)

        row = cursor.fetchone()
        cursor.close()

        if row:
            found = row[0]

        return found

    def update_issue(self, issue_id, issue_tracker_id, summary, component, version, hardware, priority, severity, reference_id, last_change_at):
        cursor = self.cnx.cursor()
        query = "UPDATE issue SET last_change_at = %s, summary = %s, component = %s, version = %s, hardware = %s, priority = %s, severity = %s, reference_id = %s WHERE own_id = %s AND issue_tracker_id = %s"
        arguments = [last_change_at, summary, component, version, hardware, priority, severity, reference_id, issue_id, issue_tracker_id]
        cursor.execute(query, arguments)
        self.cnx.commit()
        cursor.close()

    def insert_issue(self, issue_own_id, issue_tracker_id, summary, component, version, hardware, priority, severity, reference_id, user_id, created_at, last_change_at):
        cursor = self.cnx.cursor()
        query = "INSERT IGNORE INTO issue " \
                "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
        arguments = [None, issue_own_id, issue_tracker_id, summary, component, version, hardware, priority, severity, reference_id, user_id, created_at, last_change_at]
        cursor.execute(query, arguments)
        self.cnx.commit()
        cursor.close()

    def insert_label(self, name):
        cursor = self.cnx.cursor()
        query = "INSERT IGNORE INTO label " \
                "VALUES (%s, %s)"
        arguments = [None, name]
        cursor.execute(query, arguments)
        self.cnx.commit()
        cursor.close()

    def select_label_id(self, name):
        cursor = self.cnx.cursor()
        query = "SELECT id FROM label WHERE name = %s"
        arguments = [name]
        cursor.execute(query, arguments)
        row = cursor.fetchone()
        found = None
        if row:
            found = row[0]
        cursor.close()

        return found

    def select_issue_comment_id(self, own_id, issue_id, created_at):
        cursor = self.cnx.cursor()
        query = "SELECT id FROM message WHERE own_id = %s AND issue_id = %s AND created_at = %s"
        arguments = [own_id, issue_id, created_at]
        cursor.execute(query, arguments)
        row = cursor.fetchone()
        found = None
        if row:
            found = row[0]
        cursor.close()

        return found

    def get_user_id(self, user_name, user_email):
        user_id = self.db_util.select_user_id_by_email(self.cnx, user_email, self.logger)
        if not user_id:
            self.db_util.insert_user(self.cnx, user_name, user_email, self.logger)
            user_id = self.db_util.select_user_id_by_email(self.cnx, user_email, self.logger)

        return user_id

    def insert_subscriber(self, issue_id, subscriber_id):
        cursor = self.cnx.cursor()
        query = "INSERT IGNORE INTO issue_subscriber " \
                "VALUES (%s, %s)"
        arguments = [issue_id, subscriber_id]
        cursor.execute(query, arguments)
        self.cnx.commit()
        cursor.close()

    def insert_assignee(self, issue_id, assignee_id):
        cursor = self.cnx.cursor()
        query = "INSERT IGNORE INTO issue_assignee " \
                "VALUES (%s, %s)"
        arguments = [issue_id, assignee_id]
        cursor.execute(query, arguments)
        self.cnx.commit()
        cursor.close()

    def insert_attachment(self, attachment_id, issue_comment_id, name, extension, size, url):
        cursor = self.cnx.cursor()
        query = "INSERT IGNORE INTO attachment " \
                "VALUES (%s, %s, %s, %s, %s, %s, %s)"
        arguments = [None, attachment_id, issue_comment_id, name, extension, size, url]
        cursor.execute(query, arguments)
        self.cnx.commit()
        cursor.close()

    def assign_label_to_issue(self, issue_id, label_id):
        cursor = self.cnx.cursor()
        query = "INSERT IGNORE INTO issue_labelled " \
                "VALUES (%s, %s)"
        arguments = [issue_id, label_id]
        cursor.execute(query, arguments)
        self.cnx.commit()
        cursor.close()

    def find_reference_id(self, version, issue_id, repo_id):
        found = None
        if version:
            try:
                cursor = self.cnx.cursor()
                query = "SELECT id FROM reference WHERE name = %s AND repo_id = %s"
                arguments = [version, repo_id]
                cursor.execute(query, arguments)
                row = cursor.fetchone()
                if row:
                    found = row[0]
                else:
                    #sometimes the version is followed by extra information such as alpha, beta, RC, M.
                    query = "SELECT id FROM reference WHERE name LIKE '" + version + "%' AND repo_id = " + str(repo_id)
                    cursor.execute(query)
                    row = cursor.fetchone()

                    if row:
                        found = row[0]

                cursor.close()
            except Exception, e:
                self.logger.warning("version (" + version + ") not inserted for issue id: " + str(issue_id), exc_info=True)

        return found

    def select_last_change_issue(self, issue_id, issue_tracker_id, repo_id):
        found = None

        cursor = self.cnx.cursor()
        query = "SELECT i.last_change_at " \
                "FROM issue i JOIN issue_tracker it ON i.issue_tracker_id = it.id " \
                "WHERE own_id = %s AND issue_tracker_id = %s AND repo_id = %s"
        arguments = [issue_id, issue_tracker_id, repo_id]
        cursor.execute(query, arguments)

        row = cursor.fetchone()
        cursor.close()

        if row:
            found = row[0]

        return found

    def select_repo_id(self, project_id, repo_name):
        return self.db_util.select_repo_id(self.cnx, repo_name, self.logger)

    def get_cursor(self):
        return self.cnx.cursor()

    def close_cursor(self, cursor):
        return cursor.close()

    def fetchone(self, cursor):
        return cursor.fetchone()

    def execute(self, cursor, query, arguments):
        cursor.execute(query, arguments)

    def close_connection(self):
        self.db_util.close_connection(self.cnx)

    def restart_connection(self):
        self.cnx = self.db_util.restart_connection(self.config, self.logger)