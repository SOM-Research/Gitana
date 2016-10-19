#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'valerio cosentino'

from datetime import datetime
import time
import sys
import logging
import logging.handlers
sys.path.insert(0, "..//..//..")

from querier_slack import SlackQuerier
from slack_dao import SlackDao


class SlackChannel2Db(object):

    def __init__(self, db_name, instant_messaging_id, interval, token,
                 config, log_path):
        self.log_path = log_path
        self.interval = interval
        self.db_name = db_name
        self.instant_messaging_id = instant_messaging_id
        self.token = token
        config.update({'database': db_name})
        self.config = config

    def extract(self):
        try:
            start_time = datetime.now()

            for topic_id in self.interval:
                topic = self.querier.get_topic(topic_id)
                self.extract_topic(topic)

            end_time = datetime.now()

            minutes_and_seconds = divmod((end_time-start_time).total_seconds(), 60)
            self.logger.info("SlackChannel2Db finished after " + str(minutes_and_seconds[0])
                           + " minutes and " + str(round(minutes_and_seconds[1], 1)) + " secs")
        except Exception, e:
            self.logger.error("SlackChannel2Db failed", exc_info=True)