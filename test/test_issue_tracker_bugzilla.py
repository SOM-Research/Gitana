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

REFERENCES = ["0.7.0", "0.7.1", "0.7.2", "0.7.3", "0.7.4", "0.8.0", "0.9.0",
              "0.10.0", "1.0.0", "1.0.1", "1.1.2", "1.1.3", "1.1.4", "2.0.0"]


def test_1(g):
    #test before date
    g.import_bugzilla_tracker_data("papyrus_db_test", "papyrus", "papyrus_repo", "bugzilla_papyrus", "https://bugs.eclipse.org/bugs/xmlrpc.cgi", "papyrus", "2013-05-05", False, 1)


def test_2(g):
    #test update
    g.update_bugzilla_tracker_data("papyrus_db_test", "papyrus", "papyrus_repo", "bugzilla_papyrus", "papyrus", 5)


def test_3(g):
    g.import_bugzilla_tracker_data("papyrus_db_test", "papyrus", "papyrus_repo", "bugzilla_papyrus", "https://bugs.eclipse.org/bugs/xmlrpc.cgi", "papyrus", None, False, 10)


def main():
    g = Gitana(CONFIG, None)
    g.delete_previous_logs()
    #g.init_db("papyrus_db_test")
    #g.create_project("papyrus_db_test", "papyrus")
    #g.import_git_data("papyrus_db_test", "papyrus", "papyrus_repo", "C:\\Users\\atlanmod\\Desktop\\org.eclipse.papyrus", None, 1, REFERENCES, 20)

    #print "starting 1.."
    #test_1(g)
    print "starting 2.."
    test_2(g)
    print "starting 3.."
    test_3(g)

if __name__ == "__main__":
    main()
