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

GH_TOKENS = []


def test(g):
    g.init_db("db_2048")
    g.delete_previous_logs()
    g.create_project("db_2048", "2048")
    g.import_git_data("db_2048", "2048", "repo_2048", "C:\\Users\\atlanmod\\Desktop\\2048",
                      None, 1, None, 2)
    g.import_github_tracker_data("db_2048", "2048", "repo_2048", "2048-tracker", "gabrielecirulli/2048", False, GH_TOKENS)


def main():
    g = Gitana(CONFIG)
    g.delete_previous_logs()

    print "starting .."
    test(g)


if __name__ == "__main__":
    main()
