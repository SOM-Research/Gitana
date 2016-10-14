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
import sys
import json
import uuid
import errno
sys.path.insert(0, "..")

from exporter import resources

LOG_FOLDER_PATH = "logs"
LOG_NAME = "gitana-exporter"
DEFAULT_GRAPH_MODE = "dynamic"
INPUT_PATH = os.path.dirname(resources.__file__) + "\queries.json"
EXT = ".gexf"

COLORS = {
        "white": (255, 255, 255),
        "gray": (190, 190, 190),
        "black": (0, 0, 0),
        "blue": (0, 0, 255),
        "cyan": (0, 255, 255),
        "green": (34, 139, 34),
        "yellow": (255, 255, 0),
        "red": (255, 0, 0),
        "brown": (165, 42, 42),
        "orange": (255, 69, 0),
        "pink": (255, 192, 203),
        "purple": (160, 32, 240),
        "violet": (148, 0, 211)
        }


class GexfExporter():
    def __init__(self, config, db_name, log_folder_path):
        if log_folder_path:
            self.create_log_folder(log_folder_path)
            self.log_folder_path = log_folder_path
        else:
            self.create_log_folder(LOG_FOLDER_PATH)
            self.log_folder_path = LOG_FOLDER_PATH

        self.log_path = self.log_folder_path + "/" + LOG_NAME + "-" + str(uuid.uuid4())[:5] + ".log"
        self.logger = logging.getLogger(self.log_path)
        fileHandler = logging.FileHandler(self.log_path, mode='w')
        formatter = logging.Formatter("%(asctime)s:%(levelname)s:%(message)s", "%Y-%m-%d %H:%M:%S")

        fileHandler.setFormatter(formatter)
        self.logger.setLevel(logging.INFO)
        self.logger.addHandler(fileHandler)

        self.db_name = db_name

        self.config = config
        self.cnx = mysql.connector.connect(**self.config)

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

    def get_color(self, color_name):
        return COLORS.get(color_name)

    def add_nodes(self, graph, nodes_query):
        cursor = self.cnx.cursor()
        cursor.execute(nodes_query)

        row = cursor.fetchone()
        while row:
            node_id = str(row[0])
            node_label = str(row[1])
            node_size = row[2]
            node_color = str(row[3])

            try:
                r, g, b = self.get_color(node_color)
                graph.add_node(node_id)
                graph.node[node_id]['label'] = node_label
                graph.node[node_id]['viz'] = {'color': {'r': r, 'g': g, 'b': b, 'a': 0},
                                              'size': node_size}
            except:
                self.logger.warning(
                    "GexfExporter: problem when inserting node(id, label, size): (" + str(node_id) + "," + str(node_label) + ")")

            row = cursor.fetchone()

        cursor.close()

    def add_edges(self, graph, edges_query):
        cursor = self.cnx.cursor()
        cursor.execute(edges_query)

        row = cursor.fetchone()
        counter = 0
        while row:
            source_id = str(row[0])
            target_id = str(row[1])
            weight = str(row[2])
            edge_color = str(row[3])

            try:
                r, g, b = self.get_color(edge_color)
                graph.add_edge(source_id, target_id, weight=weight)
                graph[source_id][target_id]['viz'] = {'color': {'r': r, 'g': g, 'b': b, 'a': 0}}
            except:
                self.logger.warning("GexfExporter: problem when inserting edge(source_id, target_id, weight): (" + str(source_id) + "," + str(target_id) + "," + str(weight) + ")")

            row = cursor.fetchone()
            counter += 1

        cursor.close()

    def load_json(self, metric_name):
        with open(INPUT_PATH) as json_data:
            data = json.load(json_data)

        metrics = data.get('metrics')

        try:
            found = [m for m in metrics if m.get('name') == metric_name][0]
            nodes_query = found.get('nodes')
            edges_query = found.get('edges')

            for k in found.keys():
                if k not in ['name', 'edges', 'nodes']:
                    nodes_query = nodes_query.replace(k, found.get(k))
                    edges_query = edges_query.replace(k, found.get(k))

            return (nodes_query, edges_query)
        except:
            self.logger.error("GexfExporter: metric " + str(metric_name) + " not found!")

    # gtype -> graph type = "undirected", "directed", if null "undirected"
    # gmode -> graph mode = "dynamic", "static", if null "dynamic"
    def export(self, file_path, gtype, gmode, metric_name):
        start_time = datetime.now()

        (nodes_query, edges_query) = self.load_json(metric_name)

        if not gmode:
            gmode = DEFAULT_GRAPH_MODE

        if gtype == "directed":
            graph = nx.DiGraph(mode=gmode)
        else:
            graph = nx.Graph(mode=gmode)

        self.add_nodes(graph, nodes_query)
        self.add_edges(graph, edges_query)

        if not file_path.endswith(EXT):
            file_path += EXT

        self.create_output_file(file_path)
        nx.write_gexf(graph, file_path)

        end_time = datetime.now()

        minutes_and_seconds = divmod((end_time - start_time).total_seconds(), 60)
        self.logger.info("GexfExporter: process finished after " + str(minutes_and_seconds[0])
                         + " minutes and " + str(round(minutes_and_seconds[1], 1)) + " secs")