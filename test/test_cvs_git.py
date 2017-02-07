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

REFERENCES = ["0.7.0"]

#REFERENCES = ["0.7.0", "0.8.0", "0.9.0"]

# REFERENCES = ["0.7.0", "0.7.1", "0.7.2", "0.7.3", "0.7.4", "0.8.0", "0.9.0",
#               "0.10.0", "1.0.0", "1.0.1", "1.1.2", "1.1.3", "1.1.4", "2.0.0",
#               "0.10.1_RC4", "0.10.2_RC5", "0.8.1_RC4", "0.8.2_RC4", "0.9.1_RC4", "0.9.2_RC3", "1.0.2_RC4", "1.1.0_RC4", "1.2.0M5"]


def test_1():
    g = Gitana(CONFIG, None)
    g.delete_previous_logs()
    g.init_db("papyrus_db_test")
    g.create_project("papyrus_db_test", "papyrus")

    #test before date
    g.import_git_data("papyrus_db_test", "papyrus", "papyrus_repo", "C:\\Users\\atlanmod\\Desktop\\org.eclipse.papyrus", "2010-10-10", 1, REFERENCES, 20)


def test_2():
    g = Gitana(CONFIG, None)
    #g.delete_previous_logs()
    g.init_db("papyrus_db_test")

    g.create_project("papyrus_db_test", "papyrus")

    #test import type 2
    g.import_git_data("papyrus_db_test", "papyrus", "papyrus_repo", "C:\\Users\\atlanmod\\Desktop\\org.eclipse.papyrus", "2010-10-10", 2, REFERENCES, 20)


def test_3():
    g = Gitana(CONFIG, None)
    #g.delete_previous_logs()
    g.init_db("papyrus_db_test")

    g.create_project("papyrus_db_test", "papyrus")

    #test import type 3
    g.import_git_data("papyrus_db_test", "papyrus", "papyrus_repo", "C:\\Users\\atlanmod\\Desktop\\org.eclipse.papyrus", "2010-10-10", 3, REFERENCES, 5)


def test_4():
    g = Gitana(CONFIG, None)
    g.delete_previous_logs()
    g.init_db("papyrus_db_test")

    g.create_project("papyrus_db_test", "papyrus")
    g.import_git_data("papyrus_db_test", "papyrus", "papyrus_repo", "C:\\Users\\atlanmod\\Desktop\\org.eclipse.papyrus", "2009-10-10", 1, REFERENCES, 20)


def test_4a():
    g = Gitana(CONFIG, None)
    #g.delete_previous_logs()
    g.init_db("papyrus_db_test")

    g.create_project("papyrus_db_test", "papyrus")
    g.import_git_data("papyrus_db_test", "papyrus", "papyrus_repo", "C:\\Users\\atlanmod\\Desktop\\org.eclipse.papyrus", "2010-10-10", 1, REFERENCES, 1)

    #test recover
    g.update_git_data("papyrus_db_test", "papyrus", "papyrus_repo", "C:\\Users\\atlanmod\\Desktop\\org.eclipse.papyrus", None, 1)


def test_5():
    g = Gitana(CONFIG, None)
    #g.delete_previous_logs()
    g.init_db("papyrus_db_test")

    g.create_project("papyrus_db_test", "papyrus")

    #test import full
    g.import_git_data("papyrus_db_test", "papyrus", "papyrus_repo", "C:\\Users\\atlanmod\\Desktop\\org.eclipse.papyrus", None, 1, None, 20)


def test_6():
    g = Gitana(CONFIG, None)
    g.delete_previous_logs()
    g.init_db("dltk_db_test")
    g.create_project("dltk_db_test", "dltk")

    #test before date
    g.import_git_data("dltk_db_test", "dltk", "dltk_repo", "C:\\Users\\atlanmod\\Desktop\\org.eclipse.dltk.core", None, 1, None, 20)


def test_7():
    g = Gitana(CONFIG, None)
    g.delete_previous_logs()
    g.init_db("cdt_db_test")
    g.create_project("cdt_db_test", "cdt")

    #test before date
    g.import_git_data("cdt_db_test", "cdt", "cdt_repo", "C:\\Users\\atlanmod\\Desktop\\org.eclipse.cdt", None, 1, None, 20)


def test_8():
    g = Gitana(CONFIG, None)
    g.delete_previous_logs()
    g.init_db("2048_db_test")
    g.create_project("2048_db_test", "2048")

    #test before date
    g.import_git_data("2048_db_test", "2048", "2048_repo", "C:\\Users\\atlanmod\\Desktop\\2048", None, 1, None, 20)


def main():
    test_8()

if __name__ == "__main__":
    main()
