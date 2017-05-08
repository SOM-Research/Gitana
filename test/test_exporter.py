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


def main():
    g = Gitana(CONFIG, None)
    g.export_to_graph("_papyrus_db", "./graph.json", "./graph.gexf")
    g.export_to_report("_papyrus_db", "./report.json", "./report.html")

if __name__ == "__main__":
    main()