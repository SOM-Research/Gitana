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
    g.init_db("papyrus_db_test")
    g.create_project("papyrus_db_test", "papyrus")

    g.import_git_data("papyrus_db_test", "papyrus", "papyrus_repo", "C:\\Users\\atlanmod\\Desktop\\org.eclipse.papyrus", None, 1, None, 20)

    g.import_bugzilla_tracker_data("papyrus_db_test", "papyrus", "papyrus_xxx", "https://bugs.eclipse.org/bugs/xmlrpc.cgi", "papyrus", None, False, 10)

    g.import_eclipse_forum_data("papyrus_db_test", "papyrus", "https://www.eclipse.org/forums/index.php/f/121/", None, False, 4)

    g.import_stackoverflow_data("papyrus_db_test", "papyrus", "papyrus", None, False, ['IFco1Gh5EJ*U)ZY9)16ZKQ(('])

if __name__ == "__main__":
    main()
