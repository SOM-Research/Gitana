__author__ = 'valerio cosentino'

from gitana.gitana import Gitana

CONFIG = {
            'user': 'root',
            'password': 'root',
            'host': 'localhost',
            'port': '3306',
            'raise_on_warnings': False,
            'buffered': True
        }


def _papyrus_export():
    g = Gitana(CONFIG)
    g.export_graph("db_papyrus", "./graph.json", "./graph.gexf")
    g.export_activity_report("db_papyrus", "./report.json", "./report.html")


def main():
    _papyrus_export()


if __name__ == "__main__":
    main()
