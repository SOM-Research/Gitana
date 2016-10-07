#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'valerio cosentino'

import mysql.connector
from mysql.connector import errorcode
from datetime import datetime
import time
import sys
import logging
import logging.handlers
sys.path.insert(0, "..//..//..")

from querier_eclipse_forum import EclipseForumQuerier
from extractor.util.db_util import DbUtil
from extractor.util.date_util import DateUtil


class Topic2Db(object):

    TOPIC_URL = 'https://www.eclipse.org/forums/index.php/t/'

    def __init__(self, db_name, forum_id, interval,
                 config, log_path):
        self.log_path = log_path
        self.interval = interval
        self.db_name = db_name
        self.forum_id = forum_id
        config.update({'database': db_name})
        self.config = config

        self.db_util = DbUtil()
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
            self.cnx = mysql.connector.connect(**self.config)
            self.extract()
        except Exception, e:
            self.logger.error("Topic2Db failed", exc_info=True)

    def get_user_id(self, user_name, topic_id):
        user_id = self.db_util.select_user_id_by_name(self.cnx, user_name, self.logger)
        if not user_id:
            self.db_util.insert_user(self.cnx, user_name, None, self.logger)
            user_id = self.db_util.select_user_id_by_name(self.cnx, user_name, self.logger)

        return user_id

    def insert_message(self, own_id, pos, topic_id, body, user_id, created_at):
        try:
            cursor = self.cnx.cursor()
            query = "INSERT IGNORE INTO message " \
                    "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
            arguments = [None, own_id, pos, self.db_util.get_message_type_id(self.cnx, "reply"), 0, topic_id, 0, body, None, user_id, created_at]
            cursor.execute(query, arguments)
            self.cnx.commit()

            query = "SELECT id FROM message WHERE own_id = %s AND topic_id = %s"
            arguments = [own_id, topic_id]
            cursor.execute(query, arguments)

            found = None
            row = cursor.fetchone()
            cursor.close()
            if row:
                found = row[0]

            return found
        except Exception, e:
            self.logger.warning("message in pos " + str(pos) + ") for topic id: " + str(topic_id) + " not inserted", exc_info=True)

    def insert_message_attachment(self, url, own_id, name, extension, size, message_id):
        cursor = self.cnx.cursor()
        query = "INSERT IGNORE INTO attachment " \
                "VALUES (%s, %s, %s, %s, %s, %s, %s)"
        arguments = [None, own_id, message_id, name, extension, size, url]
        cursor.execute(query, arguments)
        self.cnx.commit()

    def get_message_attachments_info(self, message_id, message):
        attachments = self.querier.message_get_attachments(message)

        for a in attachments:
            url = self.querier.get_attachment_url(a)
            own_id = self.querier.get_attachment_own_id(a)
            name = self.querier.get_attachment_name(a)
            extension = name.split('.')[-1].strip('').lower()
            size = self.querier.get_attachment_size(a)

            self.insert_message_attachment(url, own_id, name, extension, size, message_id)

    def get_message_info(self, topic_id, message, pos):
        own_id = self.querier.get_message_own_id(message)
        created_at = self.date_util.get_timestamp(self.querier.get_created_at(message), "%a, %d %B %Y %H:%M")
        body = self.querier.get_message_body(message)
        author_name = self.querier.get_message_author_name(message)

        message_id = self.insert_message(own_id, pos, topic_id, body, self.get_user_id(author_name, topic_id), created_at)

        if self.querier.message_has_attachments(message):
            self.get_message_attachments_info(message_id, message)

        if pos == 1:
            self.update_topic_created_at(topic_id, created_at)

    def update_topic_created_at(self, topic_id, created_at):
        cursor = self.cnx.cursor()
        query = "UPDATE topic SET created_at = %s WHERE id = %s AND forum_id = %s"
        arguments = [created_at, topic_id, self.forum_id]
        cursor.execute(query, arguments)
        self.cnx.commit()
        cursor.close()

    def get_topic_own_id(self, forum_id, topic_id):
        found = None
        cursor = self.cnx.cursor()
        query = "SELECT own_id FROM topic WHERE forum_id = %s AND id = %s"
        arguments = [forum_id, topic_id]
        cursor.execute(query, arguments)

        row = cursor.fetchone()
        cursor.close()
        if row:
            found = row[0]

        return found

    def extract(self):
        try:
            start_time = datetime.now()

            for topic_id in self.interval:
                topic_own_id = self.get_topic_own_id(self.forum_id, topic_id)

                self.querier.set_url(Topic2Db.TOPIC_URL + str(topic_own_id) + "/")
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
            self.logger.info("process finished after " + str(minutes_and_seconds[0])
                           + " minutes and " + str(round(minutes_and_seconds[1], 1)) + " secs")
        except Exception, e:
            self.logger.error("Topic2Db failed", exc_info=True)
