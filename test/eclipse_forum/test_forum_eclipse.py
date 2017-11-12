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
    g.import_eclipse_forum_data("ecliseforum_db_test", "papyrus", "papyrus-forum",
                                "https://www.eclipse.org/forums/index.php/f/121/", before_date="2012-12-05")


def test_2(g):
    # test update
    g.update_eclipse_forum_data("ecliseforum_db_test", "papyrus", "papyrus-forum",
                                "https://www.eclipse.org/forums/index.php/f/121/", processes=5)


def test_3(g):
    # test recover process
    g.import_eclipse_forum_data("ecliseforum_db_test", "papyrus", "papyrus-forum",
                                "https://www.eclipse.org/forums/index.php/f/121/", "2014-05-05")


def test_4(g):
    # test recover process
    g.import_eclipse_forum_data("ecliseforum_db_test", "papyrus", "papyrus-forum",
                                "https://www.eclipse.org/forums/index.php/f/121/")


def main():
    g = Gitana(CONFIG)
    g.delete_previous_logs()
    g.init_db("ecliseforum_db_test")
    g.create_project("ecliseforum_db_test", "papyrus")

    print("starting 1..")
    test_1(g)
    print("starting 2..")
    test_2(g)
    print("starting 3..")
    test_3(g)
    print("starting 4..")
    test_4(g)


if __name__ == "__main__":
    main()
