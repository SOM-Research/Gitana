#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'valerio cosentino'

from datetime import datetime
import multiprocessing
import sys
sys.path.insert(0, "..//..//..")

from extractor.util import multiprocessing_util
from querier_stackoverflow import StackOverflowQuerier
from stackoverflow2db_extract_topic import StackOverflowTopic2Db
from stackoverflow_dao import StackOverflowDao


class StackOverflow2DbMain():

    def __init__(self, db_name, project_name,
                 type, forum_name, search_query, before_date, recover_import, tokens,
                 config, logger):
        self.logger = logger
        self.log_path = self.logger.name.rsplit('.', 1)[0] + "-" + project_name
        self.type = type
        self.forum_name = forum_name
        self.search_query = search_query
        self.project_name = project_name
        self.db_name = db_name
        self.before_date = before_date
        self.recover_import = recover_import
        self.tokens = tokens

        config.update({'database': db_name})
        self.config = config

        self.querier = StackOverflowQuerier(self.tokens[0], self.logger)
        self.dao = StackOverflowDao(self.config, self.logger)

    def get_topics(self, forum_id):
        topic_ids = self.querier.get_topic_ids(self.search_query, self.before_date)

        intervals = [i for i in multiprocessing_util.get_tasks_intervals(topic_ids, len(self.tokens)) if len(i) > 0]

        queue_extractors = multiprocessing.JoinableQueue()
        results = multiprocessing.Queue()

        # Start consumers
        multiprocessing_util.start_consumers(len(self.tokens), queue_extractors, results)

        pos = 0
        for interval in intervals:
            topic_extractor = StackOverflowTopic2Db(self.db_name, forum_id, interval, self.tokens[pos], self.config, self.log_path)
            queue_extractors.put(topic_extractor)
            pos += 1

        # Add end-of-queue markers
        multiprocessing_util.add_poison_pills(len(self.tokens), queue_extractors)

        # Wait for all of the tasks to finish
        queue_extractors.join()

    def extract(self):
        try:
            start_time = datetime.now()
            project_id = self.dao.select_project_id(self.project_name)
            forum_id = self.dao.insert_forum(project_id, self.forum_name, None, self.type)
            self.get_topics(forum_id)
            self.dao.close_connection()

            end_time = datetime.now()

            minutes_and_seconds = divmod((end_time-start_time).total_seconds(), 60)
            self.logger.info("StackOverflow2DbMain finished after " + str(minutes_and_seconds[0])
                         + " minutes and " + str(round(minutes_and_seconds[1], 1)) + " secs")
        except:
            self.logger.error("StackOverflow2DbMain failed", exc_info=True)