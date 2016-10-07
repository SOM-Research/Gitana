#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'valerio cosentino'

from datetime import datetime


class DateUtil():

    def get_timestamp(self, creation_time, format):
        return datetime.strptime(str(creation_time), format)