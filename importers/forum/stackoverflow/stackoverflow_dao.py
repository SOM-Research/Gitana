#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'valerio cosentino'

from util.db_util import DbUtil


class StackOverflowDao():
    """
    This class handles the persistence and retrieval of Stackoverflow data
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
            self._logger.error("StackOverflowDao failed")
            raise

    def close_connection(self):
        """
        closes DB connection
        """
        self._db_util.close_connection(self._cnx)

    def get_message_type_id(self, message_type):
        """
        gets the id associated to a given type of message

        :type message_type: str
        :param message_type: message type
        """
        return self._db_util.get_message_type_id(self._cnx, message_type)

    def get_user_id(self, user_name):
        """
        gets the id associated to a user name

        :type user_name: str
        :param user_name: user name
        """

        if not user_name:
            user_name = "uknonwn_user"

        user_id = self._db_util.select_user_id_by_name(self._cnx, user_name, self._logger)
        if not user_id:
            self._db_util.insert_user(self._cnx, user_name, None, self._logger)
            user_id = self._db_util.select_user_id_by_name(self._cnx, user_name, self._logger)

        return user_id

    def select_project_id(self, project_name):
        """
        gets project id by its name

        :type project_name: str
        :param project_name: project name
        """
        return self._db_util.select_project_id(self._cnx, project_name, self._logger)

    def select_forum_id(self, forum_name, project_id):
        """
        gets DB forum id by its name

        :type forum_name: str
        :param forum_name: forum name

        :type project_id: int
        :param project_id: project id
        """
        found = None
        cursor = self._cnx.cursor()
        query = "SELECT id " \
                "FROM forum " \
                "WHERE name = %s AND project_id = %s"
        arguments = [forum_name, project_id]
        cursor.execute(query, arguments)

        row = cursor.fetchone()

        if row:
            found = row[0]
        else:
            self._logger.warning("no forum with this name " + str(forum_name))

        cursor.close()
        return found

    def insert_forum(self, project_id, forum_name, type):
        """
        inserts forum to DB

        :type project_id: int
        :param project_id: project id

        :type forum_name: str
        :param forum_name: forum name

        :type type: str
        :param type: forum type (Eclipse forum, Bugzilla)
        """
        cursor = self._cnx.cursor()
        query = "INSERT IGNORE INTO forum " \
                "VALUES (%s, %s, %s, %s)"
        arguments = [None, project_id, forum_name, type]
        cursor.execute(query, arguments)
        self._cnx.commit()

        query = "SELECT id " \
                "FROM forum " \
                "WHERE name = %s"
        arguments = [forum_name]
        cursor.execute(query, arguments)

        row = cursor.fetchone()

        found = None
        if row:
            found = row[0]
        else:
            self._logger.warning("no forum with name " + str(forum_name))

        cursor.close()
        return found

    def update_topic_created_at(self, topic_id, created_at, forum_id):
        """
        updates created_at column of a topic

        :type forum_id: int
        :param forum_id: DB topic id

        :type created_at: str
        :param created_at: new created_at value

        :type forum_id: int
        :param forum_id: DB forum id
        """
        cursor = self._cnx.cursor()
        query = "UPDATE topic SET created_at = %s WHERE id = %s AND forum_id = %s"
        arguments = [created_at, topic_id, forum_id]
        cursor.execute(query, arguments)
        self._cnx.commit()
        cursor.close()

    def update_message(self, own_id, topic_id, body, votes):
        """
        updates message data

        :type own_id: int
        :param own_id: data source message id

        :type topic_id: int
        :param topic_id: DB topic id

        :type body: str
        :param body: new message body

        :type votes: int
        :param votes: new message votes
        """
        try:
            cursor = self._cnx.cursor()
            query = "UPDATE message " \
                    "SET body = %s, votes = %s WHERE own_id = %s AND topic_id = %s"
            arguments = [body, votes, own_id, topic_id]
            cursor.execute(query, arguments)
            self._cnx.commit()
        except:
            self._logger.warning("message " + str(own_id) + ") for topic id: " + str(topic_id) + " not inserted",
                                 exc_info=True)

    def insert_message(self, own_id, pos, type, topic_id, body, votes, author_id, created_at):
        """
        inserts message to DB

        :type own_id: int
        :param own_id: data source message id

        :type pos: int
        :param pos: position of the message in the topic

        :type type: str
        :param type: type of the message (question, reply)

        :type topic_id: int
        :param topic_id: DB topic id

        :type body: str
        :param body: message body

        :type votes: int
        :param votes: number of votes received

        :type author_id: int
        :param author_id: id of the author

        :type created_at: str
        :param created_at: creation time of the message
        """
        try:
            cursor = self._cnx.cursor()
            query = "INSERT IGNORE INTO message " \
                    "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
            arguments = [None, own_id, pos, type, 0, topic_id, 0, body, votes, author_id, created_at]
            cursor.execute(query, arguments)
            self._cnx.commit()
        except:
            self._logger.warning("message " + str(own_id) + ") for topic id: " + str(topic_id) + " not inserted",
                                 exc_info=True)

    def insert_topic(self, own_id, forum_id, name, votes, views, created_at, last_change_at):
        """
        inserts topic to DB

        :type own_id: int
        :param own_id: data source topic id

        :type forum_id: int
        :param forum_id: forum id

        :type name: str
        :param name: title of the topic

        :type views: int
        :param views: number of views of the topic

        :type created_at: str
        :param created_at: creation date

        :type last_change_at: str
        :param last_change_at: last change date
        """
        try:
            cursor = self._cnx.cursor()
            query = "INSERT IGNORE INTO topic " \
                    "VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
            arguments = [None, own_id, forum_id, name, votes, views, created_at, last_change_at]
            cursor.execute(query, arguments)
            self._cnx.commit()

            query = "SELECT id FROM topic WHERE own_id = %s AND forum_id = %s"
            arguments = [own_id, forum_id]
            cursor.execute(query, arguments)

            found = None
            row = cursor.fetchone()
            if row:
                found = row[0]

            cursor.close()
            return found
        except Exception:
            self._logger.warning("topic " + str(own_id) + ") for forum id: " + str(forum_id) + " not inserted",
                                 exc_info=True)

    def insert_message_dependency(self, source_message_id, target_message_id):
        """
        inserts dependency between two messages

        :type source_message_id: int
        :param source_message_id: DB source message id

        :type target_message_id: int
        :param target_message_id: DB target message id
        """
        cursor = self._cnx.cursor()
        query = "INSERT IGNORE INTO message_dependency " \
                "VALUES (%s, %s)"
        arguments = [source_message_id, target_message_id]
        cursor.execute(query, arguments)
        self._cnx.commit()
        cursor.close()

    def get_topic_own_id(self, forum_id, topic_id):
        """
        gets data source topic id

        :type forum_id: int
        :param forum_id: DB forum id

        :type topic_id: int
        :param topic_id: DB topic id
        """
        found = None
        cursor = self._cnx.cursor()
        query = "SELECT own_id FROM topic WHERE forum_id = %s AND id = %s"
        arguments = [forum_id, topic_id]
        cursor.execute(query, arguments)

        row = cursor.fetchone()
        if row:
            found = row[0]

        cursor.close()
        return found

    def assign_label_to_topic(self, topic_id, label_id):
        """
        links label to topic

        :type topic_id: int
        :param topic_id: db topic id

        :type label_id: int
        :param label_id: label id
        """
        cursor = self._cnx.cursor()
        query = "INSERT IGNORE INTO topic_labelled " \
                "VALUES (%s, %s)"
        arguments = [topic_id, label_id]
        cursor.execute(query, arguments)
        self._cnx.commit()
        cursor.close()

    def select_label_id(self, name):
        """
        selects the label id by its name

        :type name: str
        :param name: the name of the label
        """
        return self._db_util.select_label_id(self._cnx, name, self._logger)

    def insert_label(self, name):
        """
        inserts a label

        :type name: str
        :param name: the name of the label
        """
        self._db_util.insert_label(self._cnx, name, self._logger)

    def get_topic_own_ids(self, forum_id):
        """
        gets list of data source topic ids

        :type forum_id: int
        :param forum_id: DB forum id
        """
        topic_own_ids = []

        cursor = self._cnx.cursor()
        query = "SELECT own_id FROM topic WHERE forum_id = %s"
        arguments = [forum_id]
        cursor.execute(query, arguments)

        row = cursor.fetchone()

        while row:
            topic_own_id = row[0]
            topic_own_ids.append(topic_own_id)
            row = cursor.fetchone()

        cursor.close()
        return topic_own_ids

    def get_topic_ids(self, forum_id):
        """
        gets list of topic ids in a given forum

        :type forum_id: int
        :param forum_id: DB forum id
        """
        topic_ids = []

        cursor = self._cnx.cursor()
        query = "SELECT id FROM topic WHERE forum_id = %s"
        arguments = [forum_id]
        cursor.execute(query, arguments)

        row = cursor.fetchone()

        while row:
            topic_id = row[0]
            topic_ids.append(topic_id)
            row = cursor.fetchone()

        cursor.close()
        return topic_ids

    def get_topic_last_change_at(self, own_id, forum_id):
        """
        gets last change date of a topic

        :type own_id: int
        :param own_id: data source topic id

        :type forum_id: int
        :param forum_id: DB forum id
        """
        cursor = self._cnx.cursor()

        query = "SELECT last_change_at FROM topic WHERE own_id = %s AND forum_id = %s"
        arguments = [own_id, forum_id]
        cursor.execute(query, arguments)

        found = None
        row = cursor.fetchone()
        if row:
            found = row[0]

        cursor.close()
        return found

    def insert_attachment(self, own_id, message_id, name, url):
        """
        insert attachment of a message

        :type own_id: int
        :param own_id: data source message id

        :type message_id: int
        :param message_id: DB message id

        :type name: str
        :param name: attachment name

        :type url: str
        :param url: attachment url
        """
        cursor = self._cnx.cursor()
        query = "INSERT IGNORE INTO attachment " \
                "VALUES (%s, %s, %s, %s, %s, %s, %s)"
        arguments = [None, own_id, message_id, name, None, None, url]
        cursor.execute(query, arguments)
        self._cnx.commit()
        cursor.close()

    def select_message_id(self, own_id, topic_id):
        """
        gets message id

        :type own_id: int
        :param own_id: data source message id

        :type topic_id: int
        :param topic_id: DB topic id
        """
        cursor = self._cnx.cursor()

        query = "SELECT id FROM message WHERE own_id = %s AND topic_id = %s"
        arguments = [own_id, topic_id]
        cursor.execute(query, arguments)

        found = None
        row = cursor.fetchone()
        if row:
            found = row[0]

        cursor.close()
        return found
