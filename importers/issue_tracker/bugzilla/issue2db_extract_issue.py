#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'valerio cosentino'

from datetime import datetime
import re
from email.utils import parseaddr
import sys

from querier_bugzilla import BugzillaQuerier
from util.date_util import DateUtil
from bugzilla_dao import BugzillaDao
from util.logging_util import LoggingUtil


class BugzillaIssue2Db(object):
    """
    This class handles the import of Bugzilla issues
    """

    def __init__(self, db_name,
                 repo_id, issue_tracker_id, url, product, interval,
                 config, log_root_path):
        """
        :type db_name: str
        :param db_name: the name of an existing DB

        :type repo_id: int
        :param repo_id: the id of an existing repository in the DB

        :type issue_tracker_id: int
        :param issue_tracker_id: the id of an existing issue tracker in the DB

        :type url: str
        :param url: the URL of the bugzilla issue tracker

        :type product: str
        :param product: the name of the product in the bugzilla issue tracker

        :type interval: list int
        :param interval: a list of issue ids to import

        :type config: dict
        :param config: the DB configuration file

        :type log_root_path: str
        :param log_root_path: the log path
        """
        self._log_root_path = log_root_path
        self._url = url
        self._product = product
        self._db_name = db_name
        self._repo_id = repo_id
        self._issue_tracker_id = issue_tracker_id
        self._interval = interval
        self._config = config

        self._logging_util = LoggingUtil()
        self._date_util = DateUtil()

        self._fileHandler = None
        self._logger = None
        self._querier = None
        self._dao = None

    def __call__(self):
        try:
            log_path = self._log_root_path + "-issue2db-" + str(self._interval[0]) + "-" + str(self._interval[-1])
            self._logger = self._logging_util.get_logger(log_path)
            self._fileHandler = self._logging_util.get_file_handler(self._logger, log_path, "info")

            self._querier = BugzillaQuerier(self._url, self._product, self._logger)
            self._dao = BugzillaDao(self._config, self._logger)
            self.extract()
        except Exception:
            self._logger.error("BugzillaIssue2Db failed", exc_info=True)
        finally:
            if self._dao:
                self._dao.close_connection()

    def _is_email(self, str):
        # checks that a string is an email
        return parseaddr(str)[1] != '' and '@' in str

    def _extract_attachment(self, issue_comment_id, attachment_id):
        # inserts an attachment
        attachment_info = self._querier.get_attachment(attachment_id)
        if '.' in attachment_info.name:
            name = ('.').join(attachment_info.name.split('.')[:-1]).strip()
            extension = attachment_info.name.split('.')[-1].lower()
        else:
            name = attachment_info.name
            extension = "patch"

        size = sys.getsizeof(attachment_info)
        self._dao.insert_attachment(attachment_id, issue_comment_id, name, extension, size, None)

    def _extract_issue_event(self, action, action_content, creator_id, created_at, issue_id, field_name):
        # inserts an issue event
        event_type = action + '-' + field_name
        self._dao.insert_event_type(event_type)
        event_type_id = self._dao.select_event_type(event_type)
        target_user_id = None

        if ',' in action_content and field_name in ["keywords", "depends_on",
                                                    "cc", "flagtypes.name",
                                                    "blocks", "whiteboard", "see_also"]:
            contents = action_content.split(',')
            for content in contents:
                content = content.strip()
                if self._is_email(content):
                    target_user_id = self._dao.get_user_id(self._querier.get_user_name(content), content)

                self._dao.insert_issue_event(issue_id, event_type_id, content, creator_id, created_at, target_user_id)
        else:
            if self._is_email(action_content):
                target_user_id = self._dao.get_user_id(self._querier.get_user_name(action_content), action_content)

            self._dao.insert_issue_event(issue_id, event_type_id, action_content,
                                         creator_id, created_at, target_user_id)

    def _extract_history(self, issue_id, history):
        # inserts the history of an issue
        for event in history:
            try:
                created_at = self._date_util.get_timestamp(self._querier.get_event_property(event, 'when'),
                                                           '%Y%m%dT%H:%M:%S')
                creator_email = self._querier.get_event_property(event, 'who')
                creator_id = self._dao.get_user_id(self._querier.get_user_name(creator_email), creator_email)

                for change in self._querier.get_event_property(event, 'changes'):
                    removed = self._querier.get_change_property(change, 'removed')
                    field_name = self._querier.get_change_property(change, 'field_name').lower()
                    added = self._querier.get_change_property(change, 'added')

                    if removed != '':
                        action = "removed"
                        self._extract_issue_event(action, removed, creator_id, created_at, issue_id, field_name)

                    if added != '':
                        action = "added"
                        self._extract_issue_event(action, added, creator_id, created_at, issue_id, field_name)
            except Exception:
                self._logger.warning("event at (" + str(created_at) + ") not extracted for issue id: " +
                                     str(issue_id) + " - tracker id " + str(self._issue_tracker_id),
                                     exc_info=True)

    def _extract_subscribers(self, issue_id, subscribers):
        # inserts subscribers of an issue
        for subscriber in subscribers:
            try:
                subscriber_id = self._dao.get_user_id(self._querier.get_user_name(subscriber), subscriber)
                self._dao.insert_subscriber(issue_id, subscriber_id)
            except Exception:
                self._logger.warning("subscriber (" + subscriber + ") not inserted for issue id: " +
                                     str(issue_id) + " - tracker id " + str(self._issue_tracker_id),
                                     exc_info=True)

    def _extract_assignee(self, issue_id, assignee):
        # inserts the assignee of an issue
        try:
            assignee_id = self._dao.get_user_id(self._querier.get_user_name(assignee), assignee)
            self._dao.insert_assignee(issue_id, assignee_id)
        except Exception:
            self._logger.warning("assignee (" + assignee + ") not inserted for issue id: " + str(issue_id) +
                                 " - tracker id " + str(self._issue_tracker_id), exc_info=True)

    def _extract_comments(self, issue_id, comments):
        # inserts the comments of an issue
        for comment in comments:
            try:
                own_id = self._querier.get_comment_property(comment, 'id')
                body = self._querier.get_comment_property(comment, 'text')
                position = self._querier.get_comment_property(comment, 'count')
                author_email = self._querier.get_comment_property(comment, 'author')
                author_id = self._dao.get_user_id(self._querier.get_user_name(author_email), author_email)
                created_at = self._date_util.get_timestamp(self._querier.get_comment_property(comment, 'creation_time'),
                                                           '%Y%m%dT%H:%M:%S')
                self._dao.insert_issue_comment(own_id, position, self._dao.get_message_type_id("comment"),
                                               issue_id, body, None, author_id, created_at)

                attachment_id = self._querier.get_comment_property(comment, 'attachment_id')
                if attachment_id:
                    issue_comment_id = self._dao.select_issue_comment_id(own_id, issue_id, created_at)
                    self._extract_attachment(issue_comment_id, attachment_id)
            except Exception:
                self._logger.warning("comment(" + str(position) + ") not extracted for issue id: " + str(issue_id) +
                                     " - tracker id " + str(self._issue_tracker_id),
                                     exc_info=True)
                continue

    def _extract_labels(self, issue_id, labels):
        # inserts the labels of an issue
        for label in labels:
            try:
                digested_label = re.sub("^\W+", "", re.sub("\W+$", "", label.lower()))
                self._dao.insert_label(digested_label.strip())
                label_id = self._dao.select_label_id(digested_label)
                self._dao.assign_label_to_issue(issue_id, label_id)
            except Exception:
                self._logger.warning("label (" + label + ") not extracted for issue id: " + str(issue_id) +
                                     " - tracker id " + str(self._issue_tracker_id), exc_info=True)

    def _extract_issue_commit_dependency(self, issue_id, commits):
        # inserts the dependencies between an issue and commits
        flattened_list = [y for x in commits for y in x]
        for id in flattened_list:
            if "commit" in id:
                extracted = id.split("?id=")[1].strip()
                commit_id = self._dao.select_commit(extracted, self._repo_id)
                self._dao.insert_issue_commit_dependency(issue_id, commit_id)

    def _is_duplicated(self, issue):
        flag = True
        try:
            issue.dupe_of
        except:
            flag = False

        return flag

    def _get_issue_info(self, issue_own_id):
        # processes each single issue
        flag_insert_issue_data = False

        issue = self._querier.get_issue(issue_own_id)
        summary = self._querier.get_issue_summary(issue)
        component = self._querier.get_issue_component(issue)
        version = self._querier.get_issue_version(issue)
        hardware = self._querier.get_issue_operating_system(issue)
        priority = self._querier.get_issue_priority(issue)
        severity = self._querier.get_issue_severity(issue)
        created_at = self._querier.get_issue_creation_time(issue)
        last_change_at = self._querier.get_issue_last_change_time(issue)

        reference_id = self._dao.find_reference_id(version, issue_own_id, self._repo_id)

        issue_creator_email = self._querier.get_issue_creator(issue)
        user_id = self._dao.get_user_id(self._querier.get_user_name(issue_creator_email), issue_creator_email)

        stored_issue_last_change = self._dao.select_last_change_issue(issue_own_id,
                                                                      self._issue_tracker_id, self._repo_id)
        if stored_issue_last_change:
            if last_change_at != stored_issue_last_change:
                flag_insert_issue_data = True
                self._dao.update_issue(issue_own_id, self._issue_tracker_id, summary, component, version, hardware,
                                       priority, severity, reference_id, last_change_at)
        else:
            flag_insert_issue_data = True
            self._dao.insert_issue(issue_own_id, self._issue_tracker_id, summary, component, version, hardware,
                                   priority, severity, reference_id, user_id, created_at, last_change_at)

        if flag_insert_issue_data:
            issue_id = self._dao.select_issue_id(issue_own_id, self._issue_tracker_id, self._repo_id)

            try:
                self._extract_labels(issue_id, self._querier.get_issue_keywords(issue))
            except Exception:
                self._logger.error("BugzillaError when extracting keywords for issue id: " + str(issue_id) +
                                   " - tracker id " + str(self._issue_tracker_id), exc_info=True)

            try:
                self._extract_comments(issue_id, self._querier.get_issue_comments(issue))
            except Exception:
                self._logger.error("BugzillaError when extracting comments for issue id: " + str(issue_id) +
                                   " - tracker id " + str(self._issue_tracker_id), exc_info=True)

            try:
                self._extract_history(issue_id, self._querier.get_issue_history(issue))
            except Exception:
                self._logger.error("BugzillaError when extracting history for issue id: " + str(issue_id) +
                                   " - tracker id " + str(self._issue_tracker_id), exc_info=True)

            if issue.cc:
                self._extract_subscribers(issue_id, self._querier.get_issue_cc(issue))

            if issue.assigned_to:
                self._extract_assignee(issue_id, self._querier.get_issue_assignee(issue))

            if issue.see_also:
                self._extract_issue_commit_dependency(issue_id, [self._querier.get_issue_see_also(issue)])

    def _get_issues(self):
        # processes issues
        for issue_id in self._interval:
            try:
                self._get_issue_info(issue_id)
            except Exception:
                self._logger.error("something went wrong for issue id: " + str(issue_id) + " - tracker id " +
                                   str(self._issue_tracker_id), exc_info=True)

    def extract(self):
        """
        extracts Bugzilla issue data and stores it in the DB
        """
        try:
            self._logger.info("BugzillaIssue2Db started")
            start_time = datetime.now()
            self._get_issues()

            end_time = datetime.now()
            minutes_and_seconds = self._logging_util.calculate_execution_time(end_time, start_time)
            self._logger.info("BugzillaIssue2Db finished after " + str(minutes_and_seconds[0]) +
                              " minutes and " + str(round(minutes_and_seconds[1], 1)) + " secs")
            self._logging_util.remove_file_handler_logger(self._logger, self._fileHandler)
        except Exception:
            self._logger.error("BugzillaIssue2Db failed", exc_info=True)
