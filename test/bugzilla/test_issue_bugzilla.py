#!/usr/bin/env python
# -*- coding: utf-8 -*-
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


def test_1(g):
    # test before date
    g.import_bugzilla_issue_data("bugzilla_db_test", "papyrus", "papyrus_repo", "bugzilla_papyrus",
                                 "https://bugs.eclipse.org/bugs/xmlrpc.cgi", "papyrus", "2013-05-05", 3)


def test_2(g):
    # test update
    g.update_bugzilla_issue_data("bugzilla_db_test", "papyrus", "papyrus_repo", "bugzilla_papyrus",
                                 "https://bugs.eclipse.org/bugs/xmlrpc.cgi", "papyrus")


def test_3(g):
    g.import_bugzilla_issue_data("bugzilla_db_test", "papyrus", "papyrus_repo", "bugzilla_papyrus",
                                 "https://bugs.eclipse.org/bugs/xmlrpc.cgi", "papyrus")


def main():
    g = Gitana(CONFIG)
    g.delete_previous_logs()
    g.init_db("bugzilla_db_test")
    g.create_project("bugzilla_db_test", "papyrus")
    g.create_repository("bugzilla_db_test", "papyrus", "papyrus_repo")

    print("starting 1..")
    test_1(g)
    print("starting 2..")
    test_2(g)
    print("starting 3..")
    test_3(g)


if __name__ == "__main__":
    main()
