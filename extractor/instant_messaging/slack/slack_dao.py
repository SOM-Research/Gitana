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

    def insert_instant_messaging(self, project_id, instant_messaging_name, url, type):
        cursor = self.cnx.cursor()
        query = "INSERT IGNORE INTO instant_messaging " \
                "VALUES (%s, %s, %s, %s)"
        arguments = [None, project_id, instant_messaging_name, url, type]
        cursor.execute(query, arguments)
        self.cnx.commit()

        query = "SELECT id " \
                "FROM forum " \
                "WHERE url = %s"
        arguments = [url]
        cursor.execute(query, arguments)

        row = cursor.fetchone()
        cursor.close()

        if row:
            found = row[0]
        else:
            self.logger.warning("no instant messaging linked to " + str(url))

        return found