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

from querier_stackoverflow import StackOverflowQuerier
from extractor.util.db_util import DbUtil
from extractor.util.date_util import DateUtil


class Topic2Db(object):

    def __init__(self, db_name, forum_id, interval, token,
                 config, log_path):
        self.log_path = log_path
        self.interval = interval
        self.db_name = db_name
        self.forum_id = forum_id
        self.token = token
        config.update({'database': db_name})
        self.config = config
        self.pos = 0
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
            self.querier = StackOverflowQuerier(self.token, self.logger)
            self.cnx = mysql.connector.connect(**self.config)
            self.extract()
        except Exception, e:
            self.logger.error("Topic2Db failed", exc_info=True)

    def get_user_id(self, user_name):
        user_id = self.db_util.select_user_id_by_name(self.cnx, user_name, self.logger)
        if not user_id:
            self.db_util.insert_user(self.cnx, user_name, None, self.logger)
            user_id = self.db_util.select_user_id_by_name(self.cnx, user_name, self.logger)

        return user_id

    def insert_message(self, own_id, pos, type, topic_id, body, votes, author_id, created_at):
        try:
            cursor = self.cnx.cursor()
            query = "INSERT IGNORE INTO message " \
                    "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
            arguments = [None, own_id, pos, type, 0, topic_id, 0, body, votes, author_id, created_at]
            cursor.execute(query, arguments)
            self.cnx.commit()
        except:
            self.logger.warning("message " + str(own_id) + ") for topic id: " + str(topic_id) + " not inserted", exc_info=True)

    def insert_topic(self, own_id, forum_id, name, votes, views, created_at, last_changed_at):
        try:
            cursor = self.cnx.cursor()
            query = "INSERT IGNORE INTO topic " \
                    "VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
            arguments = [None, own_id, forum_id, name, votes, views, created_at, last_changed_at]
            cursor.execute(query, arguments)
            self.cnx.commit()

            query = "SELECT id FROM topic WHERE own_id = %s AND forum_id = %s"
            arguments = [own_id, forum_id]
            cursor.execute(query, arguments)

            found = None
            row = cursor.fetchone()
            cursor.close()
            if row:
                found = row[0]

            return found
        except Exception, e:
            self.logger.warning("topic " + str(own_id) + ") for forum id: " + str(forum_id) + " not inserted", exc_info=True)

    def extract_answers(self, answers, topic_id, message_id):
        for a in answers:
            own_id = self.querier.get_container_own_id(a)
            body = self.querier.get_container_body(a)
            author_id = self.get_user_id(self.querier.get_container_author(a))
            created_at = self.querier.get_container_created_at(a)
            votes = self.querier.get_container_votes(a)

            if a.accepted:
                message_type = "accepted_answer"
            else:
                message_type = "answer"

            self.insert_message(own_id, self.pos, self.db_util.get_message_type_id(self.cnx, message_type), topic_id, body, votes, author_id, created_at)
            answer_message_id = self.select_message_id(own_id, topic_id)
            self.insert_message_dependency(message_id, answer_message_id)
            self.extract_attachments(body, answer_message_id)
            self.pos += 1

            self.extract_comment_messages(self.querier.get_comments(a), topic_id, answer_message_id)

    def insert_message_dependency(self, source_message_id, target_message_id):
        cursor = self.cnx.cursor()
        query = "INSERT IGNORE INTO message_dependency " \
                "VALUES (%s, %s, %s)"
        arguments = [None, source_message_id, target_message_id]
        cursor.execute(query, arguments)
        self.cnx.commit()
        cursor.close()

    def extract_comment_messages(self, comments, topic_id, message_id):
        for c in comments:
            own_id = self.querier.get_container_own_id(c)
            body = self.querier.get_container_body(c)
            author_id = self.get_user_id(self.querier.get_container_author(c))
            created_at = self.querier.get_container_created_at(c)
            votes = self.querier.get_container_votes(c)
            self.insert_message(own_id, self.pos, self.db_util.get_message_type_id(self.cnx, "comment"), topic_id, body, votes, author_id, created_at)
            comment_message_id = self.select_message_id(own_id, topic_id)
            self.insert_message_dependency(message_id, comment_message_id)
            self.extract_attachments(body, comment_message_id)
            self.pos += 1

    def select_message_id(self, own_id, topic_id):
        cursor = self.cnx.cursor()

        query = "SELECT id FROM message WHERE own_id = %s AND topic_id = %s"
        arguments = [own_id, topic_id]
        cursor.execute(query, arguments)

        found = None
        row = cursor.fetchone()
        cursor.close()
        if row:
            found = row[0]

        return found

    def get_topic_last_changed_at(self, own_id, forum_id):
        cursor = self.cnx.cursor()

        query = "SELECT last_changed_at FROM topic WHERE own_id = %s AND forum_id = %s"
        arguments = [own_id, forum_id]
        cursor.execute(query, arguments)

        found = None
        row = cursor.fetchone()
        cursor.close()
        if row:
            found = row[0]

        return found

    def insert_attachment(self, own_id, message_id, name, url):
        cursor = self.cnx.cursor()
        query = "INSERT IGNORE INTO attachment " \
                "VALUES (%s, %s, %s, %s, %s, %s, %s)"
        arguments = [None, own_id, message_id, name, None, None, url]
        cursor.execute(query, arguments)
        self.cnx.commit()
        cursor.close()

    def extract_attachments(self, body, message_id):
        attachments = self.querier.get_attachments(body)
        if attachments:
            self.insert_attachments(attachments, message_id)

    def insert_attachments(self, attachments, message_id):
        pos = 0
        for attachment in attachments:
            attachment_name = self.querier.get_attachment_name(attachment)
            attachment_own_id = self.querier.generate_attachment_id(message_id, pos)
            attachment_url = self.querier.get_attachment_url(attachment)
            self.insert_attachment(attachment_own_id, message_id, attachment_name, attachment_url)
            pos += 1

    def extract_topic(self, topic):
        last_changed_at = self.querier.get_topic_last_changed_at(topic)
        own_id = self.querier.get_container_own_id(topic)

        if self.get_topic_last_changed_at(own_id, self.forum_id) != last_changed_at:
            name = self.querier.get_topic_name(topic)
            votes = self.querier.get_container_votes(topic)
            views = self.querier.get_topic_views(topic)
            created_at = self.querier.get_container_created_at(topic)

            topic_id = self.insert_topic(own_id, self.forum_id, name, votes, views, created_at, last_changed_at)
            author_id = self.get_user_id(self.querier.get_container_author(topic))

            self.pos = 0
            body = self.querier.get_container_body(topic)
            self.insert_message(own_id, self.pos, self.db_util.get_message_type_id(self.cnx, "answer"), topic_id, body,
                                votes, author_id, created_at)
            message_id = self.select_message_id(own_id, topic_id)
            self.extract_attachments(body, message_id)

            self.pos += 1

            self.extract_comment_messages(self.querier.get_comments(topic), topic_id, message_id)
            self.extract_answers(self.querier.get_answers(topic), topic_id, message_id)

    def extract(self):
        try:
            start_time = datetime.now()

            for topic_id in self.interval:
                topic = self.querier.get_topic(topic_id)
                self.extract_topic(topic)

            end_time = datetime.now()

            minutes_and_seconds = divmod((end_time-start_time).total_seconds(), 60)
            self.logger.info("process finished after " + str(minutes_and_seconds[0])
                           + " minutes and " + str(round(minutes_and_seconds[1], 1)) + " secs")
        except Exception, e:
            self.logger.error("Topic2Db failed", exc_info=True)
