#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'valerio cosentino'

from util.db_util import DbUtil


class BugzillaDao():

    def __init__(self, config, logger):
        try:
            self._config = config
            self._logger = logger
            self._db_util = DbUtil()
            self._cnx = self._db_util.get_connection(self._config)
        except:
            self._logger.error("BugzillaDao init failed")
            raise

    def select_issue_tracker_id(self, repo_id, issue_tracker_name):
        return self._db_util.select_issue_tracker_id(self._cnx, issue_tracker_name, self._logger)

    def insert_issue_comment(self, own_id, position, type, issue_id, body, votes, author_id, created_at):
        cursor = self._cnx.cursor()
        query = "INSERT IGNORE INTO message " \
                "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
        arguments = [None, own_id, position, type, issue_id, 0, 0, body, votes, author_id, created_at]
        cursor.execute(query, arguments)
        self._cnx.commit()
        cursor.close()

    def select_event_type(self, name):
        cursor = self._cnx.cursor()
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
        cursor = self._cnx.cursor()
        query = "INSERT IGNORE INTO issue_event " \
                "VALUES (%s, %s, %s, %s, %s, %s, %s)"
        arguments = [None, issue_id, event_type_id, detail, creator_id, created_at, target_user_id]
        cursor.execute(query, arguments)
        self._cnx.commit()
        cursor.close()

    def insert_issue_commit_dependency(self, issue_id, commit_id):
        cursor = self._cnx.cursor()
        query = "INSERT IGNORE INTO issue_commit_dependency " \
                "VALUES (%s, %s)"
        arguments = [issue_id, commit_id]
        cursor.execute(query, arguments)
        self._cnx.commit()
        cursor.close()

    def insert_event_type(self, name):
        cursor = self._cnx.cursor()
        query = "INSERT IGNORE INTO issue_event_type " \
                "VALUES (%s, %s)"
        arguments = [None, name]
        cursor.execute(query, arguments)
        self._cnx.commit()
        cursor.close()

    def insert_issue_tracker(self, repo_id, issue_tracker_name, type):
        return self._db_util.insert_issue_tracker(self._cnx, repo_id, issue_tracker_name, type, self._logger)

    def get_already_imported_issue_ids(self, issue_tracker_id, repo_id):
        issue_ids = []
        cursor = self._cnx.cursor()
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
        return self._db_util.get_message_type_id(self._cnx, message_type)

    def insert_issue_dependency(self, issue_source_id, issue_target_id, type):
        cursor = self._cnx.cursor()
        query = "INSERT IGNORE INTO issue_dependency " \
                "VALUES (%s, %s, %s)"
        arguments = [issue_source_id, issue_target_id, type]
        cursor.execute(query, arguments)
        self._cnx.commit()
        cursor.close()

    def select_project_id(self, project_name):
        return self._db_util.select_project_id(self._cnx, project_name, self._logger)

    def select_issue_own_id(self, issue_id, issue_tracker_id, repo_id):
        found = None
        cursor = self._cnx.cursor()
        query = "SELECT i.own_id " \
                "FROM issue i JOIN issue_tracker it ON i.issue_tracker_id = it.id " \
                "WHERE i.id = %s AND issue_tracker_id = %s AND repo_id = %s"
        arguments = [issue_id, issue_tracker_id, repo_id]
        cursor.execute(query, arguments)

        row = cursor.fetchone()

        if row:
            found = int(row[0])

        cursor.close()
        return found

    def get_issue_dependency_type_id(self, name):
        return self._db_util.get_issue_dependency_type_id(self._cnx, name)

    def select_commit(self, sha, repo_id):
        found = None
        cursor = self._cnx.cursor()
        query = "SELECT id " \
                "FROM commit " \
                "WHERE sha = %s AND repo_id = %s"
        arguments = [sha, repo_id]
        cursor.execute(query, arguments)
        row = cursor.fetchone()

        if row:
            found = row[0]

        cursor.close()
        return found

    def select_issue_id(self, issue_own_id, issue_tracker_id, repo_id):
        found = None
        cursor = self._cnx.cursor()
        query = "SELECT i.id FROM issue i " \
                "JOIN issue_tracker it ON i.issue_tracker_id = it.id " \
                "WHERE own_id = %s AND issue_tracker_id = %s AND repo_id = %s"
        arguments = [issue_own_id, issue_tracker_id, repo_id]
        cursor.execute(query, arguments)

        row = cursor.fetchone()

        if row:
            found = row[0]

        cursor.close()
        return found

    def update_issue(self, issue_id, issue_tracker_id, summary, component, version, hardware, priority, severity, reference_id, last_change_at):
        cursor = self._cnx.cursor()
        query = "UPDATE issue SET last_change_at = %s, summary = %s, component = %s, version = %s, hardware = %s, priority = %s, severity = %s, reference_id = %s WHERE own_id = %s AND issue_tracker_id = %s"
        arguments = [last_change_at, summary, component, version, hardware, priority, severity, reference_id, issue_id, issue_tracker_id]
        cursor.execute(query, arguments)
        self._cnx.commit()
        cursor.close()

    def insert_issue(self, issue_own_id, issue_tracker_id, summary, component, version, hardware, priority, severity, reference_id, user_id, created_at, last_change_at):
        cursor = self._cnx.cursor()
        query = "INSERT IGNORE INTO issue " \
                "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
        arguments = [None, issue_own_id, issue_tracker_id, summary, component, version, hardware, priority, severity, reference_id, user_id, created_at, last_change_at]
        cursor.execute(query, arguments)
        self._cnx.commit()
        cursor.close()

    def insert_label(self, name):
        cursor = self._cnx.cursor()
        query = "INSERT IGNORE INTO label " \
                "VALUES (%s, %s)"
        arguments = [None, name]
        cursor.execute(query, arguments)
        self._cnx.commit()
        cursor.close()

    def select_label_id(self, name):
        cursor = self._cnx.cursor()
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
        cursor = self._cnx.cursor()
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
        user_id = self._db_util.select_user_id_by_email(self._cnx, user_email, self._logger)
        if not user_id:
            self._db_util.insert_user(self._cnx, user_name, user_email, self._logger)
            user_id = self._db_util.select_user_id_by_email(self._cnx, user_email, self._logger)

        return user_id

    def insert_subscriber(self, issue_id, subscriber_id):
        cursor = self._cnx.cursor()
        query = "INSERT IGNORE INTO issue_subscriber " \
                "VALUES (%s, %s)"
        arguments = [issue_id, subscriber_id]
        cursor.execute(query, arguments)
        self._cnx.commit()
        cursor.close()

    def insert_assignee(self, issue_id, assignee_id):
        cursor = self._cnx.cursor()
        query = "INSERT IGNORE INTO issue_assignee " \
                "VALUES (%s, %s)"
        arguments = [issue_id, assignee_id]
        cursor.execute(query, arguments)
        self._cnx.commit()
        cursor.close()

    def insert_attachment(self, attachment_id, issue_comment_id, name, extension, size, url):
        cursor = self._cnx.cursor()
        query = "INSERT IGNORE INTO attachment " \
                "VALUES (%s, %s, %s, %s, %s, %s, %s)"
        arguments = [None, attachment_id, issue_comment_id, name, extension, size, url]
        cursor.execute(query, arguments)
        self._cnx.commit()
        cursor.close()

    def assign_label_to_issue(self, issue_id, label_id):
        cursor = self._cnx.cursor()
        query = "INSERT IGNORE INTO issue_labelled " \
                "VALUES (%s, %s)"
        arguments = [issue_id, label_id]
        cursor.execute(query, arguments)
        self._cnx.commit()
        cursor.close()

    def find_reference_id(self, version, issue_id, repo_id):
        found = None
        if version:
            try:
                cursor = self._cnx.cursor()
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
                self._logger.warning("version (" + version + ") not inserted for issue id: " + str(issue_id), exc_info=True)

        return found

    def select_last_change_issue(self, issue_id, issue_tracker_id, repo_id):
        found = None

        cursor = self._cnx.cursor()
        query = "SELECT i.last_change_at " \
                "FROM issue i JOIN issue_tracker it ON i.issue_tracker_id = it.id " \
                "WHERE own_id = %s AND issue_tracker_id = %s AND repo_id = %s"
        arguments = [issue_id, issue_tracker_id, repo_id]
        cursor.execute(query, arguments)

        row = cursor.fetchone()

        if row:
            found = row[0]

        cursor.close()
        return found

    def select_repo_id(self, project_id, repo_name):
        return self._db_util.select_repo_id(self._cnx, repo_name, self._logger)

    def get_cursor(self):
        return self._cnx.cursor()

    def close_cursor(self, cursor):
        return cursor.close()

    def fetchone(self, cursor):
        return cursor.fetchone()

    def execute(self, cursor, query, arguments):
        cursor.execute(query, arguments)

    def close_connection(self):
        self._db_util.close_connection(self._cnx)

    def restart_connection(self):
        self._cnx = self._db_util.restart_connection(self._config, self._logger)