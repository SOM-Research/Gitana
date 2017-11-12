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

REFERENCES = ["origin/master"]


def test_1():
    print("test import type 1")

    g = Gitana(CONFIG)
    g.delete_previous_logs()
    g.init_db("vcs1_db_test")
    g.create_project("vcs1_db_test", "2048")
    # test import type 1
    g.import_git_data("vcs1_db_test", "2048", "2048_repo", "C:\\Users\\atlanmod\\Desktop\\2048",
                      import_type=1, processes=5)


def test_2():
    print("test import type 2")

    g = Gitana(CONFIG)
    g.delete_previous_logs()
    g.init_db("vcs2_db_test")
    g.create_project("vcs2_db_test", "2048")

    # test import type 2
    g.import_git_data("vcs2_db_test", "2048", "2048_repo", "C:\\Users\\atlanmod\\Desktop\\2048",
                      import_type=2, processes=5)


def test_3():
    print("test import type 3")

    g = Gitana(CONFIG)
    g.delete_previous_logs()
    g.init_db("vcs3_db_test")
    g.create_project("vcs3_db_test", "2048")

    # test import type 3
    g.import_git_data("vcs3_db_test", "2048", "2048_repo", "C:\\Users\\atlanmod\\Desktop\\2048",
                      import_type=3, processes=5)


def test_4():
    print("test import references")

    g = Gitana(CONFIG)
    g.delete_previous_logs()
    g.init_db("vcs4_db_test")
    g.create_project("vcs4_db_test", "2048")

    # import references
    g.import_git_data("vcs4_db_test", "2048", "2048_repo", "C:\\Users\\atlanmod\\Desktop\\2048",
                      import_type=3, references=REFERENCES, processes=5)


def test_5():
    print("test update")

    g = Gitana(CONFIG)
    g.delete_previous_logs()
    g.init_db("vcs5_db_test")
    g.create_project("vcs5_db_test", "2048")

    # import references
    g.import_git_data("vcs5_db_test", "2048", "2048_repo", "C:\\Users\\atlanmod\\Desktop\\2048",
                      before_date="2015-10-10", import_type=2, references=REFERENCES, processes=5)

    # test update
    g.update_git_data("vcs5_db_test", "2048", "2048_repo", "C:\\Users\\atlanmod\\Desktop\\2048")


def main():
    test_1()
    test_2()
    test_3()
    test_4()
    test_5()


if __name__ == "__main__":
    main()
