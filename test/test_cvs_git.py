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

REFERENCES = ["master"]


def test_1():
    print "test before date"

    g = Gitana(CONFIG, None)
    g.delete_previous_logs()
    g.init_db("db_2048")
    g.create_project("db_2048", "2048")

    #test before date
    g.import_git_data("db_2048", "2048", "2048_repo", "C:\\Users\\atlanmod\\Desktop\\2048", "2014-10-10", 1, None, 5)


def test_2():
    print "test import type 2"

    g = Gitana(CONFIG, None)
    g.delete_previous_logs()
    g.init_db("db_2048")
    g.create_project("db_2048", "2048")

    #test import type 2
    g.import_git_data("db_2048", "2048", "2048_repo", "C:\\Users\\atlanmod\\Desktop\\2048", None, 2, None, 5)


def test_3():
    print "test import type 3"

    g = Gitana(CONFIG, None)
    g.delete_previous_logs()
    g.init_db("db_2048")
    g.create_project("db_2048", "2048")

    #test import type 2
    g.import_git_data("db_2048", "2048", "2048_repo", "C:\\Users\\atlanmod\\Desktop\\2048", None, 3, None, 5)


def test_4():
    print "test import references"

    g = Gitana(CONFIG, None)
    g.delete_previous_logs()
    g.init_db("db_2048")
    g.create_project("db_2048", "2048")

    #import references
    g.import_git_data("db_2048", "2048", "2048_repo", "C:\\Users\\atlanmod\\Desktop\\2048", None, 3, REFERENCES, 5)


def test_5():
    print "test update"

    g = Gitana(CONFIG, None)
    g.delete_previous_logs()
    g.init_db("db_2048")
    g.create_project("db_2048", "2048")

    #import references
    g.import_git_data("db_2048", "2048", "2048_repo", "C:\\Users\\atlanmod\\Desktop\\2048", "2014-10-10", 3, REFERENCES, 5)

    #test update
    g.update_git_data("db_2048", "2048", "2048_repo", "C:\\Users\\atlanmod\\Desktop\\2048", None, 5)


def test_6():
    print "test import type 1"

    g = Gitana(CONFIG, None)
    g.delete_previous_logs()
    g.init_db("db_2048")
    g.create_project("db_2048", "2048")

    #test import full
    g.import_git_data("db_2048", "2048", "2048_repo", "C:\\Users\\atlanmod\\Desktop\\2048", None, 1, None, 5)


def main():
    test_1()
    test_2()
    test_3()
    test_4()
    test_5()
    test_6()

if __name__ == "__main__":
    main()
