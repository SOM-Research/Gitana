#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'valerio cosentino'

from extractor.util.db_util import DbUtil


class SlackDao():

    def __init__(self, config, logger):
        self.config = config
        self.logger = logger
        self.db_util = DbUtil()
        try:
            self.cnx = self.db_util.get_connection(self.config)
        except:
            self.logger.error("SlackDao failed", exc_info=True)

    def close_connection(self):
        self.db_util.close_connection(self.cnx)

    def select_project_id(self, project_name):
        return self.db_util.select_project_id(self.cnx, project_name, self.logger)

    def select_instant_messaging_id(self, instant_messaging_name, project_id):
        cursor = self.cnx.cursor()
        query = "SELECT id " \
                "FROM instant_messaging " \
                "WHERE name = %s AND project_id = %s"
        arguments = [instant_messaging_name, project_id]
        cursor.execute(query, arguments)

        row = cursor.fetchone()
        cursor.close()

        if row:
            found = row[0]
        else:
            self.logger.warning("no instant messaging with this name " + str(instant_messaging_name))

        return found

    def get_message_type_id(self, message_type):
        return self.db_util.get_message_type_id(self.cnx, message_type)

    def insert_url_attachment(self, own_id, message_id, name, extension, url):
        cursor = self.cnx.cursor()
        query = "INSERT IGNORE INTO attachment " \
                "VALUES (%s, %s, %s, %s, %s, %s, %s)"
        arguments = [None, own_id, message_id, name, extension, None, url]
        cursor.execute(query, arguments)
        self.cnx.commit()
        cursor.close()

    def insert_attachment(self, own_id, message_id, name, extension, bytes, url):
        cursor = self.cnx.cursor()
        query = "INSERT IGNORE INTO attachment " \
                "VALUES (%s, %s, %s, %s, %s, %s, %s)"
        arguments = [None, own_id, message_id, name, extension, bytes, url]
        cursor.execute(query, arguments)
        self.cnx.commit()
        cursor.close()

    def select_message_id(self, own_id, channel_id):
        cursor = self.cnx.cursor()

        query = "SELECT id FROM message WHERE own_id = %s AND channel_id = %s"
        arguments = [own_id, channel_id]
        cursor.execute(query, arguments)

        found = None
        row = cursor.fetchone()
        cursor.close()
        if row:
            found = row[0]

        return found

    def get_comments(self, message_id):
        cursor = self.cnx.cursor()
        query = "SELECT COUNT(*) as count " \
                "FROM message_dependency " \
                "WHERE target_message_id = %s OR source_message_id = %s"
        arguments = [message_id, message_id]
        cursor.execute(query, arguments)

        row = cursor.fetchone()
        cursor.close()

        if row:
            found = row[0]
        else:
            self.logger.warning("no message dependency found for message id " + str(message_id))

        return found

        cursor.close()

    def insert_message_dependency(self, source_message_id, target_message_id):
        cursor = self.cnx.cursor()
        query = "INSERT IGNORE INTO message_dependency " \
                "VALUES (%s, %s)"
        arguments = [source_message_id, target_message_id]
        cursor.execute(query, arguments)
        self.cnx.commit()
        cursor.close()

    def insert_message(self, own_id, pos, type, channel_id, body, author_id, created_at):
        try:
            cursor = self.cnx.cursor()
            query = "INSERT IGNORE INTO message " \
                    "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
            arguments = [None, own_id, pos, type, 0, 0, channel_id, body, None, author_id, created_at]
            cursor.execute(query, arguments)
            self.cnx.commit()
        except:
            self.logger.warning("message " + str(own_id) + ") for channel id: " + str(channel_id) + " not inserted", exc_info=True)

    def get_user_id(self, user_name, user_email):
        if user_email:
            user_id = self.db_util.select_user_id_by_email(self.cnx, user_email, self.logger)
        else:
            user_id = self.db_util.select_user_id_by_name(self.cnx, user_name, self.logger)

        if not user_id:
            self.db_util.insert_user(self.cnx, user_name, user_email, self.logger)

            if user_email:
                user_id = self.db_util.select_user_id_by_email(self.cnx, user_email, self.logger)
            else:
                user_id = self.db_util.select_user_id_by_name(self.cnx, user_name, self.logger)

        return user_id

    def insert_channel(self, own_id, instant_messaging_id, name, description, created_at, last_changed_at):
        cursor = self.cnx.cursor()
        query = "INSERT IGNORE INTO channel " \
                "VALUES (%s, %s, %s, %s, %s, %s, %s)"
        arguments = [None, own_id, instant_messaging_id, name, description, created_at, last_changed_at]
        cursor.execute(query, arguments)
        self.cnx.commit()

        query = "SELECT id " \
                "FROM channel " \
                "WHERE own_id = %s AND instant_messaging_id = %s"
        arguments = [own_id, instant_messaging_id]
        cursor.execute(query, arguments)

        row = cursor.fetchone()
        cursor.close()

        if row:
            found = row[0]
        else:
            self.logger.warning("no channel found for instant messaging " + str(instant_messaging_id))

        return found

    def insert_instant_messaging(self, project_id, instant_messaging_name, url, type):
        cursor = self.cnx.cursor()
        query = "INSERT IGNORE INTO instant_messaging " \
                "VALUES (%s, %s, %s, %s, %s)"
        arguments = [None, project_id, instant_messaging_name, url, type]
        cursor.execute(query, arguments)
        self.cnx.commit()

        query = "SELECT id " \
                "FROM instant_messaging " \
                "WHERE name = %s"
        arguments = [instant_messaging_name]
        cursor.execute(query, arguments)

        row = cursor.fetchone()
        cursor.close()

        if row:
            found = row[0]
        else:
            self.logger.warning("no instant messaging linked to " + str(url))

        return found