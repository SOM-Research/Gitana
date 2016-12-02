#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'valerio cosentino'

import networkx as nx
import mysql.connector
from mysql.connector import errorcode
import logging
import logging.handlers
import os
from datetime import datetime
import json
import uuid
import errno
from util.dsl_util import DslUtil
from util.db_util import DbUtil

from exporter import resources
from exporter.graph.gexf_generator import GexfGenerator


LOG_FOLDER_PATH = "logs"
LOG_NAME = "gitana-graph-exporter"
INPUT_PATH = os.path.dirname(resources.__file__) + "\queries.json"


class GraphExporter():
    def __init__(self, config, db_name, log_folder_path):
        if log_folder_path:
            self.create_log_folder(log_folder_path)
            self.log_folder_path = log_folder_path
        else:
            self.create_log_folder(LOG_FOLDER_PATH)
            self.log_folder_path = LOG_FOLDER_PATH

        self.db_util = DbUtil()
        self.dsl_util = DslUtil()
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

    def load_graph_exporter_json(self, json_path):
        with open(json_path) as json_data:
            data = json.load(json_data)

        return data.get('graph')


    def get_parameter(self, key, parameters):
        found = None
        if key in ["EDGECOLOR", "NODECOLOR"]:
            found = parameters.get(key.lower())
        else:
            if key.endswith("ID"):
                name = parameters.get(key[:-2].lower())
                found = self.dsl_util.find_entity_id(self.cnx, key[:-2].lower(), name, self.logger)

        if not found:
            self.logger.error("GraphExporter: parameter " + str(key) + " not found!")

        return found

    def load_query_json(self, metric_name, parameters):
        with open(INPUT_PATH) as json_data:
            data = json.load(json_data)

        metrics = data.get('queries')

        try:
            found = [m for m in metrics if m.get('name') == metric_name][0]
            nodes_query = found.get('nodes')
            edges_query = found.get('edges')

            for k in found.keys():
                if k not in ['name', 'edges', 'nodes']:

                    k_value = str(self.get_parameter(k, parameters))

                    nodes_query = nodes_query.replace(k, k_value)
                    edges_query = edges_query.replace(k, k_value)

            return (nodes_query, edges_query)
        except:
            self.logger.error("GraphExporter: metric " + str(metric_name) + " not found!")

    # gtype -> graph type = "undirected", "directed", if null "undirected"
    # gmode -> graph mode = "dynamic", "static", if null "dynamic"
    def export(self, file_path, json_path):
        start_time = datetime.now()

        exporter_data = self.load_graph_exporter_json(json_path)

        metric_name = exporter_data.get("name")
        parameters = exporter_data.get("params")

        (nodes_query, edges_query) = self.load_query_json(metric_name, parameters)

        gexf = GexfGenerator(self.cnx, self.logger)
        gexf.create(nodes_query, edges_query, parameters.get("type"), file_path)

        end_time = datetime.now()

        self.db_util.close_connection(self.cnx)

        minutes_and_seconds = divmod((end_time - start_time).total_seconds(), 60)
        self.logger.info("GexfExporter: process finished after " + str(minutes_and_seconds[0])
                         + " minutes and " + str(round(minutes_and_seconds[1], 1)) + " secs")