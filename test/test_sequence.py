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

#REFERENCES = ["0.7.0", "0.7.1", "0.7.2", "0.7.3", "0.7.4", "0.8.0", "0.9.0",
#              "0.10.0", "1.0.0", "1.0.1", "1.1.2", "1.1.3", "1.1.4", "2.0.0",
#              "0.10.1_RC4", "0.10.2_RC5", "0.8.1_RC4", "0.8.2_RC4", "0.9.1_RC4", "0.9.2_RC3", "1.0.2_RC4", "1.1.0_RC4", "1.2.0M5"]


def main():
    g = Gitana(CONFIG, None)
    g.delete_previous_logs()
    #g.init_db("papyrus_db")

    #g.create_project("papyrus_db", "papyrus")
    #g.import_git_data("papyrus_db", "papyrus", "papyrus_repo", "C:\\Users\\atlanmod\\Desktop\\org.eclipse.papyrus", None, 1, None, 20)

    #g.import_bugzilla_tracker_data("papyrus_db", "papyrus", "papyrus_repo", "https://bugs.eclipse.org/bugs/xmlrpc.cgi", "papyrus", None, False, 20)
    #g.update_bugzilla_tracker_data("test_test", "test_project1", "test_repo1", "https://bugs.eclipse.org/bugs/xmlrpc.cgi", "papyrus", 20)

    g.import_eclipse_forum_data("papyrus_db", "papyrus", "https://www.eclipse.org/forums/index.php/f/121/", None, False, 4)
    #g.update_eclipse_forum_data("test_test", "test_project1", "https://www.eclipse.org/forums/index.php/f/121/", 1)

if __name__ == "__main__":
    main()
