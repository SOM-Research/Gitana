#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'valerio cosentino'

from util.db_util import DbUtil


class StackOverflowDao():

    def __init__(self, config, logger):
        try:
            self._config = config
            self._logger = logger
            self._db_util = DbUtil()
            self._cnx = self._db_util.get_connection(self._config)
        except:
            self._logger.error("StackOverflowDao failed")
            raise

    def close_connection(self):
        self._db_util.close_connection(self._cnx)

    def get_message_type_id(self, message_type):
        return self._db_util.get_message_type_id(self._cnx, message_type)

    def get_user_id(self, user_name):
        user_id = self._db_util.select_user_id_by_name(self._cnx, user_name, self._logger)
        if not user_id:
            self._db_util.insert_user(self._cnx, user_name, None, self._logger)
            user_id = self._db_util.select_user_id_by_name(self._cnx, user_name, self._logger)

        return user_id

    def select_project_id(self, project_name):
        return self._db_util.select_project_id(self._cnx, project_name, self._logger)

    def select_forum_id(self, forum_name, project_id):
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
        cursor = self._cnx.cursor()
        query = "UPDATE topic SET created_at = %s WHERE id = %s AND forum_id = %s"
        arguments = [created_at, topic_id, forum_id]
        cursor.execute(query, arguments)
        self._cnx.commit()
        cursor.close()

    def update_message(self, own_id, topic_id, body, votes):
        try:
            cursor = self._cnx.cursor()
            query = "UPDATE message " \
                    "SET body = %s, votes = %s WHERE own_id = %s AND topic_id = %s"
            arguments = [body, votes, own_id, topic_id]
            cursor.execute(query, arguments)
            self._cnx.commit()
        except:
            self._logger.warning("message " + str(own_id) + ") for topic id: " + str(topic_id) + " not inserted", exc_info=True)

    def insert_message(self, own_id, pos, type, topic_id, body, votes, author_id, created_at):
        try:
            cursor = self._cnx.cursor()
            query = "INSERT IGNORE INTO message " \
                    "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
            arguments = [None, own_id, pos, type, 0, topic_id, 0, body, votes, author_id, created_at]
            cursor.execute(query, arguments)
            self._cnx.commit()
        except:
            self._logger.warning("message " + str(own_id) + ") for topic id: " + str(topic_id) + " not inserted", exc_info=True)

    def insert_topic(self, own_id, forum_id, name, votes, views, created_at, last_change_at):
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
        except Exception, e:
            self._logger.warning("topic " + str(own_id) + ") for forum id: " + str(forum_id) + " not inserted", exc_info=True)

    def insert_message_dependency(self, source_message_id, target_message_id):
        cursor = self._cnx.cursor()
        query = "INSERT IGNORE INTO message_dependency " \
                "VALUES (%s, %s)"
        arguments = [source_message_id, target_message_id]
        cursor.execute(query, arguments)
        self._cnx.commit()
        cursor.close()

    def get_topic_own_id(self, forum_id, topic_id):
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

    def get_topic_own_ids(self, forum_id):
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
        cursor = self._cnx.cursor()
        query = "INSERT IGNORE INTO attachment " \
                "VALUES (%s, %s, %s, %s, %s, %s, %s)"
        arguments = [None, own_id, message_id, name, None, None, url]
        cursor.execute(query, arguments)
        self._cnx.commit()
        cursor.close()

    def select_message_id(self, own_id, topic_id):
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