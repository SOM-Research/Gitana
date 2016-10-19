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
            self.querier = SlackQuerier(self.url, self.logger)
            self.dao = SlackDao(self.config, self.logger)
        except:
            self.logger.error("Slack2DbUpdate extract failed", exc_info=True)

    def get_channels(self, instant_messaging_id):
        print "here"
        #TODO

    def update(self):
        try:
            start_time = datetime.now()
            project_id = self.dao.select_project_id(self.project_name)
            instant_messaging_id = self.dao.select_instant_messaging_id(self.instant_messaging_name, project_id)
            self.get_channels(instant_messaging_id)
            self.cnx.close()
            end_time = datetime.now()

            minutes_and_seconds = divmod((end_time-start_time).total_seconds(), 60)
            self.logger.info("Slack2DbUpdate extract finished after " + str(minutes_and_seconds[0])
                         + " minutes and " + str(round(minutes_and_seconds[1], 1)) + " secs")
        except:
            self.logger.error("Slack2DbUpdate extract failed", exc_info=True)