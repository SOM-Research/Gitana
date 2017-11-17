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


GH_TOKENS = ['09c6bda73c01db106ccee55caa3b37d567b142cf']


def test(g):
    g.init_db("githubissue_2048")
    g.create_project("githubissue_2048", "2048")
    g.import_git_data("githubissue_2048", "2048", "repo_2048", "C:\\Users\\atlanmod\\Desktop\\2048")
    g.import_github_issue_data("githubissue_2048", "2048", "repo_2048", "2048-tracker", "gabrielecirulli/2048",
                               GH_TOKENS)


def main():
    g = Gitana(CONFIG)
    g.delete_previous_logs()

    print("starting ..")
    test(g)


if __name__ == "__main__":
    main()
