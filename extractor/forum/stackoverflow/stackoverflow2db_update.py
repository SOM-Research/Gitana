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


class StackOverflow2DbUpdate():

    def __init__(self, db_name, project_name, forum_name, tokens,
                 config, logger):
        self.logger = logger
        self.log_path = self.logger.name.rsplit('.', 1)[0] + "-" + project_name
        self.project_name = project_name
        self.db_name = db_name
        self.forum_name = forum_name
        self.tokens = tokens

        config.update({'database': db_name})
        self.config = config

        try:
            self.querier = StackOverflowQuerier(self.tokens[0], self.logger)
            self.dao = StackOverflowDao(self.config, self.logger)
        except:
            self.logger.error("StackOverflow2DbUpdate extract failed", exc_info=True)

    def get_topics(self, forum_id):
        topic_ids = self.dao.get_topic_ids(forum_id)

        if topic_ids:
            intervals = [i for i in multiprocessing_util.get_tasks_intervals(topic_ids, len(self.tokens)) if len(i) > 0]

            queue_extractors = multiprocessing.JoinableQueue()
            results = multiprocessing.Queue()

            # Start consumers
            multiprocessing_util.start_consumers(len(self.tokens), queue_extractors, results)

            for interval in intervals:
                topic_extractor = StackOverflowTopic2Db(self.db_name, forum_id, interval, self.config, self.log_path)
                queue_extractors.put(topic_extractor)

            # Add end-of-queue markers
            multiprocessing_util.add_poison_pills(len(self.tokens), queue_extractors)

            # Wait for all of the tasks to finish
            queue_extractors.join()

    def update(self):
        try:
            start_time = datetime.now()
            project_id = self.dao.select_project_id(self.project_name)
            forum_id = self.dao.select_forum_id(self.forum_name, project_id)
            self.get_topics(forum_id)
            self.dao.close_connection()
            end_time = datetime.now()

            minutes_and_seconds = divmod((end_time-start_time).total_seconds(), 60)
            self.logger.info("StackOverflow2DbUpdate finished after " + str(minutes_and_seconds[0])
                         + " minutes and " + str(round(minutes_and_seconds[1], 1)) + " secs")
        except:
            self.logger.error("StackOverflow2DbUpdate failed", exc_info=True)