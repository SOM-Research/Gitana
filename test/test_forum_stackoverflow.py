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


def test_1():
    #test simple
    g = Gitana(CONFIG, None)
    g.delete_previous_logs()
    g.init_db("papyrus_db_test")

    g.create_project("papyrus_db_test", "papyrus")

    g.import_stackoverflow_data("papyrus_db_test", "papyrus", "papyrus-so", "papyrus", None, False, ['IFco1Gh5EJ*U)ZY9)16ZKQ(('])


def test_2():
    #test update
    g = Gitana(CONFIG, None)
    g.delete_previous_logs()

    g.update_stackoverflow_data("papyrus_db_test", "papyrus", "papyrus-forum", ['IFco1Gh5EJ*U)ZY9)16ZKQ(('])


def main():
    print "starting 1.."
    test_1()
    print "starting 2.."
    test_2()


if __name__ == "__main__":
    main()