__author__ = 'valerio cosentino'

from exporter.report.report_exporter import ReportExporter
from exporter.graph.graph_exporter import GraphExporter

CONFIG = {
            'user': 'root',
            'password': 'root',
            'host': 'localhost',
            'port': '3306',
            'raise_on_warnings': False,
            'buffered': True
        }


def test_graph_exporter():
    exporter = GraphExporter(CONFIG, "papyrus_db_test", None)
    exporter.export("./export.gexf", "./graph.json")


def test_report_exporter():
    exporter = ReportExporter(CONFIG, "papyrus_db_test", None)
    exporter.export("./report.html", "./report.json")


def main():
    #test_graph_exporter()
    test_report_exporter()

if __name__ == "__main__":
    main()