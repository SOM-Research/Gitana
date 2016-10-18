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

REFERENCES = ["origin/master"]


def main():
    g = Gitana(CONFIG, None)
    g.delete_previous_logs()
    g.init_db("linux_db")

    g.create_project("linux_db", "linux_project")
    g.import_git_data("linux_db", "linux_project", "linux_repo", "C:\\Users\\atlanmod\\Desktop\\linux", None, 1, None, 20)

    #g.import_bugzilla_tracker_data("papyrus_xxx", "papyrus", "papyrus_xxx", "https://bugs.eclipse.org/bugs/xmlrpc.cgi", "papyrus", None, False, 20)
    #g.update_bugzilla_tracker_data("test_test", "test_project1", "test_repo1", "https://bugs.eclipse.org/bugs/xmlrpc.cgi", "papyrus", 20)

    #g.import_eclipse_forum_data("papyrus_db", "papyrus", "https://www.eclipse.org/forums/index.php/f/121/", None, False, 4)
    #g.update_eclipse_forum_data("test_test", "test_project1", "https://www.eclipse.org/forums/index.php/f/121/", 1)

if __name__ == "__main__":
    main()