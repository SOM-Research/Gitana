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

    def __init__(self, db_name, project_name, url, tokens,
                 config, logger):
        self.logger = logger
        self.log_path = self.logger.name.rsplit('.', 1)[0] + "-" + project_name
        self.project_name = project_name
        self.db_name = db_name
        self.url = url
        self.tokens = tokens

        config.update({'database': db_name})
        self.config = config

        try:
            self.querier = StackOverflowQuerier(self.url, self.logger)
            self.dao = StackOverflowDao(self.config, self.logger)
        except:
            self.logger.error("StackOverflow2DbUpdate extract failed", exc_info=True)

    def get_topics(self, forum_id):
        print "here"
        #TODO

    def update(self):
        try:
            start_time = datetime.now()
            project_id = self.dao.select_project_id(self.project_name)
            forum_id = self.dao.select_forum_id(project_id)
            self.get_topics(forum_id)
            self.cnx.close()
            end_time = datetime.now()

            minutes_and_seconds = divmod((end_time-start_time).total_seconds(), 60)
            self.logger.info("StackOverflow2DbUpdate extract finished after " + str(minutes_and_seconds[0])
                         + " minutes and " + str(round(minutes_and_seconds[1], 1)) + " secs")
        except:
            self.logger.error("StackOverflow2DbUpdate extract failed", exc_info=True)