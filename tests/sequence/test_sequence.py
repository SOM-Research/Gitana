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

GH_TOKENS = ['4e6560ede99ff11b926a411b590a8b51a1e98a0e']

SO_TOKENS = ['MxTbS3KBl76SP6KCyT*DsA((']


def _papyrus():
    g = Gitana(CONFIG, None)
    g.delete_previous_logs()
    g.init_db("db_papyrus")
    g.create_project("db_papyrus", "papyrus")
    print("import git data")
    g.import_git_data("db_papyrus", "papyrus", "papyrus_repo",
                      "C:\\Users\\atlanmod\\Desktop\\eclipse-git-projects\\papyrus",
                      references=["0.7.0", "0.8.0", "0.9.0", "0.10.0", "1.0.0", "2.0.0"],
                      import_type=2,
                      processes=20)
    print("import bugzilla data")
    g.import_bugzilla_issue_data("db_papyrus", "papyrus", "papyrus_repo", "bugzilla-papyrus",
                                 "https://bugs.eclipse.org/bugs/xmlrpc.cgi", "papyrus", processes=10)
    print("import eclipse forum data")
    g.import_eclipse_forum_data("db_papyrus", "papyrus", "papyrus-eclipse",
                                "https://www.eclipse.org/forums/index.php/f/121/", processes=2)
    print("import stackoverflow data")
    g.import_stackoverflow_data("db_papyrus", "papyrus", "papyrus-stackoverflow", "papyrus", SO_TOKENS)


def _2048():
    g = Gitana(CONFIG, None)
    g.delete_previous_logs()
    g.init_db("db_2048")
    g.create_project("db_2048", "2048")
    print("import git data")
    g.import_git_data("db_2048", "2048", "repo_2048",
                      "C:\\Users\\atlanmod\\Desktop\\oss\\ants-work\\github-repos\\2048", import_type=2)
    print("import github data")
    g.import_github_issue_data("db_2048", "2048", "repo_2048", "2048_it", "gabrielecirulli/2048", GH_TOKENS)


def main():
    # _2048()
    _papyrus()


if __name__ == "__main__":
    main()
