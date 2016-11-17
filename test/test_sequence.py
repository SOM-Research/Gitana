#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'valerio cosentino'

from gitana import Gitana

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
    g.delete_previous_logs()
    g.init_db("_papyrus_db")
    g.create_project("_papyrus_db", "papyrus")

    g.import_git_data("_papyrus_db", "papyrus", "papyrus_repo", "C:\\Users\\atlanmod\\Desktop\\org.eclipse.papyrus", None, 1, ["0.7.0"], 20)

    g.import_bugzilla_tracker_data("_papyrus_db", "papyrus", "papyrus_repo", "bugzilla-papyrus", "https://bugs.eclipse.org/bugs/xmlrpc.cgi", "papyrus", None, 10)

    g.import_eclipse_forum_data("_papyrus_db", "papyrus", "papyrus-eclipse", "https://www.eclipse.org/forums/index.php/f/121/", None, 4)

    g.import_stackoverflow_data("_papyrus_db", "papyrus", "papyrus-stackoverflow", "papyrus", None, ['IFco1Gh5EJ*U)ZY5)16ZKQ(('])

if __name__ == "__main__":
    main()
