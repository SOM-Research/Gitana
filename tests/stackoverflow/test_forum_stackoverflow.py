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

SO_TOKENS = ['((bLKlUAwcud8GIKAztDiA))']


def test_1():
    # test simple
    g = Gitana(CONFIG)
    g.delete_previous_logs()
    g.init_db("so_db_test")
    g.create_project("so_db_test", "papyrus")
    g.import_stackoverflow_data("so_db_test", "papyrus", "papyrus-stackoverflow", "papyrus",
                                SO_TOKENS, before_date="2016-09-01")


def test_2():
    # test update
    g = Gitana(CONFIG)
    g.delete_previous_logs()

    g.update_stackoverflow_data("so_db_test", "papyrus", "papyrus-stackoverflow", SO_TOKENS)


def main():
    print("starting 1..")
    test_1()
    print("starting 2..")
    test_2()


if __name__ == "__main__":
    main()
