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


class Slack2DbMain():

    def __init__(self, db_name, project_name,
                 type, instant_messaging_name, before_date, recover_import, tokens,
                 config, logger):
        self.logger = logger
        self.log_path = self.logger.name.rsplit('.', 1)[0] + "-" + project_name
        self.type = type
        self.instant_messaging_name = instant_messaging_name
        self.project_name = project_name
        self.db_name = db_name
        self.before_date = before_date
        self.recover_import = recover_import
        self.tokens = tokens

        config.update({'database': db_name})
        self.config = config

        self.querier = SlackQuerier(self.tokens[0], self.logger)
        self.dao = SlackDao(self.config, self.logger)

    def get_channels(self, instant_messaging_id):
        channels = self.querier.get_channels()
        for c in channels:
            #TODO
            print self.querier.get_channel_name(c)

    def extract(self):
        try:
            start_time = datetime.now()
            project_id = self.dao.select_project_id(self.project_name)
            instant_messaging_id = self.dao.insert_instant_messaging(project_id, self.instant_messaging_name, None, self.type)
            self.get_channels(instant_messaging_id)
            self.dao.close_connection()

            end_time = datetime.now()

            minutes_and_seconds = divmod((end_time-start_time).total_seconds(), 60)
            self.logger.info("StackOverflow2Db extract finished after " + str(minutes_and_seconds[0])
                         + " minutes and " + str(round(minutes_and_seconds[1], 1)) + " secs")
        except:
            self.logger.error("Slack2Db extract failed", exc_info=True)