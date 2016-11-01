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

    def __call__(self):
        LOG_FILENAME = self.log_path + "-channel2db"
        self.logger = logging.getLogger(LOG_FILENAME)
        fileHandler = logging.FileHandler(LOG_FILENAME + "-" + str(self.interval[0]) + "-" + str(self.interval[-1]) + ".log", mode='w')
        formatter = logging.Formatter("%(asctime)s:%(levelname)s:%(message)s", "%Y-%m-%d %H:%M:%S")

        fileHandler.setFormatter(formatter)
        self.logger.setLevel(logging.INFO)
        self.logger.addHandler(fileHandler)

        try:
            self.querier = SlackQuerier(self.token, self.logger)
            self.dao = SlackDao(self.config, self.logger)
            self.extract()
        except Exception, e:
            self.logger.error("Channel2Db failed", exc_info=True)

    def insert_not_recognized_url_attachments(self, message_id, urls):
        pos = 0
        for url in urls:
            attachment_own_id = self.querier.generate_url_attachment_id(message_id, pos)
            attachment_name = self.querier.get_url_attachment_name(url)
            attachment_extension = self.querier.get_url_attachment_extension(url)
            self.dao.insert_url_attachment(attachment_own_id, message_id, attachment_name, attachment_extension, url)

        pos += 1

    def extract_file_attachment_info(self, message, message_id):
        file = self.querier.get_file_attachment(message)
        own_id = self.querier.get_file_attachment_property(file, "id")
        name = self.querier.get_file_attachment_property(file, "name")
        extension = self.querier.get_file_attachment_property(file, "filetype")
        url = self.querier.get_file_attachment_property(file, "permalink")
        bytes = self.querier.get_file_attachment_property(file, "size")

        self.dao.insert_attachment(own_id, message_id, name, extension, bytes, url)

    def extract_url_attachments(self, message, message_id):
        urls = self.querier.get_url_attachments(self.querier.get_message_body(message))
        attachments = self.querier.get_message_attachments(message)

        for a in attachments:
            url = self.querier.get_attachment_url(a)
            name = self.querier.get_attachament_name(a)
            own_id = self.querier.get_attachment_id(a)
            extension = self.querier.get_attachment_extension(a)
            bytes = self.querier.get_attachment_size(a)
            self.dao.insert_attachment(own_id, message_id, name, extension, bytes, url)

            if url in urls:
                urls.remove(a.get('from_url'))

        self.insert_not_recognized_url_attachments(message_id, urls)

    def extract_file_comment(self, channel_id, comment, pos):
        own_id = self.querier.get_comment_id(comment)
        body = self.querier.get_comment_body(comment)
        created_at = self.querier.get_comment_created_at(comment)
        author_name = self.querier.get_message_author_name(comment)
        author_email = self.querier.get_message_author_email(comment)
        author_id = self.dao.get_user_id(author_name, author_email)

        self.dao.insert_message(own_id, pos, self.dao.get_message_type_id("comment"), channel_id, body, author_id, created_at)
        comment_id = self.dao.select_message_id(own_id, channel_id)
        return comment_id

    def extract_comment(self, message, channel_id):
        pos = 0
        message_id = None

        initial_comment = self.querier.file_attachment_get_comment(message)
        if initial_comment:
            own_id = self.querier.get_comment_id(initial_comment)
            message_id = self.dao.select_message_id(own_id, channel_id)
            pos = self.dao.get_comments(message_id)

        comment = self.querier.get_comment_message(message)
        comment_id = self.extract_file_comment(channel_id, comment, pos)

        if message_id:
            self.dao.insert_message_dependency(comment_id, message_id)

    def extract_message(self, message, channel_id, type, pos):
        own_id = self.querier.get_message_own_id(message)
        author_name = self.querier.get_message_author_name(message)
        author_email = self.querier.get_message_author_email(message)
        author_id = self.dao.get_user_id(author_name, author_email)
        created_at = self.querier.get_message_created_at(message)
        body = self.querier.get_message_body(message)

        if type == "message":
            message_type = "reply"
        else:
            message_type = "info"

        self.dao.insert_message(own_id, pos, self.dao.get_message_type_id(message_type), channel_id, body, author_id, created_at)
        message_id = self.dao.select_message_id(own_id, channel_id)
        self.extract_url_attachments(message, message_id)

    def extract_file_upload(self, message, channel_id, pos):
        own_id = self.querier.get_message_own_id(message)
        author_name = self.querier.get_message_author_name(message)
        author_email = self.querier.get_message_author_email(message)
        author_id = self.dao.get_user_id(author_name, author_email)
        created_at = self.querier.get_message_created_at(message)
        body = self.querier.get_message_body(message).split(':')[0]

        self.dao.insert_message(own_id, pos, self.dao.get_message_type_id("file_upload"), channel_id, body, author_id, created_at)
        message_id = self.dao.select_message_id(own_id, channel_id)
        self.extract_file_attachment_info(message, message_id)

        comment = self.querier.file_attachment_get_comment(message)
        if comment:
            comment_id = self.extract_file_comment(channel_id, comment, 0)
            self.dao.insert_message_dependency(comment_id, message_id)

    def extract_messages(self, channel_id, channel_own_id):
        pos = 0
        for message in self.querier.get_channel_messages(channel_own_id):
            type = self.querier.get_message_type(message)

            if type == "file_comment":
                self.extract_comment(message, channel_id)
            elif type == "file_share":
                self.extract_file_upload(message, channel_id, pos)
                pos += 1
            else:
                self.extract_message(message, channel_id, type, pos)
                pos += 1

    def extract_channel(self, channel):
        own_id = self.querier.get_channel_id(channel)
        name = self.querier.get_channel_name(channel)
        description = self.querier.get_channel_description(channel)
        created_at = self.querier.get_channel_created_at(channel)

        channel_id = self.dao.insert_channel(own_id, self.instant_messaging_id, name, description, created_at, None)

        self.extract_messages(channel_id, own_id)

    def extract(self):
        try:
            start_time = datetime.now()

            for channel_id in self.interval:
                channel = self.querier.get_channel(channel_id)
                self.extract_channel(channel)

            end_time = datetime.now()

            minutes_and_seconds = divmod((end_time-start_time).total_seconds(), 60)
            self.logger.info("SlackChannel2Db finished after " + str(minutes_and_seconds[0])
                           + " minutes and " + str(round(minutes_and_seconds[1], 1)) + " secs")
        except Exception, e:
            self.logger.error("SlackChannel2Db failed", exc_info=True)