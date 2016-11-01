#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'valerio cosentino'

import sys
import re
from slacker import Slacker
sys.path.insert(0, "..//..//..")

from extractor.util.token_util import TokenUtil
from extractor.util.date_util import DateUtil


class SlackQuerier():

    def __init__(self, token, logger):
        self.token = token
        self.logger = logger
        self.token_util = TokenUtil()
        self.date_util = DateUtil()
        self.slack = Slacker(self.token)

    def get_channel_ids(self):
        channel_ids = []
        for channel in self.slack.channels.list().body['channels']:
            if self.get_channel_name(channel) == "ericssonmodelingdays":
                channel_ids.append(self.get_channel_id(channel))

        return channel_ids

    def get_channel(self, channel_id):
        found = None
        for channel in self.slack.channels.list().body['channels']:
            if self.get_channel_id(channel) == channel_id:
                found = channel

        return found

    def get_channel_id(self, channel):
        return channel.get("id")

    def get_channel_name(self, channel):
        return channel.get("name").lower()

    def get_channel_description(self, channel):
        description = None

        if channel.get('topic'):
            topic = channel.get('topic').get('value').lower()

        if channel.get('purpose'):
            purpose = channel.get('purpose').get('value').lower()

        if topic:
            description = topic

        if purpose:
            description = description + " - " + purpose

        return description

    def get_channel_created_at(self, channel):
        return self.date_util.get_time_fromtimestamp(channel.get('created'), "%Y-%m-%d %H:%M:%S")

    def get_channel_last_changed_at(self, channel):
        last_message = self.get_channel_messages(self.get_channel_id(channel))[-1]
        return self.get_message_created_at(last_message)

    def get_channel_own_id(self, channel):
        return channel.get('id')

    def get_message_type(self, message):
        if message.get('subtype'):
            found = message.get('subtype').lower()
        else:
            found = message.get('type').lower()

        return found

    def get_url_attachments(self, body):
        p = re.compile("<http.*>")
        matches = p.findall(body)

        attachments = []
        for m in matches:
            attachments.append(m.strip('<').strip('>'))

        return attachments

    def generate_url_attachment_id(self, message_id, pos):
        return str(message_id) + str(pos)

    def get_url_attachment_name(self, link):
        if link.endswith('/'):
            link = link.rstrip('/')
        return link.split('/')[-1]

    def get_url_attachment_extension(self, link):
        candidate = link.split('.')[-1]

        found = 'html'

        if not candidate:
            if re.match('^\w+$', candidate):
                found = candidate

        return found

    def get_message_attachments(self, message):
        attachments = []
        if message.get('attachments'):
            for attachment in message.get('attachments'):
                attachments.append(attachment)

        return attachments

    def resolve_mentions(self, text):
        p = re.compile("<@[A-Z0-9]+>")
        for hit in p.findall(text):
            stripped = hit.strip('<@').strip('>')
            try:
                info = self.slack.users.info(stripped)
                username = info.body.get('user').get('name')

                text = text.replace(hit, '@' + username)
            except:
                continue

        return text

    def get_message_body(self, message):
        text = message.get('text')
        if text.startswith('<@'):
            text = re.sub('@[A-Z0-9]+\|', '', text)

        text = self.resolve_mentions(text)

        return text

    def get_comment_message(self, message):
        return message.get('comment')

    def get_comment_id(self, comment):
        return comment.get('id')

    def get_attachment_url(self, attachment):
        return attachment.get('from_url')

    def get_attachament_name(self, attachment):
        found = attachment.get('text')

        if not found:
            found = attachment.get('title')

        if not found:
            found = attachment.get('fallback')

        return found

    def get_attachment_extension(self, attachment):
        url = self.get_attachment_url(attachment)
        return self.get_url_attachment_extension(url)

    def get_attachment_id(self, attachment):
        return attachment.get('id')

    def get_attachment_size(self, attachment):
        return attachment.get('image_bytes')

    def get_comment_body(self, comment):
        return comment.get('comment')

    def get_comment_created_at(self, comment):
        return self.date_util.get_time_fromtimestamp(comment.get('created'), "%Y-%m-%d %H:%M:%S")

    def get_comment_author_name(self, comment):
        return comment.get('user')

    def get_message_own_id(self, message):
        return message.get('ts')

    def get_file_attachment(self, message):
        return message.get('file')

    def get_file_attachment_property(self, file, property):
        return file.get(property)

    def file_attachment_get_comment(self, message):
        file = self.get_file_attachment(message)
        return file.get('initial_comment')

    def get_message_created_at(self, message):
        return self.date_util.get_time_fromtimestamp(int(message.get('ts').split(".")[0]), "%Y-%m-%d %H:%M:%S")

    def get_message_author_name(self, message):
        info = self.slack.users.info(message.get('user'))
        try:
            found = info.body.get('user').get('name')
        except:
            found = None

        return found

    def get_message_author_email(self, message):
        info = self.slack.users.info(message.get('user'))
        try:
            user = info.body.get('user')
            if user.get('profile'):
                found = user.get('profile').get('email')
        except:
            found = None

        return found

    def get_channel_messages(self, channel_id):
        messages = self.slack.channels.history(channel_id).body['messages']
        last_message = messages[-1]
        previous_messages = self.slack.channels.history(channel_id, latest=last_message.get('ts')).body['messages']

        while not set([m.get('ts') for m in previous_messages]).issubset([m.get('ts') for m in messages]):
            messages = messages + previous_messages
            last_message = previous_messages[-1]
            previous_messages = self.slack.channels.history(channel_id, latest=last_message.get('ts')).body['messages']

        messages.reverse()
        return messages

    def get_message_content(self, message):
        return message.get('text')


