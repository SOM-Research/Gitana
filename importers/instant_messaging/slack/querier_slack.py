#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'valerio cosentino'

import re
from slacker import Slacker

from util.date_util import DateUtil


class SlackQuerier():
    """
    This class collects the data available on the Eclipse forum viw Web scraping
    """

    def __init__(self, token, logger):
        """
        :type token: str
        :param token: the token to access the Slack API

        :type logger: Object
        :param logger: logger
        """
        try:
            self._token = token
            self._logger = logger
            self._date_util = DateUtil()
            self._slack = Slacker(self._token)
        except:
            self._logger.error("SlackQuerier init failed")
            raise

    def get_channel_ids(self, before_date, channels):
        """
        gets the data source channel ids

        :type before_date: str
        :param before_date: selects channels with creation date before a given date (YYYY-mm-dd)

        :type channels: list str
        :param channels: list of channels to retrieve
        """
        selected = []
        for channel in self._slack.channels.list().body['channels']:
            if channels:
                if self._get_channel_name(channel) in channels:
                    selected.append(channel)
            else:
                selected.append(channel)

        if before_date:
            selected = [c for c in selected
                        if self._date_util.get_timestamp(self._get_channel_created_at(c), "%Y-%m-%d %H:%M:%S")
                        <= self._date_util.get_timestamp(before_date, "%Y-%m-%d")]

        return [self._get_channel_id(c) for c in selected]

    def get_channel(self, channel_id):
        """
        gets the channel Object

        :type channel_id: int
        :param channel_id: the data source channel id
        """
        found = None
        for channel in self._slack.channels.list().body['channels']:
            if self._get_channel_id(channel) == channel_id:
                found = channel

        return found

    def _get_channel_id(self, channel):
        return channel.get("id")

    def _get_channel_name(self, channel):
        return channel.get("name").lower()

    def get_channel_description(self, channel):
        """
        gets the channel description

        :type channel: Object
        :param channel: the Object representing the channel
        """
        description = None

        if channel.get('topic'):
            topic = channel.get('topic').get('value').lower()

        if channel.get('purpose'):
            purpose = channel.get('purpose').get('value').lower()

        if topic and purpose:
            description = topic + " - " + purpose
        elif topic and not purpose:
            description = topic
        elif not topic and purpose:
            description = purpose

        return description

    def _get_channel_created_at(self, channel):
        return self._date_util.get_time_fromtimestamp(channel.get('created'), "%Y-%m-%d %H:%M:%S")

    def get_channel_last_change_at(self, channel):
        """
        gets the last change date of a channel

        :type channel: Object
        :param channel: the Object representing the channel
        """
        last_message = self.get_channel_messages(self._get_channel_id(channel))[-1]
        return self.get_message_created_at(last_message)

    def get_message_type(self, message):
        """
        gets the type of a message

        :type message: Object
        :param message: the Object representing the message
        """
        if message.get('subtype'):
            found = message.get('subtype').lower()
        else:
            found = message.get('type').lower()

        return found

    def get_url_attachments(self, body):
        """
        gets the attachment URLs

        :type body: str
        :param body: content of a message
        """
        p = re.compile("<http.*>")
        matches = p.findall(body)

        attachments = []
        for m in matches:
            attachments.append(m.strip('<').strip('>'))

        return attachments

    def generate_url_attachment_id(self, message_id, pos):
        """
        generates the id of an attachment URL

        :type message_id: int
        :param message_id: message id

        :type pos: int
        :param pos: message position
        """
        return str(message_id) + str(pos)

    def get_url_attachment_name(self, link):
        """
        gets the name of an attachment URL

        :type link: str
        :param link: attachment link
        """
        if link.endswith('/'):
            link = link.rstrip('/')
        return link.split('/')[-1]

    def get_url_attachment_extension(self, link):
        """
        gets the extension of an attachment URL

        :type link: str
        :param link: attachment link
        """
        candidate = link.split('.')[-1]

        found = 'html'

        if not candidate:
            if re.match('^\w+$', candidate):
                found = candidate

        return found

    def get_message_attachments(self, message):
        """
        gets the attachments within a message

        :type message: Object
        :param message: the Object representing the message
        """
        attachments = []
        if message.get('attachments'):
            for attachment in message.get('attachments'):
                attachments.append(attachment)

        return attachments

    def _resolve_mentions(self, text):
        p = re.compile("<@[A-Z0-9]+>")
        for hit in p.findall(text):
            stripped = hit.strip('<@').strip('>')
            try:
                info = self._slack.users.info(stripped)
                username = info.body.get('user').get('name')

                text = text.replace(hit, '@' + username)
            except:
                continue

        return text

    def get_message_body(self, message):
        """
        gets the body of a message

        :type message: Object
        :param message: the Object representing the message
        """
        text = message.get('text')
        if text.startswith('<@'):
            text = re.sub('@[A-Z0-9]+\|', '', text)

        text = self._resolve_mentions(text)

        return text

    def is_bot_message(self, message):
        """
        checks that a message is auto-generated

        :type message: Object
        :param message: the Object representing the message
        """
        bot_id = message.get('bot_id')
        return bot_id is not None

    def get_comment_message(self, message):
        """
        gets the comment of a message

        :type message: Object
        :param message: the Object representing the message
        """
        return message.get('comment')

    def get_comment_id(self, comment):
        """
        gets the id of a comment

        :type comment: Object
        :param comment: the Object representing the comment
        """
        return comment.get('id')

    def get_attachment_url(self, attachment):
        """
        gets the url of an attachment

        :type attachment: Object
        :param attachment: the Object representing the attachment
        """
        return attachment.get('from_url')

    def get_attachament_name(self, attachment):
        """
        gets the name of an attachment

        :type attachment: Object
        :param attachment: the Object representing the attachment
        """
        found = attachment.get('title')

        if not found:
            found = attachment.get('fallback')

        if not found:
            found = attachment.get('text')

        return found

    def get_attachment_extension(self, attachment):
        """
        gets the extension of an attachment

        :type attachment: Object
        :param attachment: the Object representing the attachment
        """
        url = self.get_attachment_url(attachment)
        return self.get_url_attachment_extension(url)

    def get_attachment_id(self, attachment):
        """
        gets the id of an attachment

        :type attachment: Object
        :param attachment: the Object representing the attachment
        """
        return attachment.get('id')

    def get_attachment_size(self, attachment):
        """
        gets the size (in bytes) of an attachment

        :type attachment: Object
        :param attachment: the Object representing the attachment
        """
        return attachment.get('image_bytes')

    def get_comment_body(self, comment):
        """
        gets the body of a comment

        :type comment: Object
        :param comment: the Object representing the comment
        """
        return comment.get('comment')

    def get_comment_created_at(self, comment):
        """
        gets the creation date of a comment

        :type comment: Object
        :param comment: the Object representing the comment
        """
        return self._date_util.get_time_fromtimestamp(comment.get('created'), "%Y-%m-%d %H:%M:%S")

    def get_message_own_id(self, message):
        """
        gets the data source id of a message

        :type message: Object
        :param message: the Object representing the message
        """
        return message.get('ts')

    def get_file_attachment(self, message):
        """
        gets the attachment of a message

        :type message: Object
        :param message: the Object representing the message
        """
        return message.get('file')

    def get_file_attachment_property(self, file, property):
        """
        gets a property of an attached file

        :type file: Object
        :param file: the Object representing the file

        :type property: str
        :param property: the string representing the property

        """
        return file.get(property)

    def file_attachment_get_comment(self, message):
        """
        gets the initial comment of an attached file

        :type message: Object
        :param message: the Object representing the message
        """
        file = self.get_file_attachment(message)
        return file.get('initial_comment')

    def get_message_created_at(self, message):
        """
        gets the creation date of a message

        :type message: message
        :param message: the Object representing the message
        """
        return self._date_util.get_time_fromtimestamp(int(message.get('ts').split(".")[0]), "%Y-%m-%d %H:%M:%S")

    def get_message_author_name(self, message):
        """
        gets the author of a message

        :type message: message
        :param message: the Object representing the message
        """
        try:
            info = self._slack.users.info(message.get('user'))
            found = info.body.get('user').get('name')
        except:
            found = None

        return found

    def get_message_author_email(self, message):
        """
        gets the author email of a message

        :type message: message
        :param message: the Object representing the message
        """
        try:
            info = self._slack.users.info(message.get('user'))
            user = info.body.get('user')
            if user.get('profile'):
                found = user.get('profile').get('email')
        except:
            found = None

        return found

    def get_channel_messages(self, channel_id):
        """
        gets the messages of a channel

        :type channel_id: int
        :param channel_id: the id of the channel
        """
        messages = self._slack.channels.history(channel_id).body['messages']
        last_message = messages[-1]
        previous_messages = self._slack.channels.history(channel_id, latest=last_message.get('ts')).body['messages']

        while not set([m.get('ts') for m in previous_messages]).issubset([m.get('ts') for m in messages]):
            messages = messages + previous_messages
            last_message = previous_messages[-1]
            previous_messages = self._slack.channels.history(channel_id, latest=last_message.get('ts')).body['messages']

        messages.reverse()
        return messages
