#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'valerio cosentino'

import codecs
import logging
import logging.handlers
import os
from datetime import datetime
import json
import uuid
import errno
from util.dsl_util import DslUtil
from util.date_util import DateUtil
from util.db_util import DbUtil
from exporter.report.chart_generator import ChartGenerator
from exporter.report.html_generator import HtmlGenerator

from exporter import resources

LOG_FOLDER_PATH = "logs"
LOG_NAME = "gitana-report-exporter"
INPUT_PATH = os.path.dirname(resources.__file__) + "\queries.json"


class ReportExporter():
    def __init__(self, config, db_name, log_folder_path):
        if log_folder_path:
            self.create_log_folder(log_folder_path)
            self.log_folder_path = log_folder_path
        else:
            self.create_log_folder(LOG_FOLDER_PATH)
            self.log_folder_path = LOG_FOLDER_PATH

        self.dsl_util = DslUtil()
        self.date_util = DateUtil()
        self.db_util = DbUtil()

        self.log_path = self.log_folder_path + "/" + LOG_NAME + "-" + str(uuid.uuid4())[:5] + ".log"
        self.logger = logging.getLogger(self.log_path)
        fileHandler = logging.FileHandler(self.log_path, mode='w')
        formatter = logging.Formatter("%(asctime)s:%(levelname)s:%(message)s", "%Y-%m-%d %H:%M:%S")

        fileHandler.setFormatter(formatter)
        self.logger.setLevel(logging.INFO)
        self.logger.addHandler(fileHandler)

        self.db_name = db_name

        self.config = config
        self.cnx = self.db_util.get_connection(self.config)

        self.set_database()
        self.set_settings()

        self.chart_generator = ChartGenerator(self.cnx, self.logger)
        self.html_generator = HtmlGenerator(self.logger)

    def create_log_folder(self, name):
        if not os.path.exists(name):
            os.makedirs(name)

    def create_output_file(self, filename):
        if not os.path.exists(os.path.dirname(filename)):
            try:
                os.makedirs(os.path.dirname(filename))
            except OSError as exc: # Guard against race condition
                if exc.errno != errno.EEXIST:
                    raise


    def set_database(self):
        cursor = self.cnx.cursor()
        use_database = "USE " + self.db_name
        cursor.execute(use_database)
        cursor.close()

    def set_settings(self):
        cursor = self.cnx.cursor()
        cursor.execute("set global innodb_file_format = BARRACUDA")
        cursor.execute("set global innodb_file_format_max = BARRACUDA")
        cursor.execute("set global innodb_large_prefix = ON")
        cursor.execute("set global character_set_server = utf8")
        cursor.close()

    def load_report_exporter_json(self, json_path):
        with open(json_path) as json_data:
            data = json.load(json_data)

        return data.get('report')

    def find_entity_id(self, type, name):
        found = None

        if type == "project":
            found = self.db_util.select_project_id(self.cnx, name, self.logger)
        elif type == "repo":
            found = self.db_util.select_repo_id(self.cnx, name, self.logger)
        elif type == "issuetracker":
            found = self.db_util.select_issue_tracker_id(self.cnx, name, self.logger)
        elif type == "forum":
            found = self.db_util.select_forum_id(self.cnx, name, self.logger)
        elif type == "instantmessaging":
            found = self.db_util.select_instant_messaging_id(self.cnx, name, self.logger)

        if not found:
            self.logger.error("ReporExporter: entity " + str(type) + " with name " + str(name) + " not found!")

        return found

    def get_parameter(self, key, parameters):
        found = None
        if key in ["AFTERDATE", "INTERVAL"]:
            found = parameters.get(key.lower())
        else:
            if key.endswith("ID"):
                found = parameters.get(key[:-2].lower())
        if not found:
            self.logger.error("ReportExporter: parameter " + str(key) + " not found!")

        return found

    def load_query_json(self, metric_name, parameters):
        with open(INPUT_PATH) as json_data:
            data = json.load(json_data)

        metrics = data.get('queries')

        try:
            found = [m for m in metrics if m.get('name') == metric_name][0]
            query = found.get('query')

            for k in found.keys():
                if k not in ['name', 'query']:

                    k_value = str(self.get_parameter(k, parameters))

                    query = query.replace(k, k_value)

            return query
        except:
            self.logger.error("ReportExporter: metric " + str(metric_name) + " not found!")

    def get_activity_name(self, activity):
        return activity.replace("_", " ")

    def get_activity_type(self, activity):
        return activity.replace("_activity", "").replace("_", "")

    def generate_charts(self, activity, activity_data, project_id, time_span):
        entity2charts = {}
        after_date, interval = self.calculate_time_information(time_span)
        activity_type = self.get_activity_type(activity)
        names = activity_data.get('names')
        measures = activity_data.get('measures')

        for entity_name in names:
            entity_id = self.dsl_util.find_entity_id(self.cnx, activity_type, entity_name, self.logger)
            charts = []
            for measure in measures:
                query = self.load_query_json(measure, {activity_type: entity_id, 'project': project_id, 'afterdate': after_date, 'interval': interval})
                charts.append(self.chart_generator.create(query, interval.lower(), measure, time_span))

            entity2charts.update({entity_name: charts})

        return entity2charts

    def calculate_time_information(self, time_span):
        start = None
        interval = None
        current_time = datetime.now() #test datetime.strptime("2015-10-10", "%Y-%m-%d")
        if time_span == "this_week":
            start = self.date_util.get_start_time_span(current_time, "week", "%Y-%m-%d")
            interval = "DAY"
        elif time_span == "this_month":
            start = self.date_util.get_start_time_span(current_time, "month", "%Y-%m-%d")
            interval = "DAY"
        elif time_span == "this_year":
            start = self.date_util.get_start_time_span(current_time, "year", "%Y-%m-%d")
            interval = "MONTH"
        else:
            self.logger.error("ReportExporter: time span " + str(time_span) + " not recognized! Options are: this_week, this_month, this_year")

        return start, interval

    def export(self, file_path, json_path):
        start_time = datetime.now()

        exporter_data = self.load_report_exporter_json(json_path)

        project_name = exporter_data.get('project')
        project_id = self.dsl_util.find_entity_id(self.cnx, "project", project_name, self.logger)

        time_span = exporter_data.get('time_span')

        activity2charts = {}
        for activity in [attr for attr in exporter_data.keys() if attr.endswith('activity')]:
            activity_name = self.get_activity_name(activity)
            charts = self.generate_charts(activity, exporter_data.get(activity), project_id, time_span)
            activity2charts.update({activity_name: charts})

        html_page = self.html_generator.create(project_name, activity2charts)

        with codecs.open(file_path,'w',encoding='utf8') as f:
            f.write(html_page)

        self.db_util.close_connection(self.cnx)
        end_time = datetime.now()

        minutes_and_seconds = divmod((end_time - start_time).total_seconds(), 60)
        self.logger.info("GexfExporter: process finished after " + str(minutes_and_seconds[0])
                         + " minutes and " + str(round(minutes_and_seconds[1], 1)) + " secs")