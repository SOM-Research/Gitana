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


def test_create_db():
    g = Gitana(CONFIG)
    g.init_db("dbschema_test")


def test_create_db_parts():
    g = Gitana(CONFIG)
    g.init_db("dbschema_test", init_forum=False, init_instant_messaging=False, init_issue_tracker=False)
    g.add_issue_tracker_tables("dbschema_test")
    g.add_forum_tables("dbschema_test")
    g.add_instant_messaging_tables("dbschema_test")

    g.init_db("dbschema_test", init_forum=False, init_instant_messaging=False, init_issue_tracker=False)


def test_list_projects():
    g = Gitana(CONFIG)
    g.list_projects("db_2048")


def test_add_project():
    g = Gitana(CONFIG)
    g.create_project("dbschema_test", "1")
    g.create_project("dbschema_test", "2")
    g.list_projects("dbschema_test")


def test_add_repository():
    g = Gitana(CONFIG)
    g.delete_previous_logs()
    g.create_repository("dbschema_test", "1", "11")


def main():
    # test_create_db()
    test_create_db_parts()
    # test_list_projects()
    # test_add_project()
    # test_add_repository()


if __name__ == "__main__":
    main()
