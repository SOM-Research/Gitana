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
    g = Gitana(CONFIG, None)
    g.delete_previous_logs()
    g.init_db("bootstrap_db_test")
    g.create_project("bootstrap_db_test", "bootstrap")
    g.import_slack_data("bootstrap_db_test", "bootstrap", "slack_bootstrap", "2016-08-12", ["random", "metascience", "softwareanalysis"], ['xoxp-67182691220-67204318994-79972048550-3efcced1cd'])


def test_2():
    g = Gitana(CONFIG, None)
    g.delete_previous_logs()

    #remeber to delete the last messages from a channel
    g.update_slack_data("bootstrap_db_test", "bootstrap", "slack_bootstrap", ['xoxp-67182691220-67204318994-79972048550-3efcced1cd'])


def main():
    #print "starting 1.."
    #test_1()
    print "starting 2.."
    test_2()

if __name__ == "__main__":
    main()
