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

    def get_channels(self):
        channels = []
        for channel in self.slack.channels.list().body['channels']:
            channels.append(channel)

        return channels

    def get_channel_id(self, channel):
        return channel.get("id")

    def get_channel_name(self, channel):
        return channel.get("name")

    def get_channel_messages(self, channel_id):
        messages = self.slack.channels.history(channel_id).body['messages']
        last_message = messages[-1]
        previous_messages = self.channels.history(channel_id, latest=last_message.get('ts')).body['messages']

        while not set([m.get('ts') for m in previous_messages]).issubset([m.get('ts') for m in messages]):
            messages = messages + previous_messages
            last_message = previous_messages[-1]
            previous_messages = self.channels.history(channel_id, latest=last_message.get('ts')).body['messages']

        messages.reverse()
        return messages

    def get_message_content(self, message):
        return message.get('text')


