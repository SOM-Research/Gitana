#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'valerio cosentino'

import os
from datetime import datetime
import json
import errno
from util.dsl_util import DslUtil
from util.db_util import DbUtil
from util.logging_util import LoggingUtil
from exporters import resources
from exporters.graph.gexf_generator import GexfGenerator


class GraphExporter():
    """
    This class exports the Gitana data to a graph representation
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
        self._db_util = DbUtil()
        self._dsl_util = DslUtil()
        self._logging_util = LoggingUtil()
        self._log_path = log_root_path + "export-graph-" + db_name + ".log"
        self._logger = self._logging_util.get_logger(self._log_path)
        self._fileHandler = self._logging_util.get_file_handler(self._logger, self._log_path, "info")

        self._db_name = db_name

        self._config = config
        self._cnx = self._db_util.get_connection(self._config)

        self._db_util.set_database(self._cnx, self._db_name)
        self._db_util.set_settings(self._cnx)

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

    def _load_graph_exporter_json(self, json_path):
        # load the JSON that drives the graph exporter process
        with open(json_path) as json_data:
            data = json.load(json_data)

        return data.get('graph')

    def _get_parameter(self, key, parameters):
        # get JSON parameters
        found = None
        if key in ["EDGECOLOR", "NODECOLOR"]:
            found = parameters.get(key.lower())
        else:
            if key.endswith("ID"):
                name = parameters.get(key[:-2].lower())
                found = self._dsl_util.find_entity_id(self._cnx, key[:-2].lower(), name, self._logger)

        if not found:
            self._logger.error("GraphExporter: parameter " + str(key) + " not found!")

        return found

    def _load_query_json(self, metric_name, parameters):
        # loads the query stored in the JSON file
        with open(GraphExporter.INPUT_PATH) as json_data:
            data = json.load(json_data)

        metrics = data.get('queries')

        try:
            found = [m for m in metrics if m.get('name') == metric_name][0]
            nodes_query = found.get('nodes')
            edges_query = found.get('edges')

            for k in found.keys():
                if k not in ['name', 'edges', 'nodes']:

                    k_value = str(self._get_parameter(k, parameters))

                    nodes_query = nodes_query.replace(k, k_value)
                    edges_query = edges_query.replace(k, k_value)

            return (nodes_query, edges_query)
        except:
            self._logger.error("GraphExporter: metric " + str(metric_name) + " not found!")

    def export(self, file_path, json_path):
        """
        exports the Gitana data to a graph

        :type file_path: str
        :param file_path: the path where to export the graph

        :type json_path: str
        :param json_path: the path of the JSON that drives the export process
        """

        # gtype -> graph type = "undirected", "directed", if null "undirected"
        # gmode -> graph mode = "dynamic", "static", if null "dynamic"
        try:
            self._logger.info("GraphExporter started")
            start_time = datetime.now()

            exporter_data = self._load_graph_exporter_json(json_path)

            metric_name = exporter_data.get("name")
            parameters = exporter_data.get("params")

            (nodes_query, edges_query) = self._load_query_json(metric_name, parameters)

            gexf = GexfGenerator(self._cnx, self._logger)
            gexf.create(nodes_query, edges_query, parameters.get("type"), file_path)
            self._db_util.close_connection(self._cnx)

            end_time = datetime.now()
            minutes_and_seconds = self._logging_util.calculate_execution_time(end_time, start_time)
            self._logger.info("GraphExporter: process finished after " + str(minutes_and_seconds[0]) +
                              " minutes and " + str(round(minutes_and_seconds[1], 1)) + " secs")
            self._logging_util.remove_file_handler_logger(self._logger, self._fileHandler)
        except:
            self._logger.error("GraphExporter failed", exc_info=True)
