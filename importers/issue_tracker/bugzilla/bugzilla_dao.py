#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'valerio cosentino'

from util.db_util import DbUtil


class BugzillaDao():
    """
    This class handles the persistence and retrieval of Bugzilla issue tracker data
    """

    def __init__(self, config, logger):
        """
        :type config: dict
        :param config: the DB configuration file

        :type logger: Object
        :param logger: logger
        """
        try:
            self._config = config
            self._logger = logger
            self._db_util = DbUtil()
            self._cnx = self._db_util.get_connection(self._config)
        except:
            self._logger.error("BugzillaDao init failed")
            raise

    def select_issue_tracker_id(self, repo_id, issue_tracker_name):
        """
        gets DB issue tracker id by its name

        :type repo_id: int
        :param repo_id: id of the repository associated to the issue tracker

        :type issue_tracker_name: str
        :param issue_tracker_name: issue tracker name
        """
        return self._db_util.select_issue_tracker_id(self._cnx, issue_tracker_name, self._logger)

    def insert_issue_comment(self, own_id, position, type, issue_id, body, votes, author_id, created_at):
        """
        inserts issue comment

        :type own_id: id
        :param own_id: data source message id

        :type position: int
        :param position: position of the comment

        :type type: str
        :param type: type of the message

        :type issue_id: id
        :param issue_id: DB issue id

        :type body: str
        :param body: body of the comment

        :type votes: int
        :param votes: votes of the comment

        :type author_id: int
        :param author_id: id of the author

        :type created_at: str
        :param created_at: creation date of the comment
        """
        cursor = self._cnx.cursor()
        query = "INSERT IGNORE INTO message " \
                "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
        arguments = [None, own_id, position, type, issue_id, 0, 0, body, votes, author_id, created_at]
        cursor.execute(query, arguments)
        self._cnx.commit()
        cursor.close()

    def select_event_type(self, name):
        """
        selects event type id by its name

        :type name: str
        :param name: name of the event
        """
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
        """
        inserts issue event

        :type issue_id: int
        :param issue_id: DB issue id

        :type event_type_id: int
        :param event_type_id: event type id

        :type detail: str
        :param detail: detail of the event

        :type creator_id: int
        :param creator_id: id of the creator

        :type created_at: str
        :param created_at: creation date of the event

        :type target_user_id: int
        :param target_user_id: target user id
        """
        cursor = self._cnx.cursor()
        query = "INSERT IGNORE INTO issue_event " \
                "VALUES (%s, %s, %s, %s, %s, %s, %s)"
        arguments = [None, issue_id, event_type_id, detail, creator_id, created_at, target_user_id]
        cursor.execute(query, arguments)
        self._cnx.commit()
        cursor.close()

    def insert_issue_commit_dependency(self, issue_id, commit_id):
        """
        inserts dependency between commit and issue

        :type issue_id: int
        :param issue_id: DB issue id

        :type commit_id: int
        :param commit_id: DB commit id
        """
        cursor = self._cnx.cursor()
        query = "INSERT IGNORE INTO issue_commit_dependency " \
                "VALUES (%s, %s)"
        arguments = [issue_id, commit_id]
        cursor.execute(query, arguments)
        self._cnx.commit()
        cursor.close()

    def insert_event_type(self, name):
        """
        inserts event type

        :type name: str
        :param name: event type name
        """
        cursor = self._cnx.cursor()
        query = "INSERT IGNORE INTO issue_event_type " \
                "VALUES (%s, %s)"
        arguments = [None, name]
        cursor.execute(query, arguments)
        self._cnx.commit()
        cursor.close()

    def insert_issue_tracker(self, repo_id, issue_tracker_name, type):
        """
        inserts issue tracker

        :type repo_id: int
        :param repo_id: DB repo id

        :type issue_tracker_name: str
        :param issue_tracker_name: issue tracker name

        :type type: str
        :param type: issue tracker type (github, bugzilla, etc.)
        """
        return self._db_util.insert_issue_tracker(self._cnx, repo_id, issue_tracker_name, type, self._logger)

    def get_already_imported_issue_ids(self, issue_tracker_id, repo_id):
        """
        gets issues already stored in DB

        :type issue_tracker_id: int
        :param issue_tracker_id: DB issue tracker id

        :type repo_id: int
        :param repo_id: DB repo id
        """
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
        """
        gets message type id

        :type message_type: str
        :param message_type: message type
        """
        return self._db_util.get_message_type_id(self._cnx, message_type)

    def insert_issue_dependency(self, issue_source_id, issue_target_id, type):
        """
        inserts dependency between issues

        :type issue_source_id: int
        :param issue_source_id: issue source id

        :type issue_target_id: int
        :param issue_target_id: issue target id

        :type type: str
        :param type: type of dependency
        """
        cursor = self._cnx.cursor()
        query = "INSERT IGNORE INTO issue_dependency " \
                "VALUES (%s, %s, %s)"
        arguments = [issue_source_id, issue_target_id, type]
        cursor.execute(query, arguments)
        self._cnx.commit()
        cursor.close()

    def select_project_id(self, project_name):
        """
        selects project id by its name

        :type project_name: str
        :param project_name: name of a project
        """
        return self._db_util.select_project_id(self._cnx, project_name, self._logger)

    def select_issue_own_id(self, issue_id, issue_tracker_id, repo_id):
        """
        selects data source issue id

        :type issue_id: int
        :param issue_id: DB issue id

        :type issue_tracker_id: int
        :param issue_tracker_id: issue tracker id

        :type repo_id: int
        :param repo_id: repository id
        """
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
        """
        get id of the issue dependency type

        :type name: str
        :param name: name of the dependency type
        """
        return self._db_util.get_issue_dependency_type_id(self._cnx, name)

    def select_commit(self, sha, repo_id):
        """
        gets commit by its SHA

        :type sha: str
        :param sha: SHA of the commit

        :type repo_id: int
        :param repo_id: repository id
        """
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
        """
        gets issue id

        :type issue_own_id: int
        :param issue_own_id: data source issue id

        :type issue_tracker_id: int
        :param issue_tracker_id: issue tracker id

        :type repo_id: int
        :param repo_id: repository id
        """
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

    def update_issue(self, issue_id, issue_tracker_id, summary, component, version, hardware, priority, severity,
                     reference_id, last_change_at):
        """
        updates an issue

        :type issue_id: int
        :param issue_id: DB issue id

        :type issue_tracker_id: int
        :param issue_tracker_id: issue tracker id

        :type summary: str
        :param summary: new issue description

        :type component: str
        :param component: component where the issue was found

        :type version: str
        :param version: version where the issue was found

        :type hardware: str
        :param hardware: hardware where the issue was found

        :type priority: str
        :param priority: priority of the issue

        :type severity: str
        :param severity: severity of the issue

        :type reference_id: int
        :param reference_id: id of the Git reference where the issue was found

        :type last_change_at: str
        :param last_change_at: last change date of the issue
        """
        cursor = self._cnx.cursor()
        query = "UPDATE issue SET " \
                "last_change_at = %s, summary = %s, component = %s, version = %s, hardware = %s, " \
                "priority = %s, severity = %s, reference_id = %s " \
                "WHERE own_id = %s AND issue_tracker_id = %s"
        arguments = [last_change_at, summary, component, version, hardware, priority,
                     severity, reference_id, issue_id, issue_tracker_id]
        cursor.execute(query, arguments)
        self._cnx.commit()
        cursor.close()

    def insert_issue(self, issue_own_id, issue_tracker_id, summary, component, version, hardware, priority,
                     severity, reference_id, user_id, created_at, last_change_at):
        """
        inserts an issue

        :type issue_own_id: int
        :param issue_own_id: data source issue id

        :type issue_tracker_id: int
        :param issue_tracker_id: issue tracker id

        :type summary: str
        :param summary: new issue description

        :type component: str
        :param component: component where the issue was found

        :type version: str
        :param version: version where the issue was found

        :type hardware: str
        :param hardware: hardware where the issue was found

        :type priority: str
        :param priority: priority of the issue

        :type severity: str
        :param severity: severity of the issue

        :type reference_id: int
        :param reference_id: id of the Git reference where the issue was found

        :type user_id: int
        :param user_id: issue creator id

        :type created_at: str
        :param created_at: creation date of the issue

        :type last_change_at: str
        :param last_change_at: last change date of the issue
        """
        cursor = self._cnx.cursor()
        query = "INSERT IGNORE INTO issue " \
                "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
        arguments = [None, issue_own_id, issue_tracker_id, summary, component, version, hardware, priority,
                     severity, reference_id, user_id, created_at, last_change_at]
        cursor.execute(query, arguments)
        self._cnx.commit()
        cursor.close()

    def insert_label(self, name):
        """
        inserts a label

        :type name: str
        :param name: the name of the label
        """
        self._db_util.insert_label(self._cnx, name, self._logger)

    def select_label_id(self, name):
        """
        selects the label id by its name

        :type name: str
        :param name: the name of the label
        """
        return self._db_util.select_label_id(self._cnx, name, self._logger)

    def select_issue_comment_id(self, own_id, issue_id, created_at):
        """
        selects the id of an issue comment

        :type own_id: int
        :param own_id: data source comment id

        :type issue_id: int
        :param issue_id: DB issue id

        :type created_at: str
        :param created_at: creation date of the issue
        """
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
        """
        selects the id of a user

        :type user_name: str
        :param user_name: name of the user

        :type user_email: str
        :param user_email: email of the user
        """

        if not user_email and not user_name:
            user_name = "uknonwn_user"
            user_email = "uknonwn_user"

        user_id = self._db_util.select_user_id_by_email(self._cnx, user_email, self._logger)
        if not user_id:
            self._db_util.insert_user(self._cnx, user_name, user_email, self._logger)
            user_id = self._db_util.select_user_id_by_email(self._cnx, user_email, self._logger)

        return user_id

    def insert_subscriber(self, issue_id, subscriber_id):
        """
        inserts issue subscriber

        :type issue_id: int
        :param issue_id: db issue id

        :type subscriber_id: int
        :param subscriber_id: subscriber id
        """
        cursor = self._cnx.cursor()
        query = "INSERT IGNORE INTO issue_subscriber " \
                "VALUES (%s, %s)"
        arguments = [issue_id, subscriber_id]
        cursor.execute(query, arguments)
        self._cnx.commit()
        cursor.close()

    def insert_assignee(self, issue_id, assignee_id):
        """
        inserts issue assignee

        :type issue_id: int
        :param issue_id: db issue id

        :type assignee_id: int
        :param assignee_id: assignee id
        """
        cursor = self._cnx.cursor()
        query = "INSERT IGNORE INTO issue_assignee " \
                "VALUES (%s, %s)"
        arguments = [issue_id, assignee_id]
        cursor.execute(query, arguments)
        self._cnx.commit()
        cursor.close()

    def insert_attachment(self, attachment_id, issue_comment_id, name, extension, size, url):
        """
        inserts attachment

        :type attachment_id: int
        :param attachment_id: db attachment id

        :type issue_comment_id: int
        :param issue_comment_id: issue comment id

        :type name: str
        :param name: name of the attachment

        :type extension: str
        :param extension: extension of the attachment

        :type size: str
        :param size: size of the attachment

        :type url: str
        :param url: url of the attachment
        """
        cursor = self._cnx.cursor()
        query = "INSERT IGNORE INTO attachment " \
                "VALUES (%s, %s, %s, %s, %s, %s, %s)"
        arguments = [None, attachment_id, issue_comment_id, name, extension, size, url]
        cursor.execute(query, arguments)
        self._cnx.commit()
        cursor.close()

    def assign_label_to_issue(self, issue_id, label_id):
        """
        links label to issue

        :type issue_id: int
        :param issue_id: db issue id

        :type label_id: int
        :param label_id: label id
        """
        cursor = self._cnx.cursor()
        query = "INSERT IGNORE INTO issue_labelled " \
                "VALUES (%s, %s)"
        arguments = [issue_id, label_id]
        cursor.execute(query, arguments)
        self._cnx.commit()
        cursor.close()

    def find_reference_id(self, version, issue_id, repo_id):
        """
        retrieves reference id

        :type version: str
        :param version: name of the reference

        :type issue_id: int
        :param issue_id: db issue id

        :type repo_id: int
        :param repo_id: repository id
        """
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
                    # sometimes the version is followed by extra information such as alpha, beta, RC, M.
                    query = "SELECT id " \
                            "FROM reference " \
                            "WHERE name LIKE '" + str(version) + "%' AND repo_id = " + str(repo_id)
                    cursor.execute(query)
                    row = cursor.fetchone()

                    if row:
                        found = row[0]

                cursor.close()
            except Exception:
                self._logger.warning("version (" + str(version) + ") not inserted for issue id: " + str(issue_id),
                                     exc_info=True)

        return found

    def select_last_change_issue(self, issue_id, issue_tracker_id, repo_id):
        """
        retrieves last change date of an issue

        :type issue_id: int
        :param issue_id: db issue id

        :type issue_tracker_id: int
        :param issue_tracker_id: issue tracker id

        :type repo_id: int
        :param repo_id: repository id
        """
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
        """
        selects repository id

        :type project_id: int
        :param project_id: project id

        :type repo_name: int
        :param repo_name: repository name
        """
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
