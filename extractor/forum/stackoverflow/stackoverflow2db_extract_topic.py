#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'valerio cosentino'

from datetime import datetime
import time
import sys
import logging
import logging.handlers
sys.path.insert(0, "..//..//..")

from querier_stackoverflow import StackOverflowQuerier
from stackoverflow_dao import StackOverflowDao


class StackOverflowTopic2Db(object):

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
            self.dao = StackOverflowDao(self.config, self.logger)
            self.extract()
        except Exception, e:
            self.logger.error("Topic2Db failed", exc_info=True)

    def extract_answers(self, answers, topic_id, message_id):
        for a in answers:
            own_id = self.querier.get_container_own_id(a)
            body = self.querier.get_container_body(a)
            author_id = self.dao.get_user_id(self.querier.get_container_author(a))
            created_at = self.querier.get_container_created_at(a)
            votes = self.querier.get_container_votes(a)

            if a.accepted:
                message_type = "accepted_answer"
            else:
                message_type = "answer"

            self.dao.insert_message(own_id, self.pos, self.dao.get_message_type_id(message_type), topic_id, self.querier.remove_html_tags(body), votes, author_id, created_at)
            answer_message_id = self.dao.select_message_id(own_id, topic_id)
            self.dao.insert_message_dependency(message_id, answer_message_id)
            self.extract_attachments(body, answer_message_id)
            self.pos += 1

            self.extract_comment_messages(self.querier.get_comments(a), topic_id, answer_message_id)

    def extract_comment_messages(self, comments, topic_id, message_id):
        for c in comments:
            own_id = self.querier.get_container_own_id(c)
            body = self.querier.get_container_body(c)
            author_id = self.dao.get_user_id(self.querier.get_container_author(c))
            created_at = self.querier.get_container_created_at(c)
            votes = self.querier.get_container_votes(c)
            self.dao.insert_message(own_id, self.pos, self.dao.get_message_type_id("comment"), topic_id, self.querier.remove_html_tags(body), votes, author_id, created_at)
            comment_message_id = self.dao.select_message_id(own_id, topic_id)
            self.dao.insert_message_dependency(message_id, comment_message_id)
            self.extract_attachments(body, comment_message_id)
            self.pos += 1

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
            self.dao.insert_attachment(attachment_own_id, message_id, attachment_name, attachment_url)
            pos += 1

    def extract_topic(self, topic):
        last_changed_at = self.querier.get_topic_last_changed_at(topic)
        own_id = self.querier.get_container_own_id(topic)

        if self.dao.get_topic_last_changed_at(own_id, self.forum_id) != last_changed_at:
            name = self.querier.get_topic_name(topic)
            votes = self.querier.get_container_votes(topic)
            views = self.querier.get_topic_views(topic)
            created_at = self.querier.get_container_created_at(topic)

            topic_id = self.dao.insert_topic(own_id, self.forum_id, name, votes, views, created_at, last_changed_at)
            author_id = self.dao.get_user_id(self.querier.get_container_author(topic))

            self.pos = 0
            body = self.querier.get_container_body(topic)
            self.dao.insert_message(own_id, self.pos, self.dao.get_message_type_id("question"), topic_id, self.querier.remove_html_tags(body),
                                    votes, author_id, created_at)
            message_id = self.dao.select_message_id(own_id, topic_id)
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
            self.logger.info("StackOverflowTopic2Db finished after " + str(minutes_and_seconds[0])
                           + " minutes and " + str(round(minutes_and_seconds[1], 1)) + " secs")
        except Exception, e:
            self.logger.error("StackOverflowTopic2Db failed", exc_info=True)
