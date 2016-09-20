__author__ = 'valerio cosentino'

import sys
sys.path.insert(0, "..")

import networkx as nx
from extractor.init_db import config_db
import mysql.connector
from mysql.connector import errorcode
import logging
import logging.handlers
import glob
import os
from datetime import datetime

GRAPH_TYPE = "directed"
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
        "oranges": (255, 69, 0),
        "pink": (255, 192, 203),
        "purple": (160, 32, 240),
        "violet": (148, 0, 211)
        }

SQL_NODES = """
SELECT CONCAT('U', c.author_id) AS id, u.email AS label, COUNT(distinct file_id) AS size, 1 AS color
FROM commit c JOIN file_modification fm ON c.id = fm.commit_id
JOIN file f ON f.id = fm.file_id
JOIN user u ON u.id = c.author_id
JOIN repository r ON r.id = f.repo_id
WHERE r.name = %s
GROUP BY c.author_id
UNION
SELECT CONCAT('F', f.id) AS id, f.name AS label, 1 AS size, 6 AS color
FROM file f JOIN repository r ON r.id = f.repo_id
WHERE r.name = %s
"""

SQL_EDGES = """
SELECT CONCAT('U', author_id) AS source, CONCAT('F', file_id) AS target, COUNT(*) AS weight
FROM commit c JOIN file_modification fm ON c.id = fm.commit_id
JOIN file f ON f.id = fm.file_id
JOIN repository r ON r.id = f.repo_id
WHERE r.name = %s
GROUP BY author_id, file_id;
"""


class GexfExporter():
    def __init__(self, db_name, repo_name):
        LOG_FILENAME = "logs/exporter"
        self.delete_previous_logs("logs")
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

    def delete_previous_logs(self, path):
        files = glob.glob(path + "/*")
        for f in files:
            os.remove(f)

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

    def get_color(self, color_number):
        color = COLORS.keys()[int(color_number)]
        return COLORS.get(color)

    def add_nodes(self, graph):
        cursor = self.cnx.cursor()
        arguments = [self.repo_name, self.repo_name]
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
                graph.node[node_id]['viz'] = {'color': {'r': r, 'g': g, 'b': b, 'a': 0},
                                              'size': node_size,
                                              'label': node_label}
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

            try:
                graph.add_edge(source_id, target_id, weight=weight)
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
