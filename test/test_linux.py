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
    g.init_db("linux_db")

    g.create_project("linux_db", "linux_project")
    g.import_git_data("linux_db", "linux_project", "linux_repo", "C:\\Users\\atlanmod\\Desktop\\linux", None, 1, ["v2.6.19"], 20)


def test_2():
    g = Gitana(CONFIG, None)
    g.delete_previous_logs()
    g.init_db("linux_db")

    g.create_project("linux_db", "linux_project")
    g.import_git_data("linux_db", "linux_project", "linux_repo", "C:\\Users\\atlanmod\\Desktop\\linux", None, 1, ["v2.6.14-rc1"], 20)


def test_3():
    g = Gitana(CONFIG, None)
    g.delete_previous_logs()
    g.init_db("linux_db")

    g.create_project("linux_db", "linux_project")
    g.import_git_data("linux_db", "linux_project", "linux_repo", "C:\\Users\\atlanmod\\Desktop\\linux", None, 1, ["v2.6.14-rc1"], 20)


def main():
    #print "starting 1.."
    #test_1()
    #print "starting 2.."
    #test_2()
    print "starting 3.."
    test_3()


if __name__ == "__main__":
    main()