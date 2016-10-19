#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'valerio cosentino'

from extractor.util.db_util import DbUtil


class EclipseForumDao():

    def __init__(self, config, logger):
        self.config = config
        self.logger = logger
        self.db_util = DbUtil()
        try:
            self.cnx = self.db_util.get_connection(self.config)
        except:
            self.logger.error("EclipseForumDao failed", exc_info=True)

    def close_connection(self):
        self.db_util.close_connection(self.cnx)

    def get_message_type_id(self, message_type):
        return self.db_util.get_message_type_id(self.cnx, message_type)

    def get_user_id(self, user_name):
        user_id = self.db_util.select_user_id_by_name(self.cnx, user_name, self.logger)
        if not user_id:
            self.db_util.insert_user(self.cnx, user_name, None, self.logger)
            user_id = self.db_util.select_user_id_by_name(self.cnx, user_name, self.logger)

        return user_id

    def insert_message_attachment(self, url, own_id, name, extension, size, message_id):
        cursor = self.cnx.cursor()
        query = "INSERT IGNORE INTO attachment " \
                "VALUES (%s, %s, %s, %s, %s, %s, %s)"
        arguments = [None, own_id, message_id, name, extension, size, url]
        cursor.execute(query, arguments)
        self.cnx.commit()

    def get_topic_own_id(self, forum_id, topic_id):
        found = None
        cursor = self.cnx.cursor()
        query = "SELECT own_id FROM topic WHERE forum_id = %s AND id = %s"
        arguments = [forum_id, topic_id]
        cursor.execute(query, arguments)

        row = cursor.fetchone()
        cursor.close()
        if row:
            found = row[0]

        return found

    def get_topic_id(self, topic_own_id, forum_id):
        found = None

        cursor = self.cnx.cursor()
        query = "SELECT id FROM topic WHERE own_id = %s AND forum_id = %s"
        arguments = [topic_own_id, forum_id]
        cursor.execute(query, arguments)

        row = cursor.fetchone()
        cursor.close()

        if row:
            found = row[0]

        return found

    def get_topic_ids(self, forum_id):
        topic_ids = []

        cursor = self.cnx.cursor()
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

    def update_topic_created_at(self, topic_id, created_at, forum_id):
        cursor = self.cnx.cursor()
        query = "UPDATE topic SET created_at = %s WHERE id = %s AND forum_id = %s"
        arguments = [created_at, topic_id, forum_id]
        cursor.execute(query, arguments)
        self.cnx.commit()
        cursor.close()

    def insert_message(self, own_id, pos, type, topic_id, body, votes, author_id, created_at):
        try:
            cursor = self.cnx.cursor()
            query = "INSERT IGNORE INTO message " \
                    "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
            arguments = [None, own_id, pos, type, 0, topic_id, 0, body, votes, author_id, created_at]
            cursor.execute(query, arguments)
            self.cnx.commit()

            query = "SELECT id FROM message WHERE own_id = %s AND topic_id = %s"
            arguments = [own_id, topic_id]
            cursor.execute(query, arguments)

            found = None
            row = cursor.fetchone()
            cursor.close()
            if row:
                found = row[0]

            return found
        except:
            self.logger.warning("message " + str(own_id) + ") for topic id: " + str(topic_id) + " not inserted", exc_info=True)

    def select_forum_id(self, forum_name, project_id):
        cursor = self.cnx.cursor()
        query = "SELECT id " \
                "FROM forum " \
                "WHERE name = %s AND project_id = %s"
        arguments = [forum_name, project_id]
        cursor.execute(query, arguments)

        row = cursor.fetchone()
        cursor.close()

        if row:
            found = row[0]
        else:
            self.logger.warning("no forum with this name " + str(forum_name))

        return found

    def select_forum_url(self, forum_name, project_id):
        cursor = self.cnx.cursor()
        query = "SELECT url " \
                "FROM forum " \
                "WHERE name = %s AND project_id = %s"
        arguments = [forum_name, project_id]
        cursor.execute(query, arguments)

        row = cursor.fetchone()
        cursor.close()

        if row:
            found = row[0]
        else:
            self.logger.warning("no forum with this name " + str(forum_name))

        return found

    def select_project_id(self, project_name):
        return self.db_util.select_project_id(self.cnx, project_name, self.logger)

    def insert_forum(self, project_id, forum_name, url, type):
        cursor = self.cnx.cursor()
        query = "INSERT IGNORE INTO forum " \
                "VALUES (%s, %s, %s, %s, %s)"
        arguments = [None, project_id, forum_name, url, type]
        cursor.execute(query, arguments)
        self.cnx.commit()

        query = "SELECT id " \
                "FROM forum " \
                "WHERE name = %s"
        arguments = [forum_name]
        cursor.execute(query, arguments)

        row = cursor.fetchone()
        cursor.close()

        if row:
            found = row[0]
        else:
            self.logger.warning("no forum with this name " + str(forum_name))

        return found

    def select_project_id(self, project_name):
        return self.db_util.select_project_id(self.cnx, project_name, self.logger)

    def select_topic_id(self, forum_id, own_id):
        try:
            found = None
            cursor = self.cnx.cursor()
            query = "SELECT id FROM topic WHERE forum_id = %s AND own_id = %s"
            arguments = [forum_id, own_id]
            cursor.execute(query, arguments)

            row = cursor.fetchone()
            cursor.close()
            if row:
                found = row[0]

            return found
        except Exception, e:
            self.logger.warning("topic id " + str(own_id) + " not found for forum id: " + str(forum_id), exc_info=True)

    def insert_topic(self, own_id, forum_id, title, views, last_changed_at):
        try:
            cursor = self.cnx.cursor()
            query = "INSERT IGNORE INTO topic " \
                    "VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
            arguments = [None, own_id, forum_id, title.lower(), None, views, None, last_changed_at]
            cursor.execute(query, arguments)
            self.cnx.commit()
            cursor.close()
        except Exception, e:
            self.logger.warning("topic with title " + title.lower() + " not inserted for forum id: " + str(forum_id), exc_info=True)

    def update_topic_info(self, topic_id, forum_id, views, last_changed_at):
        cursor = self.cnx.cursor()
        query = "UPDATE topic SET views = %s, last_changed_at = %s WHERE id = %s AND forum_id = %s"
        arguments = [views, last_changed_at, topic_id, forum_id]
        cursor.execute(query, arguments)
        self.cnx.commit()
        cursor.close()