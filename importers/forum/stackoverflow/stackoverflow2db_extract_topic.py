#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'valerio cosentino'

from datetime import datetime

from querier_stackoverflow import StackOverflowQuerier
from stackoverflow_dao import StackOverflowDao
from util.logging_util import LoggingUtil


class StackOverflowTopic2Db(object):
    """
    This class handles the import of Stackoverflow topics
    """

    def __init__(self, db_name, forum_id, interval, token,
                 config, log_root_path):
        """
        :type db_name: str
        :param db_name: the name of an existing DB

        :type forum_id: int
        :param forum_id: the id of an existing forum in the DB

        :type interval: list int
        :param interval: a list of topic ids to import

        :type token: str
        :param token: a Stackoverflow token

        :type config: dict
        :param config: the DB configuration file

        :type log_root_path: str
        :param log_root_path: the log path
        """

        self._log_root_path = log_root_path
        self._interval = interval
        self._db_name = db_name
        self._forum_id = forum_id
        self._token = token
        self._config = config

        self._logging_util = LoggingUtil()

        self._fileHandler = None
        self._logger = None
        self._querier = None
        self._dao = None

    def __call__(self):
        try:
            log_path = self._log_root_path + "-topic2db-" + str(self._interval[0]) + "-" + str(self._interval[-1])
            self._logger = self._logging_util.get_logger(log_path)
            self._fileHandler = self._logging_util.get_file_handler(self._logger, log_path, "info")

            self._querier = StackOverflowQuerier(self._token, self._logger)
            self._dao = StackOverflowDao(self._config, self._logger)
            self.extract()
        except Exception:
            self._logger.error("StackOverflowTopic2Db failed", exc_info=True)
        finally:
            if self._dao:
                self._dao.close_connection()

    def _extract_answers(self, answers, topic_id, message_id):
        # extracts answers
        for a in answers:
            own_id = self._querier.get_container_own_id(a)
            body = self._querier.get_container_body(a)
            author_id = self._dao.get_user_id(self._querier.get_container_author(a))
            created_at = self._querier.get_container_created_at(a)
            votes = self._querier.get_container_votes(a)

            if self._querier.is_accepted_answer(a):
                message_type = "accepted_answer"
            else:
                message_type = "answer"

            answer_message_id = self._dao.select_message_id(own_id, topic_id)

            if answer_message_id:
                self._dao.update_message(own_id, topic_id, body, votes)
            else:
                self._dao.insert_message(own_id, self.pos, self._dao.get_message_type_id(message_type), topic_id,
                                         self._querier.remove_html_tags(body), votes, author_id, created_at)
                answer_message_id = self._dao.select_message_id(own_id, topic_id)

            self._dao.insert_message_dependency(message_id, answer_message_id)
            self._extract_attachments(body, answer_message_id)
            self.pos += 1

            self._extract_comment_messages(self._querier.get_comments(a), topic_id, answer_message_id)

    def _extract_comment_messages(self, comments, topic_id, message_id):
        # extracts comments
        for c in comments:
            own_id = self._querier.get_container_own_id(c)
            body = self._querier.get_container_body(c)
            author_id = self._dao.get_user_id(self._querier.get_container_author(c))
            created_at = self._querier.get_container_created_at(c)
            votes = self._querier.get_container_votes(c)

            comment_message_id = self._dao.select_message_id(own_id, topic_id)
            if comment_message_id:
                self._dao.update_message(own_id, topic_id, body, votes)
            else:
                self._dao.insert_message(own_id, self.pos, self._dao.get_message_type_id("comment"), topic_id,
                                         self._querier.remove_html_tags(body), votes, author_id, created_at)
                comment_message_id = self._dao.select_message_id(own_id, topic_id)

            self._dao.insert_message_dependency(message_id, comment_message_id)
            self._extract_attachments(body, comment_message_id)
            self.pos += 1

    def _extract_attachments(self, body, message_id):
        # extracts attachments
        attachments = self._querier.get_attachments(body)
        if attachments:
            self._insert_attachments(attachments, message_id)

    def _insert_labels(self, labels, topic_id):
        for l in labels:
            self._dao.insert_label(l)
            label_id = self._dao.select_label_id(l)
            self._dao.assign_label_to_topic(label_id, topic_id)

    def _insert_attachments(self, attachments, message_id):
        # inserts attachments
        pos = 0
        for attachment in attachments:
            attachment_name = self._querier.get_attachment_name(attachment)
            attachment_own_id = self._querier.generate_attachment_id(message_id, pos)
            attachment_url = self._querier.get_attachment_url(attachment)
            self._dao.insert_attachment(attachment_own_id, message_id, attachment_name, attachment_url)
            pos += 1

    def _extract_topic(self, topic):
        # extracts a topic
        last_change_at = self._querier.get_topic_last_change_at(topic)
        own_id = self._querier.get_container_own_id(topic)

        if self._dao.get_topic_last_change_at(own_id, self._forum_id) != last_change_at:
            name = self._querier.get_topic_name(topic)
            votes = self._querier.get_container_votes(topic)
            views = self._querier.get_topic_views(topic)
            created_at = self._querier.get_container_created_at(topic)

            topic_id = self._dao.insert_topic(own_id, self._forum_id, name, votes, views, created_at, last_change_at)
            author_id = self._dao.get_user_id(self._querier.get_container_author(topic))

            labels = self._querier.get_topic_labels(topic)
            self._insert_labels(labels, topic_id)

            self.pos = 0
            body = self._querier.get_container_body(topic)

            message_id = self._dao.select_message_id(own_id, topic_id)
            if message_id:
                self._dao.update_message(own_id, topic_id, self._querier.remove_html_tags(body), votes)
            else:
                self._dao.insert_message(own_id, self.pos, self._dao.get_message_type_id("question"), topic_id,
                                         self._querier.remove_html_tags(body),
                                         votes, author_id, created_at)
                message_id = self._dao.select_message_id(own_id, topic_id)
            self._extract_attachments(body, message_id)

            self.pos += 1

            self._extract_comment_messages(self._querier.get_comments(topic), topic_id, message_id)
            self._extract_answers(self._querier.get_answers(topic), topic_id, message_id)

    def extract(self):
        """
        extracts Stackoverflow topic data and stores it in the DB
        """
        try:
            self._logger.info("StackOverflowTopic2Db started")
            start_time = datetime.now()

            for topic_id in self._interval:
                topic = self._querier.get_topic(topic_id)
                if topic:
                    self._extract_topic(topic)

            end_time = datetime.now()

            minutes_and_seconds = self._logging_util.calculate_execution_time(end_time, start_time)
            self._logger.info("StackOverflowTopic2Db finished after " + str(minutes_and_seconds[0]) +
                              " minutes and " + str(round(minutes_and_seconds[1], 1)) + " secs")
            self._logging_util.remove_file_handler_logger(self._logger, self._fileHandler)
        except Exception:
            self._logger.error("StackOverflowTopic2Db failed", exc_info=True)
