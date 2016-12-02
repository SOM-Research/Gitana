__author__ = 'valerio cosentino'

import networkx as nx
from random import randint
import errno
import os

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


class GexfGenerator():

    def __init__(self, cnx, logger):
        self.cnx = cnx
        self.logger = logger

    def create_output_file(self, filename):
        if not os.path.exists(os.path.dirname(filename)):
            try:
                os.makedirs(os.path.dirname(filename))
            except OSError as exc: # Guard against race condition
                if exc.errno != errno.EEXIST:
                    raise

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
                if node_color == "random":
                    r = randint(0, 255)
                    g = randint(0, 255)
                    b = randint(0, 255)
                else:
                    r, g, b = self.get_color(node_color)
                graph.add_node(node_id)
                graph.node[node_id]['label'] = node_label
                graph.node[node_id]['viz'] = {'color': {'r': r, 'g': g, 'b': b, 'a': 0},
                                              'size': node_size,
                                              'position': {'x': randint(0, 255), 'y': randint(0, 255), 'z': randint(0, 255)}}
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

    def create(self, nodes_query, edges_query, type, file_path):
        if type == "directed":
            graph = nx.DiGraph(mode=DEFAULT_GRAPH_MODE)
        else:
            graph = nx.Graph(mode=DEFAULT_GRAPH_MODE)

        self.add_nodes(graph, nodes_query)
        self.add_edges(graph, edges_query)

        if not file_path.endswith(EXT):
            file_path += EXT

        self.create_output_file(file_path)
        nx.write_gexf(graph, file_path)

