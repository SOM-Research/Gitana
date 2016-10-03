#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'valerio cosentino'

import mysql.connector
from mysql.connector import errorcode
from datetime import datetime
import multiprocessing
import sys
sys.path.insert(0, "..//..//..")

from extractor.util import consumer
from querier_eclipse_forum import EclipseForumQuerier


class Forum2DbMain():

    def __init__(self, db_name, project_name,
                 type, url, before_date, recover_import, num_processes,
                 config, logger):
        self.logger = logger
        self.log_path = self.logger.name.rsplit('.', 1)[0] + "-" + project_name
        self.type = type
        self.url = url
        self.project_name = project_name
        self.db_name = db_name
        self.before_date = before_date
        self.recover_import = recover_import
        self.num_processes = num_processes

        config.update({'database': db_name})
        self.config = config

        #try:
        self.querier = EclipseForumQuerier(self.url, self.logger)
        self.cnx = mysql.connector.connect(**self.config)
        #except:
        #    self.logger.error("Forum2Db extract failed", exc_info=True)

    def select_project(self):
        found = None
        cursor = self.cnx.cursor()
        query = "SELECT r.id " \
                "FROM project p " \
                "WHERE p.name = %s"
        arguments = [self.project_name]
        cursor.execute(query, arguments)
        row = cursor.fetchone()
        cursor.close()

        if row:
            found = row[0]
        else:
            self.logger.error("the project " + self.project_name + " does not exist")

        return found

    def insert_forum(self, project_id):
        cursor = self.cnx.cursor()
        query = "INSERT IGNORE INTO forum " \
                "VALUES (%s, %s, %s, %s)"
        arguments = [None, project_id, self.url, self.type]
        cursor.execute(query, arguments)
        self.cnx.commit()

        query = "SELECT id " \
                "FROM forum " \
                "WHERE url = %s"
        arguments = [self.url]
        cursor.execute(query, arguments)

        row = cursor.fetchone()
        cursor.close()

        if row:
            found = row[0]
        else:
            self.logger("no forum linked to " + str(self.url))

        return found

    def get_topics(self):
        self.querier.start_browser()
        next_page = True

        while next_page:
            topics_on_page = self.querier.get_topics()
            for t in topics_on_page:
                print "do something"

            next_page = self.querier.go_next_page()

    def extract(self):
        #try:
        start_time = datetime.now()
        self.get_topics()
        self.cnx.close()
        end_time = datetime.now()

        minutes_and_seconds = divmod((end_time-start_time).total_seconds(), 60)
        self.logger.info("Forum2Db extract finished after " + str(minutes_and_seconds[0])
                     + " minutes and " + str(round(minutes_and_seconds[1], 1)) + " secs")
        #except:
        #    self.logger.error("Forum2Db extract failed", exc_info=True)