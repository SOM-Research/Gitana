#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'valerio cosentino'

from github import Github
from util.date_util import DateUtil
from util.token_util import TokenUtil


class GitHubQuerier():

    def __init__(self, url, token, logger):
        self.logger = logger
        self.url = url
        self.token_util = TokenUtil()
        self.token = token
        self.github = Github(token)
        self.repo = self.load_repo(self.url)
        self.date_util = DateUtil()

    def load_repo(self, url):
        repo = None
        try:
            repo = self.github.get_repo(url)
        except Exception, e:
            self.logger.error("Error loading repository " + url + "- " + e.message)
        return repo

    def get_issue_ids(self, before_date):
        issue_ids = []
        page_count = 1
        last_page = int(self.repo.get_issues(state="all", direction="asc")._getLastPageUrl().split("page=")[-1])

        while page_count != last_page:
            self.token_util.wait_is_usable(self.github)
            issues = self.repo.get_issues(state="all").get_page(page_count)
            for i in issues:
                if before_date:
                   if i.created_at <= self.date_util.get_timestamp(before_date, "%Y-%m-%d"):
                       issue_ids.append(i.number)
                else:
                    issue_ids.append(i.number)

            page_count += 1

        return issue_ids

    def get_issue(self, issue_id):
        self.token_util.wait_is_usable(self.github)
        return self.repo.get_issue(issue_id)

    def get_issue_summary(self, issue):
        return issue.title

    def get_issue_body(self, issue):
        return issue.body

    def get_issue_version(self, issue):
        version = None
        if issue.milestone is not None:
            version = issue.milestone.number
        return version

    def get_issue_creation_time(self, issue):
        return issue.created_at

    def get_issue_last_change_time(self, issue):
        return issue.updated_at

    def get_issue_creator(self, issue):
        try:
            found = issue.user
        except:
            found = None

        return found

    def get_user_email(self, user):
        try:
            found = user.email
        except:
            found = None

        return found

    def get_user_name(self, user):
        try:
            found = user.login
        except:
            found = None

        return found

    def get_issue_tags(self, issue):
        labels = []
        for label in issue.get_labels():
            self.token_util.wait_is_usable(self.github)
            labels.append(label.name)

        return labels

    def get_issue_comments(self, issue):
        comments = []
        for comment in issue.get_comments():
            self.token_util.wait_is_usable(self.github)
            comments.append(comment)

        return comments

    def get_issue_comment_id(self, issue_comment):
        return issue_comment.id

    def get_issue_comment_body(self, issue_comment):
        return issue_comment.body

    def get_issue_comment_author(self, issue_comment):
        return issue_comment.user

    def get_issue_comment_creation_time(self, issue_comment):
        return issue_comment.created_at

    def get_event_creation_time(self, event):
        return event.created_at

    def get_event_actor(self, event):
        return event.actor

    def get_issue_history(self, issue):
        events = []
        for event in issue.get_events():
            self.token_util.wait_is_usable(self.github)
            events.append(event)

        return events

    def find_user(self, login):
        found = None
        users = self.github.search_users(login, **{"type": "user", "in": "login"})
        for user in users:
            found = user
            break
        return found

    def get_issue_subscribers(self, history):
        subscribers = []
        for event in history:
            if event.event == "subscribed":
                subscribers.append(event.actor)
        return subscribers

    def get_issue_assignees(self, history):
        assignees = []
        for event in history:
            if event.event in ["assigned", "unassigned"]:
                if event.event == "assigned":
                    assignees.append(event._rawData.get('assignee'))
                elif event.event == "unassigned":
                    assignees.remove(event._rawData.get('assignee'))
        return assignees

    def get_commit_dependencies(self, history):
        commit_dependencies = []
        for event in history:
            if event.event == "referenced":
                commit_dependencies.append(event.commit_id)
        return commit_dependencies