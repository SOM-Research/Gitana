#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'valerio cosentino'

from datetime import datetime
import multiprocessing
import sys
sys.path.insert(0, "..//..//..")

from extractor.util import multiprocessing_util
from querier_slack import SlackQuerier
from slack2db_extract_channel import SlackChannel2Db
from slack_dao import SlackDao


class Slack2DbUpdate():

    def __init__(self, db_name, project_name, instant_messaging_name, tokens,
                 config, logger):
        self.logger = logger
        self.log_path = self.logger.name.rsplit('.', 1)[0] + "-" + project_name
        self.project_name = project_name
        self.db_name = db_name
        self.instant_messaging_name = instant_messaging_name
        self.tokens = tokens

        config.update({'database': db_name})
        self.config = config

        try:
            self.querier = SlackQuerier(self.tokens[0], self.logger)
            self.dao = SlackDao(self.config, self.logger)
        except:
            self.logger.error("Slack2DbUpdate extract failed", exc_info=True)

    def update_channels(self, instant_messaging_id):
        channel_ids = self.dao.get_channel_ids(instant_messaging_id)

        if channel_ids:
            intervals = [i for i in multiprocessing_util.get_tasks_intervals(channel_ids, len(self.tokens)) if len(i) > 0]

            queue_extractors = multiprocessing.JoinableQueue()
            results = multiprocessing.Queue()

            # Start consumers
            multiprocessing_util.start_consumers(len(self.tokens), queue_extractors, results)

            for i in range(len(intervals)):
                channel_extractor = SlackChannel2Db(self.db_name, instant_messaging_id, intervals[i], self.tokens[i], self.config, self.log_path)
                queue_extractors.put(channel_extractor)

            # Add end-of-queue markers
            multiprocessing_util.add_poison_pills(len(self.tokens), queue_extractors)

            # Wait for all of the tasks to finish
            queue_extractors.join()

    def update(self):
        try:
            start_time = datetime.now()
            project_id = self.dao.select_project_id(self.project_name)
            instant_messaging_id = self.dao.select_instant_messaging_id(self.instant_messaging_name, project_id)
            self.update_channels(instant_messaging_id)
            self.dao.close_connection()
            end_time = datetime.now()

            minutes_and_seconds = divmod((end_time-start_time).total_seconds(), 60)
            self.logger.info("Slack2DbUpdate extract finished after " + str(minutes_and_seconds[0])
                         + " minutes and " + str(round(minutes_and_seconds[1], 1)) + " secs")
        except:
            self.logger.error("Slack2DbUpdate extract failed", exc_info=True)