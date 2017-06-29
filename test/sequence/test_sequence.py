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

GH_TOKENS = ['1',
             '2',
             '3',
             '4',
             '5']


def _papyrus():
    g = Gitana(CONFIG, None)
    g.delete_previous_logs()
    g.init_db("db_papyrus")
    g.create_project("db_papyrus", "papyrus")
    #print "import git data"
    #g.import_git_data("db_papyrus", "papyrus", "papyrus_repo", "C:\\Users\\atlanmod\\Desktop\\eclipse-git-projects\\papyrus", processes=20)
    print "import bugzilla data"
    g.import_bugzilla_issue_data("_papyrus_db", "papyrus", "papyrus_repo", "bugzilla-papyrus", "https://bugs.eclipse.org/bugs/xmlrpc.cgi", "papyrus", processes=10)
    print "import eclipse forum data"
    g.import_eclipse_forum_data("_papyrus_db", "papyrus", "papyrus-eclipse", "https://www.eclipse.org/forums/index.php/f/121/", processes=4)
    print "import stackoverflow data"
    g.import_stackoverflow_data("_papyrus_db", "papyrus", "papyrus-stackoverflow", "papyrus", ['IFco1Gh5EJ*U)ZY5)16ZKQ(('])


def _2048():
    g = Gitana(CONFIG, None)
    g.delete_previous_logs()
    g.init_db("db_2048")
    g.create_project("db_2048", "2048")
    print "import git data"
    g.import_git_data("db_2048", "2048", "repo_2048", "C:\\Users\\atlanmod\\Desktop\\oss\\ants-work\\github-repos\\2048", import_type=2)
    print "import github data"
    g.import_github_issue_data("db_2048", "2048", "repo_2048", "2048_it", "gabrielecirulli/2048", GH_TOKENS)


def main():
    #_2048()
    _papyrus()

if __name__ == "__main__":
    main()
