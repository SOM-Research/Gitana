#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'valerio cosentino'

import pygal
from pygal.style import LightColorizedStyle
from util.date_util import DateUtil


class ChartGenerator():

    def __init__(self, cnx, logger):
        self.cnx = cnx
        self.logger = logger
        self.date_util = DateUtil()

    def get_db_data(self, query):
        cursor = self.cnx.cursor()
        cursor.execute(query)

        results_y = []
        results_x = []
        row = cursor.fetchone()
        while row:
            counter = int(row[0])
            span = int(row[1])
            results_y.append(counter)
            results_x.append(span)
            row = cursor.fetchone()

        cursor.close()

        return results_x, results_y

    def create(self, query, x_label, y_label, time_dimension):
        intervals, counters = self.get_db_data(query)

        if "year" in time_dimension:
            span = [self.date_util.get_month_from_int(i) for i in intervals]
        elif "month" in time_dimension:
            span = intervals
        elif "week" in time_dimension:
            span = [self.date_util.get_weekday_from_int(i-1) for i in intervals if i <= 7]

        if '_' in y_label:
            y_label = y_label.replace('_', ' ')

        line_chart = pygal.Bar(style=LightColorizedStyle)
        line_chart.title = y_label + " * " + x_label
        line_chart.x_labels = span
        line_chart.add(y_label, counters)
        chart = line_chart.render()

        return chart