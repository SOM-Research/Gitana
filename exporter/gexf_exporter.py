__author__ = 'valerio cosentino'

import networkx as nx
import mysql.connector
from mysql.connector import errorcode
import logging
import logging.handlers
import glob
import os
from datetime import datetime
import sys
sys.path.insert(0, "..")

from extractor.db import config_db

LOG_FOLDER = "logs"
GRAPH_TYPE = "undirected"
GRAPH_MODE = "dynamic"
OUTPUT_PATH = "./output/"
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

SQL_NODES = """
SELECT author_id as id, u.email AS label, COUNT(DISTINCT issue_id) AS size, 'blue' AS color
FROM issue_comment ic JOIN user u ON ic.author_id = u.id
JOIN issue i ON i.id = ic.issue_id
JOIN issue_tracker it ON it.id = i.issue_tracker_id
JOIN repository r ON r.id = it.repo_id
WHERE r.name = %s
GROUP BY author_id;
"""

SQL_EDGES = """
SELECT source, target, COUNT(*) AS weight, 'gray' AS color
FROM (
SELECT ic1.issue_id, ic1.author_id AS source, ic2.author_id AS target, CONCAT(ic1.author_id, '-', ic2.author_id) AS pair
from issue_comment ic1
JOIN issue_comment ic2 ON ic1.id <> ic2.id
AND ic1.issue_id = ic2.issue_id
AND ic1.author_id <> ic2.author_id
AND ic1.author_id > ic2.author_id
JOIN issue i ON ic1.issue_id = i.id
JOIN issue_tracker it ON it.id = i.issue_tracker_id
JOIN repository r ON r.id = it.repo_id
WHERE r.name = %s) AS issue_interaction
GROUP BY pair;
"""

class GexfExporter():
    def __init__(self, db_name, repo_name):
        self.create_folder(LOG_FOLDER)
        LOG_FILENAME = LOG_FOLDER + "/exporter"
        self.delete_previous_logs(LOG_FOLDER)
        self.logger = logging.getLogger(LOG_FILENAME)
        fileHandler = logging.FileHandler(LOG_FILENAME + "-" + db_name + ".log", mode='w')
        formatter = logging.Formatter("%(asctime)s:%(levelname)s:%(message)s", "%Y-%m-%d %H:%M:%S")

        fileHandler.setFormatter(formatter)
        self.logger.setLevel(logging.INFO)
        self.logger.addHandler(fileHandler)

        self.db_name = db_name
        self.repo_name = repo_name

        self.cnx = mysql.connector.connect(**config_db.CONFIG)
        self.set_database()
        self.set_settings()

    def create_folder(self, name):
        if not os.path.exists(name):
            os.makedirs(name)

    def delete_previous_logs(self, path):
        files = glob.glob(path + "/*")
        for f in files:
            try:
                os.remove(f)
            except:
                continue

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

    def add_nodes(self, graph):
        cursor = self.cnx.cursor()
        arguments = [self.repo_name]
        cursor.execute(SQL_NODES, arguments)

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

    def add_edges(self, graph):
        cursor = self.cnx.cursor()
        arguments = [self.repo_name]
        cursor.execute(SQL_EDGES, arguments)

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

    def export(self, file_name, gtype, gmode):
        start_time = datetime.now()

        if gtype == "directed":
            graph = nx.DiGraph(mode=gmode)
        else:
            graph = nx.Graph(mode=gmode)

        self.add_nodes(graph)
        self.add_edges(graph)

        self.create_folder(OUTPUT_PATH)
        nx.write_gexf(graph, OUTPUT_PATH + file_name + EXT)

        end_time = datetime.now()

        minutes_and_seconds = divmod((end_time - start_time).total_seconds(), 60)
        self.logger.info("GexfExporter: process finished after " + str(minutes_and_seconds[0])
                         + " minutes and " + str(round(minutes_and_seconds[1], 1)) + " secs")


def main():
    a = GexfExporter(config_db.DB_NAME, config_db.REPO_NAME)
    # graph type = "undirected", "directed"
    # graph mode = "dynamic", "static"
    a.export("test", GRAPH_TYPE, GRAPH_MODE)


if __name__ == "__main__":
    main()
