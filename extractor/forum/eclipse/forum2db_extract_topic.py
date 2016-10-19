#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'valerio cosentino'

from datetime import datetime
import time
import sys
import logging
import logging.handlers
sys.path.insert(0, "..//..//..")

from querier_eclipse_forum import EclipseForumQuerier
from extractor.util.date_util import DateUtil
from eclipse_forum_dao import EclipseForumDao


class EclipseTopic2Db(object):

    TOPIC_URL = 'https://www.eclipse.org/forums/index.php/t/'

    def __init__(self, db_name, forum_id, interval,
                 config, log_path):
        self.log_path = log_path
        self.interval = interval
        self.db_name = db_name
        self.forum_id = forum_id
        config.update({'database': db_name})
        self.config = config

        self.date_util = DateUtil()

    def __call__(self):
        LOG_FILENAME = self.log_path + "-topic2db"
        self.logger = logging.getLogger(LOG_FILENAME)
        fileHandler = logging.FileHandler(LOG_FILENAME + "-" + str(self.interval[0]) + "-" + str(self.interval[-1]) + ".log", mode='w')
        formatter = logging.Formatter("%(asctime)s:%(levelname)s:%(message)s", "%Y-%m-%d %H:%M:%S")

        fileHandler.setFormatter(formatter)
        self.logger.setLevel(logging.INFO)
        self.logger.addHandler(fileHandler)

        try:
            self.querier = EclipseForumQuerier(None, self.logger)
            self.dao = EclipseForumDao(self.config, self.logger)
            self.extract()
        except Exception, e:
            self.logger.error("Topic2Db failed", exc_info=True)

    def get_message_attachments_info(self, message_id, message):
        attachments = self.querier.message_get_attachments(message)

        for a in attachments:
            url = self.querier.get_attachment_url(a)
            own_id = self.querier.get_attachment_own_id(a)
            name = self.querier.get_attachment_name(a)
            extension = name.split('.')[-1].strip('').lower()
            size = self.querier.get_attachment_size(a)

            self.dao.insert_message_attachment(url, own_id, name, extension, size, message_id)

    def get_message_info(self, topic_id, message, pos):
        own_id = self.querier.get_message_own_id(message)
        created_at = self.date_util.get_timestamp(self.querier.get_created_at(message), "%a, %d %B %Y %H:%M")
        body = self.querier.get_message_body(message)
        author_name = self.querier.get_message_author_name(message)
        message_id = self.dao.insert_message(own_id, pos, self.dao.get_message_type_id("reply"), topic_id, body, None, self.dao.get_user_id(author_name), created_at)

        if self.querier.message_has_attachments(message):
            self.get_message_attachments_info(message_id, message)

        if pos == 1:
            self.dao.update_topic_created_at(topic_id, created_at, self.forum_id)

    def extract(self):
        try:
            start_time = datetime.now()

            for topic_id in self.interval:
                topic_own_id = self.dao.get_topic_own_id(self.forum_id, topic_id)

                self.querier.set_url(EclipseTopic2Db.TOPIC_URL + str(topic_own_id) + "/")
                self.querier.start_browser()
                time.sleep(3)

                if 'index.php/e/' in self.querier.url:
                    self.logger.warning("No URL exists for the topic id " + str(topic_id) + " - " + str(self.forum_id))

                next_page = True
                pos = 1

                while next_page:
                    messages_on_page = self.querier.get_messages()

                    for message in messages_on_page:
                        self.get_message_info(topic_id, message, pos)
                        pos += 1

                    next_page = self.querier.go_next_page()

            self.querier.close_browser()
            end_time = datetime.now()

            minutes_and_seconds = divmod((end_time-start_time).total_seconds(), 60)
            self.logger.info("EclipseTopic2Db finished after " + str(minutes_and_seconds[0])
                           + " minutes and " + str(round(minutes_and_seconds[1], 1)) + " secs")
        except Exception, e:
            self.logger.error("EclipseTopic2Db failed", exc_info=True)
