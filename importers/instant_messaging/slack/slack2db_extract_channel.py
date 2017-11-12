#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'valerio cosentino'

from datetime import datetime

from querier_slack import SlackQuerier
from slack_dao import SlackDao
from util.logging_util import LoggingUtil


class SlackChannel2Db(object):
    """
    This class handles the import of Slack channels
    """

    def __init__(self, db_name, instant_messaging_id, interval, token,
                 config, log_root_path):
        """
        :type db_name: str
        :param db_name: the name of an existing DB

        :type instant_messaging_id: int
        :param instant_messaging_id: the id of an existing instant messaging in the DB

        :type interval: list int
        :param interval: a list of channel ids to import

        :type token: str
        :param token: a Slack token

        :type config: dict
        :param config: the DB configuration file

        :type log_root_path: str
        :param log_root_path: the log path
        """

        self._log_root_path = log_root_path
        self._interval = interval
        self._db_name = db_name
        self._instant_messaging_id = instant_messaging_id
        self._token = token
        self._config = config

        self._logging_util = LoggingUtil()

        self._fileHandler = None
        self._logger = None
        self._querier = None
        self._dao = None

    def __call__(self):
        try:
            log_path = self._log_root_path + "-channel2db-" + str(self._interval[0]) + "-" + str(self._interval[-1])
            self._logger = self._logging_util.get_logger(log_path)
            self._fileHandler = self._logging_util.get_file_handler(self._logger, log_path, "info")

            self._querier = SlackQuerier(self._token, self._logger)
            self._dao = SlackDao(self._config, self._logger)
            self.extract()
        except Exception:
            self._logger.error("Channel2Db failed", exc_info=True)
        finally:
            if self._dao:
                self._dao.close_connection()

    def _insert_not_recognized_url_attachments(self, message_id, urls):
        # insert not recognized url attachments
        pos = 0
        for url in urls:
            attachment_own_id = self._querier.generate_url_attachment_id(message_id, pos)
            attachment_name = self._querier.get_url_attachment_name(url)
            attachment_extension = self._querier.get_url_attachment_extension(url)
            self._dao.insert_url_attachment(attachment_own_id, message_id, attachment_name, attachment_extension, url)

        pos += 1

    def _extract_file_attachment_info(self, message, message_id):
        # insert file attachments
        file = self._querier.get_file_attachment(message)
        own_id = self._querier.get_file_attachment_property(file, "id")
        name = self._querier.get_file_attachment_property(file, "name")
        extension = self._querier.get_file_attachment_property(file, "filetype")
        url = self._querier.get_file_attachment_property(file, "permalink")
        bytes = self._querier.get_file_attachment_property(file, "size")

        self._dao.insert_attachment(own_id, message_id, name, extension, bytes, url)

    def _extract_url_attachments(self, message, message_id):
        # insert URL attachments
        urls = self._querier.get_url_attachments(self._querier.get_message_body(message))
        attachments = self._querier.get_message_attachments(message)

        for a in attachments:
            url = self._querier.get_attachment_url(a)
            name = self._querier.get_attachament_name(a)
            own_id = self._querier.get_attachment_id(a)
            extension = self._querier.get_attachment_extension(a)
            bytes = self._querier.get_attachment_size(a)
            self._dao.insert_attachment(own_id, message_id, name, extension, bytes, url)

            if url in urls:
                urls.remove(a.get('from_url'))

        self._insert_not_recognized_url_attachments(message_id, urls)

    def _extract_file_comment(self, channel_id, comment, pos):
        # insert file comment
        own_id = self._querier.get_comment_id(comment)
        body = self._querier.get_comment_body(comment)
        created_at = self._querier.get_comment_created_at(comment)
        author_name = self._querier.get_message_author_name(comment)
        author_email = self._querier.get_message_author_email(comment)
        author_id = self._dao.get_user_id(author_name, author_email)

        self._dao.insert_message(own_id, pos, self._dao.get_message_type_id("comment"), channel_id, body,
                                 author_id, created_at)
        comment_id = self._dao.select_message_id(own_id, channel_id)
        return comment_id

    def _extract_comment(self, message, channel_id):
        # insert comment
        pos = 0
        message_id = None

        initial_comment = self._querier.file_attachment_get_comment(message)
        if initial_comment:
            own_id = self._querier.get_comment_id(initial_comment)
            message_id = self._dao.select_message_id(own_id, channel_id)
            pos = self._dao.get_comments(message_id)

        comment = self._querier.get_comment_message(message)
        comment_id = self._extract_file_comment(channel_id, comment, pos)

        if message_id:
            self._dao.insert_message_dependency(comment_id, message_id)

    def _extract_message(self, message, channel_id, type, pos):
        # insert message
        author_name = self._querier.get_message_author_name(message)
        author_email = self._querier.get_message_author_email(message)
        author_id = self._dao.get_user_id(author_name, author_email)
        body = self._querier.get_message_body(message)
        own_id = self._querier.get_message_own_id(message)
        created_at = self._querier.get_message_created_at(message)

        if type == "message":
            message_type = "reply"
        else:
            message_type = "info"

        self._dao.insert_message(own_id, pos, self._dao.get_message_type_id(message_type), channel_id, body,
                                 author_id, created_at)
        message_id = self._dao.select_message_id(own_id, channel_id)
        self._extract_url_attachments(message, message_id)

    def _extract_file_upload(self, message, channel_id, pos):
        # insert file upload
        own_id = self._querier.get_message_own_id(message)
        author_name = self._querier.get_message_author_name(message)
        author_email = self._querier.get_message_author_email(message)
        author_id = self._dao.get_user_id(author_name, author_email)
        created_at = self._querier.get_message_created_at(message)
        body = self._querier.get_message_body(message).split(':')[0]

        self._dao.insert_message(own_id, pos, self._dao.get_message_type_id("file_upload"), channel_id, body,
                                 author_id, created_at)
        message_id = self._dao.select_message_id(own_id, channel_id)
        self._extract_file_attachment_info(message, message_id)

        comment = self._querier.file_attachment_get_comment(message)
        if comment:
            comment_id = self._extract_file_comment(channel_id, comment, 0)
            self._dao.insert_message_dependency(comment_id, message_id)

    def _extract_messages(self, channel_id, channel_own_id):
        # insert messages
        pos = 0
        for message in self._querier.get_channel_messages(channel_own_id):
            type = self._querier.get_message_type(message)

            if type == "file_comment":
                self._extract_comment(message, channel_id)
            elif type == "file_share":
                self._extract_file_upload(message, channel_id, pos)
                pos += 1
            else:
                if not self._querier.is_bot_message(message):
                    self._extract_message(message, channel_id, type, pos)
                # TODO deal with bot messages
                pos += 1

    def extract(self):
        """
        extracts Slack channel data and stores it in the DB
        """
        try:
            self._logger.info("SlackChannel2Db started")
            start_time = datetime.now()
            for channel_id in self._interval:
                channel_own_id = self._dao.select_channel_own_id(channel_id, self._instant_messaging_id)
                self._extract_messages(channel_id, channel_own_id)

            end_time = datetime.now()
            minutes_and_seconds = self._logging_util.calculate_execution_time(end_time, start_time)
            self._logger.info("SlackChannel2Db finished after " + str(minutes_and_seconds[0]) +
                              " minutes and " + str(round(minutes_and_seconds[1], 1)) + " secs")
            self._logging_util.remove_file_handler_logger(self._logger, self._fileHandler)
        except Exception:
            self._logger.error("SlackChannel2Db failed", exc_info=True)
