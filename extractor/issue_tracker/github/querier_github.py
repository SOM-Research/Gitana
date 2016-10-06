#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = '...'

# Data about project's issues should be obtained using the GitHub API through OAuth tokens.
# https://help.github.com/articles/git-automation-with-oauth-tokens/
# https://developer.github.com/v3/issues/
# https://developer.github.com/v3/activity/events/types/ (types xii and xiii)

# In order to query the GitHub API through Python, you can use PyGitHub
# https://pypi.python.org/pypi/PyGithub
# http://pygithub.readthedocs.io/en/latest/introduction.html

#This script should contain the code to interact with PyGitHub.

from github import Github

TOKEN = '013ab2fcdf56b46c856beeb5ad934f7a0926e200'


def check_rate_limit():
    g = Github()
    print "unauthenticated access - rate limit: " + str(g.get_rate_limit().rate.remaining)

    g = Github(TOKEN)
    print "authenticated access - rate limit: " + str(g.get_rate_limit().rate.remaining)


def issue_access():
    g = Github(TOKEN)
    repo = g.get_repo("gabrielecirulli/2048")

    # with pagination
    page_count = 1
    last_page = int(repo.get_issues(state="all", direction="asc")._getLastPageUrl().split("page=")[-1])

    while page_count != last_page:
        issues = repo.get_issues(state="all", direction="asc").get_page(page_count)
        for i in issues:
            print str(i.number) + " " + i.title
        page_count += 1

    print "--- --- --- --- ---"

    # without pagination
    issues = repo.get_issues(state="all", direction="asc")
    for i in issues:
        print str(i.number) + " " + i.title


def main():
    issue_access()

if __name__ == "__main__":
    main()

