#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'valerio cosentino'

from util.db_util import DbUtil


class SlackDao():

    def __init__(self, config, logger):
        try:
            self._config = config
            self._logger = logger
            self._db_util = DbUtil()
            self._cnx = self._db_util.get_connection(self._config)
        except:
            self._logger.error("SlackDao init failed")
            raise

    def close_connection(self):
        self._db_util.close_connection(self._cnx)

    def select_project_id(self, project_name):
        return self._db_util.select_project_id(self._cnx, project_name, self._logger)

    def select_instant_messaging_id(self, instant_messaging_name, project_id):
        found = None
        cursor = self._cnx.cursor()
        query = "SELECT id " \
                "FROM instant_messaging " \
                "WHERE name = %s AND project_id = %s"
        arguments = [instant_messaging_name, project_id]
        cursor.execute(query, arguments)

        row = cursor.fetchone()

        if row:
            found = row[0]
        else:
            self._logger.warning("no instant messaging with this name " + str(instant_messaging_name))

        cursor.close()
        return found

    def get_message_type_id(self, message_type):
        return self._db_util.get_message_type_id(self._cnx, message_type)

    def insert_url_attachment(self, own_id, message_id, name, extension, url):
        cursor = self._cnx.cursor()
        query = "INSERT IGNORE INTO attachment " \
                "VALUES (%s, %s, %s, %s, %s, %s, %s)"
        arguments = [None, own_id, message_id, name, extension, None, url]
        cursor.execute(query, arguments)
        self._cnx.commit()
        cursor.close()

    def insert_attachment(self, own_id, message_id, name, extension, bytes, url):
        cursor = self._cnx.cursor()
        query = "INSERT IGNORE INTO attachment " \
                "VALUES (%s, %s, %s, %s, %s, %s, %s)"
        arguments = [None, own_id, message_id, name, extension, bytes, url]
        cursor.execute(query, arguments)
        self._cnx.commit()
        cursor.close()

    def select_message_id(self, own_id, channel_id):
        cursor = self._cnx.cursor()

        query = "SELECT id FROM message WHERE own_id = %s AND channel_id = %s"
        arguments = [own_id, channel_id]
        cursor.execute(query, arguments)

        found = None
        row = cursor.fetchone()
        if row:
            found = row[0]

        cursor.close()
        return found

    def get_comments(self, message_id):
        cursor = self._cnx.cursor()
        query = "SELECT COUNT(*) as count " \
                "FROM message_dependency " \
                "WHERE target_message_id = %s OR source_message_id = %s"
        arguments = [message_id, message_id]
        cursor.execute(query, arguments)

        row = cursor.fetchone()

        if row:
            found = row[0]
        else:
            self._logger.warning("no message dependency found for message id " + str(message_id))

        cursor.close()
        return found

    def insert_message_dependency(self, source_message_id, target_message_id):
        cursor = self._cnx.cursor()
        query = "INSERT IGNORE INTO message_dependency " \
                "VALUES (%s, %s)"
        arguments = [source_message_id, target_message_id]
        cursor.execute(query, arguments)
        self._cnx.commit()
        cursor.close()

    def insert_message(self, own_id, pos, type, channel_id, body, author_id, created_at):
        try:
            cursor = self._cnx.cursor()
            query = "INSERT IGNORE INTO message " \
                    "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
            arguments = [None, own_id, pos, type, 0, 0, channel_id, body, None, author_id, created_at]
            cursor.execute(query, arguments)
            self._cnx.commit()
        except:
            self._logger.warning("message " + str(own_id) + ") for channel id: " + str(channel_id) + " not inserted", exc_info=True)

    def get_user_id(self, user_name, user_email):
        if user_email:
            user_id = self._db_util.select_user_id_by_email(self._cnx, user_email, self._logger)
        else:
            user_id = self._db_util.select_user_id_by_name(self._cnx, user_name, self._logger)

        if not user_id:
            self._db_util.insert_user(self._cnx, user_name, user_email, self._logger)

            if user_email:
                user_id = self._db_util.select_user_id_by_email(self._cnx, user_email, self._logger)
            else:
                user_id = self._db_util.select_user_id_by_name(self._cnx, user_name, self._logger)

        return user_id

    def select_channel_own_id(self, channel_id, instant_messaging_id):
        cursor = self._cnx.cursor()
        query = "SELECT own_id " \
                "FROM channel " \
                "WHERE id = %s AND instant_messaging_id = %s"
        arguments = [channel_id, instant_messaging_id]
        cursor.execute(query, arguments)

        row = cursor.fetchone()

        if row:
            found = row[0]
        else:
            self._logger.warning("no channel found for instant messaging " + str(instant_messaging_id))

        cursor.close()
        return found

    def insert_channel(self, own_id, instant_messaging_id, name, description, created_at, last_change_at):
        cursor = self._cnx.cursor()
        query = "INSERT IGNORE INTO channel " \
                "VALUES (%s, %s, %s, %s, %s, %s, %s)"
        arguments = [None, own_id, instant_messaging_id, name, description, created_at, last_change_at]
        cursor.execute(query, arguments)
        self._cnx.commit()

        query = "SELECT id " \
                "FROM channel " \
                "WHERE own_id = %s AND instant_messaging_id = %s"
        arguments = [own_id, instant_messaging_id]
        cursor.execute(query, arguments)

        row = cursor.fetchone()

        if row:
            found = row[0]
        else:
            self._logger.warning("no channel found for instant messaging " + str(instant_messaging_id))

        cursor.close()
        return found

    def insert_instant_messaging(self, project_id, instant_messaging_name, type):
        cursor = self._cnx.cursor()
        query = "INSERT IGNORE INTO instant_messaging " \
                "VALUES (%s, %s, %s, %s)"
        arguments = [None, project_id, instant_messaging_name, type]
        cursor.execute(query, arguments)
        self._cnx.commit()

        query = "SELECT id " \
                "FROM instant_messaging " \
                "WHERE name = %s"
        arguments = [instant_messaging_name]
        cursor.execute(query, arguments)

        row = cursor.fetchone()

        if row:
            found = row[0]
        else:
            self._logger.warning("no instant messaging with name " + str(instant_messaging_name))

        cursor.close()
        return found

    def get_channel_last_change_at(self, own_id, instant_messaging_id):
        cursor = self._cnx.cursor()

        query = "SELECT last_change_at FROM channel WHERE own_id = %s AND instant_messaging_id = %s"
        arguments = [own_id, instant_messaging_id]
        cursor.execute(query, arguments)

        found = None
        row = cursor.fetchone()
        if row:
            found = row[0]

        cursor.close()
        return found

    def get_channel_ids(self, instant_messaging_id):
        channel_ids = []

        cursor = self._cnx.cursor()
        query = "SELECT id FROM channel WHERE instant_messaging_id = %s"
        arguments = [instant_messaging_id]
        cursor.execute(query, arguments)

        row = cursor.fetchone()

        while row:
            channel_id = row[0]
            channel_ids.append(channel_id)
            row = cursor.fetchone()

        cursor.close()
        return channel_ids