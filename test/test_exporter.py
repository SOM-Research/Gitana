__author__ = 'valerio cosentino'

from exporter.gexf_exporter import GexfExporter

CONFIG = {
            'user': 'root',
            'password': 'root',
            'host': 'localhost',
            'port': '3306',
            'raise_on_warnings': False,
            'buffered': True
        }


def main():
    gexf = GexfExporter(CONFIG, "papyrus_db", None)
    gexf.export("./export.gexf", "undirected", "dynamic", "users-on-issues")


if __name__ == "__main__":
    main()