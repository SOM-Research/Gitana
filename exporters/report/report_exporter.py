#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'valerio cosentino'

import codecs
import os
from datetime import datetime
import json
import errno
from util.dsl_util import DslUtil
from util.date_util import DateUtil
from util.db_util import DbUtil
from util.logging_util import LoggingUtil
from exporters.report.chart_generator import ChartGenerator
from exporters.report.html_generator import HtmlGenerator

from exporters import resources


class ActivityReportExporter():
    """
    This class handles the generation of reports
    """

    LOG_FOLDER_PATH = "logs"
    INPUT_PATH = os.path.join(os.path.dirname(resources.__file__), 'queries.json')

    def __init__(self, config, db_name, log_root_path):
        """
        :type config: dict
        :param config: the DB configuration file

        :type db_name: str
        :param config: name of an existing DB

        :type log_root_path: str
        :param log_root_path: the log path
        """
        self._dsl_util = DslUtil()
        self._date_util = DateUtil()
        self._db_util = DbUtil()

        self._logging_util = LoggingUtil()
        self._log_path = log_root_path + "export-report-" + db_name + ".log"
        self._logger = self._logging_util.get_logger(self._log_path)
        self._fileHandler = self._logging_util.get_file_handler(self._logger, self._log_path, "info")

        self._db_name = db_name
        self._config = config
        self._cnx = self._db_util.get_connection(self._config)
        self._db_util.set_database(self._cnx, self._db_name)
        self._db_util.set_settings(self._cnx)

        self._chart_generator = ChartGenerator(self._cnx, self._logger)
        self._html_generator = HtmlGenerator(self._logger)

    def _create_log_folder(self, name):
        # creates the log folder
        if not os.path.exists(name):
            os.makedirs(name)

    def _create_output_file(self, filename):
        # creates the output folder
        if not os.path.exists(os.path.dirname(filename)):
            try:
                os.makedirs(os.path.dirname(filename))
            except OSError as exc:  # Guard against race condition
                if exc.errno != errno.EEXIST:
                    raise

    def _load_report_exporter_json(self, json_path):
        # loads the JSON that drives the report export process
        with open(json_path) as json_data:
            data = json.load(json_data)

        return data.get('report')

    def _find_entity_id(self, type, name):
        # finds the id of the tools stored in the DB
        found = None

        if type == "project":
            found = self._db_util.select_project_id(self._cnx, name, self._logger)
        elif type == "repo":
            found = self._db_util.select_repo_id(self._cnx, name, self._logger)
        elif type == "issuetracker":
            found = self._db_util.select_issue_tracker_id(self._cnx, name, self._logger)
        elif type == "forum":
            found = self._db_util.select_forum_id(self._cnx, name, self._logger)
        elif type == "instantmessaging":
            found = self._db_util.select_instant_messaging_id(self._cnx, name, self._logger)

        if not found:
            self._logger.error("ReporExporter: entity " + str(type) + " with name " + str(name) + " not found!")

        return found

    def _get_parameter(self, key, parameters):
        # gets parameters of the JSON
        found = None
        if key in ["AFTERDATE", "INTERVAL"]:
            found = parameters.get(key.lower())
        else:
            if key.endswith("ID"):
                found = parameters.get(key[:-2].lower())
        if not found:
            self._logger.error("ReportExporter: parameter " + str(key) + " not found!")

        return found

    def _load_query_json(self, metric_name, parameters):
        # loads the queries in the JSON configuration file
        with open(ActivityReportExporter.INPUT_PATH) as json_data:
            data = json.load(json_data)

        metrics = data.get('queries')

        try:
            found = [m for m in metrics if m.get('name') == metric_name][0]
            query = found.get('query')

            for k in found.keys():
                if k not in ['name', 'query']:

                    k_value = str(self._get_parameter(k, parameters))

                    query = query.replace(k, k_value)

            return query
        except:
            self._logger.error("ReportExporter: metric " + str(metric_name) + " not found!")

    def _get_activity_name(self, activity):
        # gets the name of the activity
        return activity.replace("_", " ")

    def _get_activity_type(self, activity):
        # gets the type of the activity
        return activity.replace("_activity", "").replace("_", "")

    def _generate_charts(self, activity, activity_data, project_id, time_span):
        # generates charts
        entity2charts = {}
        after_date, interval = self._calculate_time_information(time_span)
        activity_type = self._get_activity_type(activity)
        names = activity_data.get('names')
        measures = activity_data.get('measures')

        for entity_name in names:
            entity_id = self._dsl_util.find_entity_id(self._cnx, activity_type, entity_name, self._logger)
            charts = []
            for measure in measures:
                query = self._load_query_json(measure, {activity_type: entity_id, 'project': project_id,
                                                        'afterdate': after_date, 'interval': interval})
                charts.append(self._chart_generator.create(query, interval.lower(), measure, time_span))

            entity2charts.update({entity_name: charts})

        return entity2charts

    def _calculate_time_information(self, time_span):
        # calculates the time span information
        start = None
        interval = None
        current_time = datetime.now()  # test datetime.strptime("2015-10-10", "%Y-%m-%d")
        if time_span == "this_week":
            start = self._date_util.get_start_time_span(current_time, "week", "%Y-%m-%d")
            interval = "DAY"
        elif time_span == "this_month":
            start = self._date_util.get_start_time_span(current_time, "month", "%Y-%m-%d")
            interval = "DAY"
        elif time_span == "this_year":
            start = self._date_util.get_start_time_span(current_time, "year", "%Y-%m-%d")
            interval = "MONTH"
        else:
            self._logger.error("ReportExporter: time span " + str(time_span) +
                               " not recognized! Options are: this_week, this_month, this_year")

        return start, interval

    def export(self, file_path, json_path):
        """
        exports the Gitana data to a report

        :type file_path: str
        :param file_path: the path where to export the report

        :type json_path: str
        :param json_path: the path of the JSON that drives the export process
        """
        try:
            self._logger.info("ReportExporter started")
            start_time = datetime.now()

            exporter_data = self._load_report_exporter_json(json_path)

            project_name = exporter_data.get('project')
            project_id = self._dsl_util.find_entity_id(self._cnx, "project", project_name, self._logger)

            time_span = exporter_data.get('time_span')

            activity2charts = {}
            for activity in [attr for attr in exporter_data.keys() if attr.endswith('activity')]:
                activity_name = self._get_activity_name(activity)
                charts = self._generate_charts(activity, exporter_data.get(activity), project_id, time_span)
                activity2charts.update({activity_name: charts})

            html_page = self._html_generator.create(project_name, activity2charts)

            with codecs.open(file_path, 'w', encoding='utf8') as f:
                f.write(html_page)

            self._db_util.close_connection(self._cnx)

            end_time = datetime.now()
            minutes_and_seconds = self._logging_util.calculate_execution_time(end_time, start_time)
            self._logger.info("ReportExporter: process finished after " + str(minutes_and_seconds[0]) +
                              " minutes and " + str(round(minutes_and_seconds[1], 1)) + " secs")
            self._logging_util.remove_file_handler_logger(self._logger, self._fileHandler)
        except:
            self._logger.error("ReportExporter failed", exc_info=True)
