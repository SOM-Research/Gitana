#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'valerio cosentino'

import calendar
from datetime import datetime, timedelta


class DateUtil():

    def get_month_from_int(self, month_int):
        return calendar.month_name[month_int]

    def get_weekday_from_int(self, day_int):
        return calendar.day_name[day_int]

    def get_start_time_span(self, reference_time, time_unit, format):
        start_time = None
        if time_unit == "week":
            start_time = reference_time - timedelta(days=reference_time.weekday())
        elif time_unit == "month":
            start_time = reference_time - timedelta(days=reference_time.day - 1)
        elif time_unit == "year":
            start_time = reference_time - timedelta(days=reference_time.timetuple().tm_yday - 1)

        if start_time:
            start_time = start_time.strftime(format)

        return start_time

    def get_timestamp(self, creation_time, format):
        return datetime.strptime(str(creation_time), format)

    def get_time_fromtimestamp(self, creation_time, format):
        try:
            time = datetime.fromtimestamp(creation_time).strftime(format)
        except:
            time = None

        return time