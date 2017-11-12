#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'valerio cosentino'

from github import Github
from util.date_util import DateUtil
from util.token_util import TokenUtil
import re


class GitHubQuerier():
    """
    This class collects the data available on the GitHub issue tracker via its API
    """

    def __init__(self, url, token, logger):
        """
        :type url: str
        :param url: full name of the GitHub repository

        :type token: str
        :param token: a GitHub token

        :type logger: Object
        :param logger: logger
        """
        try:
            self._logger = logger
            self._url = url
            self._token = token
            self._github = Github(token)
            self._repo = self._load_repo(self._url)
            self._token_util = TokenUtil(self._logger, "github")
            self._date_util = DateUtil()
        except:
            self._logger.error("GitHubQuerier init failed")
            raise

    def _load_repo(self, url):
        # connect to the GitHub API
        try:
            repo = self._github.get_repo(url)
            return repo
        except Exception:
            self._logger.error("GitHubQuerier error loading repository " + url + "- ", exc_info=True)
            raise

    def get_issue_ids(self, before_date):
        """
        gets data source issue ids

        :type before_date: str
        :param before_date: selects issues with creation date before a given date (YYYY-mm-dd)
        """
        issue_ids = []
        page_count = 0
        self._token_util.wait_is_usable(self._github)
        last_page = int(self._repo.get_issues(state="all", direction="asc")._getLastPageUrl().split("page=")[-1])

        while page_count != last_page + 1:
            self._token_util.wait_is_usable(self._github)
            issues = self._repo.get_issues(state="all").get_page(page_count)
            for i in issues:
                if before_date:
                    if i.created_at <= self._date_util.get_timestamp(before_date, "%Y-%m-%d"):
                        issue_ids.append(i.number)
                else:
                    issue_ids.append(i.number)

            page_count += 1

        if issue_ids:
            issue_ids.sort()

        return issue_ids

    def get_issue(self, issue_id):
        """
        gets issue

        :type issue_id: int
        :param issue_id: data source issue id
        """
        self._token_util.wait_is_usable(self._github)
        return self._repo.get_issue(issue_id)

    def get_issue_summary(self, issue):
        """
        gets summary of the issue

        :type issue: Object
        :param issue: the Object representing the issue
        """
        return issue.title

    def get_issue_body(self, issue):
        """
        gets body of the issue

        :type issue: Object
        :param issue: the Object representing the issue
        """
        return issue.body

    def get_issue_version(self, issue):
        """
        gets version of the issue

        :type issue: Object
        :param issue: the Object representing the issue
        """
        version = None
        if issue.milestone is not None:
            version = issue.milestone.number
        return version

    def get_issue_creation_time(self, issue):
        """
        gets creation time of the issue

        :type issue: Object
        :param issue: the Object representing the issue
        """
        return issue.created_at

    def get_issue_last_change_time(self, issue):
        """
        gets last change date of the issue

        :type issue: Object
        :param issue: the Object representing the issue
        """
        return issue.updated_at

    def get_issue_creator(self, issue):
        """
        gets creator of the issue

        :type issue: Object
        :param issue: the Object representing the issue
        """
        try:
            found = issue.user
        except:
            found = None

        return found

    def get_user_email(self, user):
        """
        gets the email of the issue creator

        :type user: Object
        :param user: the Object representing the user
        """
        try:
            found = user.email
        except:
            found = None

        return found

    def get_user_name(self, user):
        """
        gets the user name of the issue creator

        :type user: Object
        :param user: the Object representing the user
        """
        try:
            found = user.login
        except:
            found = None

        return found

    def get_issue_tags(self, issue):
        """
        gets labels of the issue

        :type issue: Object
        :param issue: the Object representing the issue
        """
        labels = []
        self._token_util.wait_is_usable(self._github)
        for label in issue.get_labels():
            labels.append(label.name)

        return labels

    def get_issue_comments(self, issue):
        """
        gets the comments of the issue

        :type issue: Object
        :param issue: the Object representing the issue
        """
        comments = []
        self._token_util.wait_is_usable(self._github)
        for comment in issue.get_comments():
            comments.append(comment)

        return comments

    def get_issue_comment_id(self, issue_comment):
        """
        gets the id of the issue comment

        :type issue_comment: Object
        :param issue_comment: the Object representing the issue comment
        """
        return issue_comment.id

    def get_issue_comment_body(self, issue_comment):
        """
        gets the body of the issue comment

        :type issue_comment: Object
        :param issue_comment: the Object representing the issue comment
        """
        return issue_comment.body

    def get_issue_comment_author(self, issue_comment):
        """
        gets the author of the issue comment

        :type issue_comment: Object
        :param issue_comment: the Object representing the issue comment
        """
        return issue_comment.user

    def get_issue_comment_creation_time(self, issue_comment):
        """
        gets the creation time of the issue comment

        :type issue_comment: Object
        :param issue_comment: the Object representing the issue comment
        """
        return issue_comment.created_at

    def generate_attachment_id(self, message_id, pos):
        """
        creates the attachment id

        :type message_id: int
        :param message_id: the data source message id

        :type pos: int
        :param pos: position of the message
        """
        return str(message_id) + str(pos)

    def get_attachments(self, comment):
        """
        gets the attachements within a comment

        :type comment: str
        :param comment: content of the comment
        """
        p = re.compile("\[.*\]\(http.*\)", re.MULTILINE)
        matches = p.findall(comment)

        attachments = []
        for m in matches:
            attachments.append(m)
        return attachments

    def get_attachment_name(self, text):
        """
        gets the name of the attachement

        :type text: str
        :param text: content of the comment
        """
        parts = text.split('](')
        name = parts[0].lstrip('[')

        found = name

        if not found:
            found = parts[1].split('/')[-1]

        return found

    def get_attachment_url(self, text):
        """
        gets the URL of the attachement

        :type text: str
        :param text: content of the comment
        """
        parts = text.split('](')
        return parts[1].rstrip(')')

    def get_referenced_issues(self, comment):
        """
        gets the referenced issues within a comment

        :type comment: str
        :param comment: content of the comment
        """
        p = re.compile('#\d+', re.MULTILINE)

        matches = p.findall(comment)

        referenced_issues = []
        for m in matches:
            referenced_issues.append(m.strip('#'))

        return referenced_issues

    def get_event_creation_time(self, event):
        """
        gets the creation time of an event

        :type event: Object
        :param event: the Object representing the event
        """
        return event.created_at

    def get_event_actor(self, event):
        """
        gets the actor of an event

        :type event: Object
        :param event: the Object representing the event
        """
        return event.actor

    def get_issue_history(self, issue):
        """
        gets the event history of an issue

        :type issue: Object
        :param issue: the Object representing the issue
        """
        events = []
        self._token_util.wait_is_usable(self._github)
        for event in issue.get_events():
            events.append(event)

        return events

    def regenerate_token(self):
        """
        regenerate GitHub token
        """
        self._github = Github(self._token)

    def find_user(self, login):
        """
        finds GitHub user

        :type login: str
        :param login: GitHub username
        """
        found = None
        self._token_util.wait_is_usable(self._github)
        users = self._github.search_users(login, **{"type": "user", "in": "login"})
        for user in users:
            found = user
            break
        return found

    def get_issue_subscribers(self, history):
        """
        gets subscribers of an issue

        :type history: Object
        :param history: the Object representing the events of an issue
        """
        subscribers = []
        for event in history:
            if event.event == "subscribed":
                subscribers.append(event.actor)
        return subscribers

    def get_issue_assignees(self, history):
        """
        gets assignees of an issue

        :type history: Object
        :param history: the Object representing the events of an issue
        """
        assignees = []
        for event in history:
            if event.event in ["assigned", "unassigned"]:
                if event.event == "assigned":
                    assignees.append(event._rawData.get('assignee'))
                elif event.event == "unassigned":
                    assignees.remove(event._rawData.get('assignee'))
        return assignees

    def get_commit_dependencies(self, history):
        """
        gets dependencies between an issue and commits

        :type history: Object
        :param history: the Object representing the events of an issue
        """
        commit_dependencies = []
        for event in history:
            if event.event == "referenced":
                commit_dependencies.append(event.commit_id)
        return commit_dependencies

    def get_author_by_commit(self, sha):
        self._token_util.wait_is_usable(self._github)
        commit = self._repo.get_commit(sha)
        return commit.author
