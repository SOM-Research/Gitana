#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'valerio cosentino'

from datetime import datetime
import time

from querier_eclipse_forum import EclipseForumQuerier
from util.date_util import DateUtil
from eclipse_forum_dao import EclipseForumDao
from util.logging_util import LoggingUtil


class EclipseTopic2Db(object):
    """
    This class handles the import of Eclipse forum topics
    """

    TOPIC_URL = 'https://www.eclipse.org/forums/index.php/t/'

    def __init__(self, db_name, forum_id, interval,
                 config, log_root_path):
        """
        :type db_name: str
        :param db_name: the name of an existing DB

        :type forum_id: int
        :param forum_id: the id of an existing forum in the DB

        :type interval: list int
        :param interval: a list of topic ids to import

        :type config: dict
        :param config: the DB configuration file

        :type log_root_path: str
        :param log_root_path: the log path
        """

        self._log_root_path = log_root_path
        self._interval = interval
        self._db_name = db_name
        self._forum_id = forum_id
        self._config = config

        self._logging_util = LoggingUtil()
        self._date_util = DateUtil()

        self._fileHandler = None
        self._logger = None
        self._querier = None
        self._dao = None

    def __call__(self):
        try:
            log_path = self._log_root_path + "-topic2db-" + str(self._interval[0]) + "-" + str(self._interval[-1])
            self._logger = self._logging_util.get_logger(log_path)
            self._fileHandler = self._logging_util.get_file_handler(self._logger, log_path, "info")

            self._querier = EclipseForumQuerier(None, self._logger)
            self._dao = EclipseForumDao(self._config, self._logger)
            self.extract()
        except Exception:
            self._logger.error("EclipseTopic2Db failed", exc_info=True)
        finally:
            if self._dao:
                self._dao.close_connection()

    def _get_message_attachments_info(self, message_id, message):
        #get attachment informatio of messages
        attachments = self._querier.message_get_attachments(message)

        for a in attachments:
            url = self._querier.get_attachment_url(a)
            own_id = self._querier.get_attachment_own_id(a)
            name = self._querier.get_attachment_name(a)
            extension = name.split('.')[-1].strip('').lower()
            size = self._querier.get_attachment_size(a)

            self._dao.insert_message_attachment(url, own_id, name, extension, size, message_id)

    def _get_message_info(self, topic_id, message, pos):
        # get information of topic messages
        own_id = self._querier.get_message_own_id(message)
        created_at = self._date_util.get_timestamp(self._querier.get_created_at(message), "%a, %d %B %Y %H:%M")
        body = self._querier.get_message_body(message)
        author_name = self._querier.get_message_author_name(message)
        message_id = self._dao.insert_message(own_id, pos, self._dao.get_message_type_id("reply"), topic_id, body,
                                              None, self._dao.get_user_id(author_name), created_at)

        if self._querier.message_has_attachments(message):
            self._get_message_attachments_info(message_id, message)

        if pos == 1:
            self._dao.update_topic_created_at(topic_id, created_at, self._forum_id)

    def extract(self):
        """
        extracts Eclipse forum topic data and stores it in the DB
        """
        self._logger.info("EclipseTopic2Db started")
        start_time = datetime.now()

        for topic_id in self._interval:
            topic_own_id = self._dao.get_topic_own_id(self._forum_id, topic_id)

            self._querier.set_url(EclipseTopic2Db.TOPIC_URL + str(topic_own_id) + "/")
            self._querier.start_browser()
            time.sleep(3)

            if 'index.php/e/' in self._querier._url:
                self._logger.warning("No URL exists for the topic id " + str(topic_id) + " - " + str(self._forum_id))

            next_page = True
            pos = 1

            while next_page:
                messages_on_page = self._querier.get_messages()

                for message in messages_on_page:
                    self._get_message_info(topic_id, message, pos)
                    pos += 1

                next_page = self._querier.go_next_page()

        self._querier.close_browser()
        end_time = datetime.now()
        minutes_and_seconds = self._logging_util.calculate_execution_time(end_time, start_time)
        self._logger.info("EclipseTopic2Db finished after " + str(minutes_and_seconds[0])
                       + " minutes and " + str(round(minutes_and_seconds[1], 1)) + " secs")
        self._logging_util.remove_file_handler_logger(self._logger, self._fileHandler)
