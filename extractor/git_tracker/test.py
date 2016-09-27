#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'valerio cosentino'

from git import *

GIT_REPO_PATH = "C:\\Users\\atlanmod\\Desktop\\rails"


def get_commits(repo, ref_name):
    commits = []
    for commit in repo.iter_commits(rev=ref_name):
        commits.append(commit)
    return commits


def main():
    repo = Repo(GIT_REPO_PATH, odbt=GitCmdObjectDB)
    for ref in repo.references[31:]:
        if ref.name:
            print ref.name
            print str(len(get_commits(repo, ref.name)))
            print "---"

if __name__ == "__main__":
    main()