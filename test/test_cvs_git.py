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

    #test update
    #g.update_git_data("papyrus_db_test", "papyrus", "papyrus_repo", "C:\\Users\\atlanmod\\Desktop\\org.eclipse.papyrus", "2012-10-10", True, False, 20)


def test_4a():
    g = Gitana(CONFIG, None)
    #g.delete_previous_logs()
    g.init_db("papyrus_db_test")

    g.create_project("papyrus_db_test", "papyrus")
    g.import_git_data("papyrus_db_test", "papyrus", "papyrus_repo", "C:\\Users\\atlanmod\\Desktop\\org.eclipse.papyrus", "2010-10-10", 1, REFERENCES, 20)

    #test recover
    g.update_git_data("papyrus_db_test", "papyrus", "papyrus_repo", "C:\\Users\\atlanmod\\Desktop\\org.eclipse.papyrus", None, True, False, 20)


def test_5():
    g = Gitana(CONFIG, None)
    #g.delete_previous_logs()
    g.init_db("papyrus_db_test")

    g.create_project("papyrus_db_test", "papyrus")

    #test import full
    g.import_git_data("papyrus_db_test", "papyrus", "papyrus_repo", "C:\\Users\\atlanmod\\Desktop\\org.eclipse.papyrus", None, 1, None, 20)


def main():
    # print "starting 1.."
    # test_1()
    # print "starting 2.."
    # test_2()
    # print "starting 3.."
    # test_3()
    # print "starting 4.."
    # test_4()
    # print "starting 4a.."
    # test_4a()
    print "starting 5.."
    test_5()

if __name__ == "__main__":
    main()
