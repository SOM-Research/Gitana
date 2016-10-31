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


def test_1(g):
    g.import_slack_data("bootstrap_db_test", "bootstrap", "slack_bootstrap", None, None, ['xoxp-67182691220-67204318994-79972048550-3efcced1cde'])


def main():
    g = Gitana(CONFIG, None)
    g.delete_previous_logs()
    g.init_db("bootstrap_db_test")
    g.create_project("bootstrap_db_test", "bootstrap")

    print "starting 1.."
    test_1(g)

if __name__ == "__main__":
    main()
