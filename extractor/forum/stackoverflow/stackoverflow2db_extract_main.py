#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'valerio cosentino'

import mysql.connector
from mysql.connector import errorcode
from datetime import datetime
import multiprocessing
import sys
sys.path.insert(0, "..//..//..")

from extractor.util import multiprocessing_util
from extractor.util.db_util import DbUtil
from extractor.util.date_util import DateUtil
from querier_stackoverflow import StackOverflowQuerier
from stackoverflow2db_extract_topic import Topic2Db


class StackOverflow2DbMain():

    URL = 'http://stackoverflow.com/search?q='

    def __init__(self, db_name, project_name,
                 type, search_query, before_date, recover_import, tokens,
                 config, logger):
        self.logger = logger
        self.log_path = self.logger.name.rsplit('.', 1)[0] + "-" + project_name
        self.type = type
        self.search_query = search_query
        self.project_name = project_name
        self.db_name = db_name
        self.before_date = before_date
        self.recover_import = recover_import
        self.tokens = tokens
        self.url = StackOverflow2DbMain.URL + self.search_query.replace(' ', '+')

        self.db_util = DbUtil()
        self.date_util = DateUtil()

        config.update({'database': db_name})
        self.config = config

        try:
            self.querier = StackOverflowQuerier(self.tokens[0], self.logger)
            self.cnx = mysql.connector.connect(**self.config)
        except:
            self.logger.error("StackOverflow2Db extract failed", exc_info=True)

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

    def get_topics(self, forum_id):
        topic_ids = self.querier.get_topic_ids(self.search_query)

        intervals = [i for i in multiprocessing_util.get_tasks_intervals(topic_ids, len(self.tokens)) if len(i) > 0]

        queue_extractors = multiprocessing.JoinableQueue()
        results = multiprocessing.Queue()

        # Start consumers
        multiprocessing_util.start_consumers(len(self.tokens), queue_extractors, results)

        pos = 0
        for interval in intervals:
            topic_extractor = Topic2Db(self.db_name, forum_id, interval, self.tokens[pos], self.config, self.log_path)
            queue_extractors.put(topic_extractor)
            pos += 1

        # Add end-of-queue markers
        multiprocessing_util.add_poison_pills(len(self.tokens), queue_extractors)

        # Wait for all of the tasks to finish
        queue_extractors.join()

    def extract(self):
        try:
            start_time = datetime.now()
            project_id = self.db_util.select_project_id(self.cnx, self.project_name, self.logger)
            forum_id = self.insert_forum(project_id)
            self.get_topics(forum_id)
            self.cnx.close()

            end_time = datetime.now()

            minutes_and_seconds = divmod((end_time-start_time).total_seconds(), 60)
            self.logger.info("StackOverflow2Db extract finished after " + str(minutes_and_seconds[0])
                         + " minutes and " + str(round(minutes_and_seconds[1], 1)) + " secs")
        except:
            self.logger.error("StackOverflow2Db extract failed", exc_info=True)