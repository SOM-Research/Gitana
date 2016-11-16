__author__ = 'valerio cosentino'

import pygal
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

    def create(self, query, x_label, y_label):
        intervals, counters = self.get_db_data(query)

        months = [self.date_util.get_month_from_int(i) for i in intervals]

        line_chart = pygal.Bar()
        line_chart.title = y_label + " * " + x_label
        line_chart.x_labels = months
        line_chart.add(y_label, counters)
        chart = line_chart.render()

        return chart