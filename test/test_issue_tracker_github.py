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


def test_2(g):
    g.init_db("db_halflife")
    g.create_project("db_halflife", "halflife")
    g.import_git_data("db_halflife", "halflife", "halflife", "C:\\Users\\atlanmod\\Desktop\\halflife",
                      None, 1, None, 20)
    g.import_github_tracker_data("db_halflife", "halflife", "halflife", "halflife-tracker", "ValveSoftware/halflife", False, ["5ed4abfa9db99b61d1b1159dff548571e1bee27d"])


def test_1(g):
    g.init_db("db_2048")
    g.create_project("db_2048", "2048")
    g.import_git_data("db_2048", "2048", "2048", "C:\\Users\\atlanmod\\Desktop\\2048",
                      None, 1, None, 20)
    g.import_github_tracker_data("db_2048", "2048", "2048", "2048-tracker", "gabrielecirulli/2048", False, ["5ed4abfa9db99b61d1b1159dff548571e1bee27d"])


def main():
    g = Gitana(CONFIG, None)
    g.delete_previous_logs()

    print "starting 1.."
    test_1(g)
    #print "starting 2.."
    #test_2(g)


if __name__ == "__main__":
    main()
