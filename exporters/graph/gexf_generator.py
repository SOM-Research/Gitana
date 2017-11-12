#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'valerio cosentino'

import networkx as nx
from random import randint
import errno
import os


class GexfGenerator():
    """
    This class handles the generation of graphs in Gexf format
    """

    DEFAULT_GRAPH_MODE = "dynamic"
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

    def __init__(self, cnx, logger):
        """
        :type cnx: Object
        :param cnx: DB connection

        :type logger: Object
        :param logger: logger
        """
        self._cnx = cnx
        self._logger = logger

    def _create_output_file(self, filename):
        # creates the output file where to store the Gexf
        if not os.path.exists(os.path.dirname(filename)):
            try:
                os.makedirs(os.path.dirname(filename))
            except OSError as exc:  # Guard against race condition
                if exc.errno != errno.EEXIST:
                    raise

    def _get_color(self, color_name):
        # gets the color by its name
        return GexfGenerator.COLORS.get(color_name)

    def _add_nodes(self, graph, nodes_query):
        # adds nodes to the graph
        cursor = self._cnx.cursor()
        cursor.execute(nodes_query)

        row = cursor.fetchone()
        while row:
            node_id = str(row[0])
            node_label = row[1]
            node_size = row[2]
            node_color = str(row[3])

            try:
                if node_color == "random":
                    r = randint(0, 255)
                    g = randint(0, 255)
                    b = randint(0, 255)
                else:
                    r, g, b = self._get_color(node_color)
                graph.add_node(node_id)
                graph.node[node_id]['label'] = node_label
                graph.node[node_id]['viz'] = {'color': {'r': r, 'g': g, 'b': b, 'a': 0},
                                              'size': node_size,
                                              'position': {'x': randint(0, 255),
                                                           'y': randint(0, 255),
                                                           'z': randint(0, 255)}}
            except:
                self._logger.warning(
                    "GexfExporter: problem when inserting node(id, label, size): "
                    "(" + str(node_id) + "," + str(node_label) + ")")

            row = cursor.fetchone()

        cursor.close()

    def _add_edges(self, graph, edges_query):
        # adds edges to the graph
        cursor = self._cnx.cursor()
        cursor.execute(edges_query)

        row = cursor.fetchone()
        counter = 0
        while row:
            source_id = str(row[0])
            target_id = str(row[1])
            weight = str(row[2])
            edge_color = str(row[3])

            try:
                r, g, b = self._get_color(edge_color)
                graph.add_edge(source_id, target_id, weight=weight)
                graph[source_id][target_id]['viz'] = {'color': {'r': r, 'g': g, 'b': b, 'a': 0}}
            except:
                self._logger.warning("GexfExporter: problem when inserting edge(source_id, target_id, weight): "
                                     "(" + str(source_id) + "," + str(target_id) + "," + str(weight) + ")")

            row = cursor.fetchone()
            counter += 1

        cursor.close()

    def create(self, nodes_query, edges_query, type, file_path):
        """
        creates the Gexf file

        :type nodes_query: str
        :param nodes_query: SQL query of the nodes

        :type edges_query: str
        :param edges_query: SQL query of the edges

        :type type: str
        :param type: type of the graph (directed, undirected)

        :type file_path: str
        :param file_path: file path where to store the output
        """
        if type == "directed":
            graph = nx.DiGraph(mode=GexfGenerator.DEFAULT_GRAPH_MODE)
        else:
            graph = nx.Graph(mode=GexfGenerator.DEFAULT_GRAPH_MODE)

        self._add_nodes(graph, nodes_query)
        self._add_edges(graph, edges_query)

        if not file_path.endswith(GexfGenerator.EXT):
            file_path += GexfGenerator.EXT

        self._create_output_file(file_path)
        nx.write_gexf(graph, file_path)
