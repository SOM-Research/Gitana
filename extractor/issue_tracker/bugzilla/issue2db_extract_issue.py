#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'valerio cosentino'

from datetime import datetime
import re
from email.utils import parseaddr

from querier_bugzilla import BugzillaQuerier
from util.date_util import DateUtil
from bugzilla_dao import BugzillaDao
from util.logging_util import LoggingUtil


class BugzillaIssue2Db(object):

    def __init__(self, db_name,
                 repo_id, issue_tracker_id, url, product, interval,
                 config, log_path):
        self.log_path = log_path
        self.url = url
        self.product = product
        self.db_name = db_name
        self.repo_id = repo_id
        self.issue_tracker_id = issue_tracker_id
        self.interval = interval
        self.fileHandler = None
        config.update({'database': db_name})
        self.config = config
        self.logging_util = LoggingUtil()
        self.date_util = DateUtil()

    def __call__(self):
        log_filename = self.log_path + "-issue2db-" + str(self.interval[0]) + "-" + str(self.interval[-1])
        self.logger = self.logging_util.get_logger(log_filename)
        self.fileHandler = self.logging_util.get_file_handler(self.logger, log_filename, "info")

        try:
            self.querier = BugzillaQuerier(self.url, self.product, self.logger)
            self.dao = BugzillaDao(self.config, self.logger)
            self.extract()
        except Exception, e:
            self.logger.error("Issue2Db failed", exc_info=True)

    def is_email(self, str):
        return parseaddr(str)[1] != '' and '@' in str

    def extract_attachment(self, issue_comment_id, attachment_id):
        attachment_info = self.querier.get_attachment(attachment_id)
        if '.' in attachment_info.name:
            name = ('.').join(attachment_info.name.split('.')[:-1]).strip()
            extension = attachment_info.name.split('.')[-1].lower()
        else:
            name = attachment_info.name
            extension = "patch"

        size = sys.getsizeof(attachment_info)
        self.dao.insert_attachment(attachment_id, issue_comment_id, name, extension, size, None)

    def extract_issue_event(self, action, action_content, creator_id, created_at, issue_id, field_name):
        event_type = action + '-' + field_name
        self.dao.insert_event_type(event_type)
        event_type_id = self.dao.select_event_type(event_type)
        target_user_id = None

        if ',' in action_content and field_name in ["keywords", "depends_on", "cc", "flagtypes.name", "blocks", "whiteboard", "see_also"]:
            contents = action_content.split(',')
            for content in contents:
                content = content.strip()
                if self.is_email(content):
                    target_user_id = self.dao.get_user_id(self.querier.get_user_name(content), content)

                self.dao.insert_issue_event(issue_id, event_type_id, content, creator_id, created_at, target_user_id)
        else:
            if self.is_email(action_content):
                target_user_id = self.dao.get_user_id(self.querier.get_user_name(action_content), action_content)

            self.dao.insert_issue_event(issue_id, event_type_id, action_content, creator_id, created_at, target_user_id)

    def extract_history(self, issue_id, history):
        for event in history:
            try:
                created_at = self.date_util.get_timestamp(self.querier.get_event_property(event, 'when'), '%Y%m%dT%H:%M:%S')
                creator_email = self.querier.get_event_property(event, 'who')
                creator_id = self.dao.get_user_id(self.querier.get_user_name(creator_email), creator_email)

                for change in self.querier.get_event_property(event, 'changes'):
                    removed = self.querier.get_change_property(change, 'removed')
                    field_name = self.querier.get_change_property(change, 'field_name').lower()
                    added = self.querier.get_change_property(change, 'added')

                    if removed != '':
                        action = "removed"
                        self.extract_issue_event(action, removed, creator_id, created_at, issue_id, field_name)

                    if added != '':
                        action = "added"
                        self.extract_issue_event(action, added, creator_id, created_at, issue_id, field_name)
            except Exception, e:
                self.logger.warning("event at (" + str(created_at) + ") not extracted for issue id: " + str(issue_id) + " - tracker id " + str(self.issue_tracker_id), exc_info=True)

    def extract_subscribers(self, issue_id, subscribers):
        for subscriber in subscribers:
            try:
                subscriber_id = self.dao.get_user_id(self.querier.get_user_name(subscriber), subscriber)
                self.dao.insert_subscriber(issue_id, subscriber_id)
            except Exception, e:
                self.logger.warning("subscriber (" + subscriber + ") not inserted for issue id: " + str(issue_id) + " - tracker id " + str(self.issue_tracker_id), exc_info=True)

    def extract_assignee(self, issue_id, assignee):
        try:
            assignee_id = self.dao.get_user_id(self.querier.get_user_name(assignee), assignee)
            self.dao.insert_assignee(issue_id, assignee_id)
        except Exception, e:
            self.logger.warning("assignee (" + assignee + ") not inserted for issue id: " + str(issue_id) + " - tracker id " + str(self.issue_tracker_id), exc_info=True)

    def extract_comments(self, issue_id, comments):
        for comment in comments:
            try:
                own_id = self.querier.get_comment_property(comment, 'id')
                body = self.querier.get_comment_property(comment, 'text')
                position = self.querier.get_comment_property(comment, 'count')
                author_email = self.querier.get_comment_property(comment, 'author')
                author_id = self.dao.get_user_id(self.querier.get_user_name(author_email), author_email)
                created_at = self.date_util.get_timestamp(self.querier.get_comment_property(comment, 'creation_time'), '%Y%m%dT%H:%M:%S')
                self.dao.insert_issue_comment(own_id, position, self.dao.get_message_type_id("comment"), issue_id, body, None, author_id, created_at)

                attachment_id = self.querier.get_comment_property(comment, 'attachment_id')
                if attachment_id:
                    issue_comment_id = self.dao.select_issue_comment_id(own_id, issue_id, created_at)
                    self.extract_attachment(issue_comment_id, attachment_id)
            except Exception, e:
                self.logger.warning("comment(" + str(position) + ") not extracted for issue id: " + str(issue_id) + " - tracker id " + str(self.issue_tracker_id), exc_info=True)
                continue

    def extract_labels(self, issue_id, labels):
        for label in labels:
            try:
                digested_label = re.sub("^\W+", "", re.sub("\W+$", "", label.lower()))
                self.dao.insert_label(digested_label.strip())
                label_id = self.dao.select_label_id(digested_label)
                self.dao.assign_label_to_issue(issue_id, label_id)
            except Exception, e:
                self.logger.warning("label (" + label + ") not extracted for issue id: " + str(issue_id) + " - tracker id " + str(self.issue_tracker_id), exc_info=True)

    def extract_issue_commit_dependency(self, issue_id, commits):
        flattened_list = [y for x in commits for y in x]
        for id in flattened_list:
            if "commit" in id:
                extracted = id.split("?id=")[1].strip()
                commit_id = self.dao.select_commit(extracted, self.repo_id)
                self.dao.insert_issue_commit_dependency(issue_id, commit_id)

    def is_duplicated(self, issue):
        flag = True
        try:
            issue.dupe_of
        except:
            flag = False

        return flag

    def get_issue_info(self, issue_own_id):
        flag_insert_issue_data = False

        issue = self.querier.get_issue(issue_own_id)
        summary = self.querier.get_issue_summary(issue)
        component = self.querier.get_issue_component(issue)
        version = self.querier.get_issue_version(issue)
        hardware = self.querier.get_issue_operating_system(issue)
        priority = self.querier.get_issue_priority(issue)
        severity = self.querier.get_issue_severity(issue)
        created_at = self.querier.get_issue_creation_time(issue)
        last_change_at = self.querier.get_issue_last_change_time(issue)

        reference_id = self.dao.find_reference_id(version, issue_own_id, self.repo_id)

        issue_creator_email = self.querier.get_issue_creator(issue)
        user_id = self.dao.get_user_id(self.querier.get_user_name(issue_creator_email), issue_creator_email)

        stored_issue_last_change = self.dao.select_last_change_issue(issue_own_id, self.issue_tracker_id, self.repo_id)
        if stored_issue_last_change:
            if last_change_at != stored_issue_last_change:
                flag_insert_issue_data = True
                self.dao.update_issue(issue_own_id, self.issue_tracker_id, summary, component, version, hardware, priority, severity, reference_id, last_change_at)
        else:
            flag_insert_issue_data = True
            self.dao.insert_issue(issue_own_id, self.issue_tracker_id, summary, component, version, hardware, priority, severity, reference_id, user_id, created_at, last_change_at)

        if flag_insert_issue_data:
            issue_id = self.dao.select_issue_id(issue_own_id, self.issue_tracker_id, self.repo_id)
            #tags and keywords are mapped as labels
            try:
                self.extract_labels(issue_id, self.querier.get_issue_tags(issue))
            except Exception, e:
                self.logger.error("BugzillaError when extracting tags for issue id: " + str(issue_id) + " - tracker id " + str(self.issue_tracker_id), exc_info=True)

            try:
                self.extract_labels(issue_id, self.querier.get_issue_keywords(issue))
            except Exception, e:
                self.logger.error("BugzillaError when extracting keywords for issue id: " + str(issue_id) + " - tracker id " + str(self.issue_tracker_id), exc_info=True)

            try:
                self.extract_comments(issue_id, self.querier.get_issue_comments(issue))
            except Exception, e:
                self.logger.error("BugzillaError when extracting comments for issue id: " + str(issue_id) + " - tracker id " + str(self.issue_tracker_id), exc_info=True)

            try:
                self.extract_history(issue_id, self.querier.get_issue_history(issue))
            except Exception, e:
                self.logger.error("BugzillaError when extracting history for issue id: " + str(issue_id) + " - tracker id " + str(self.issue_tracker_id), exc_info=True)

            if issue.cc:
                self.extract_subscribers(issue_id, self.querier.get_issue_cc(issue))

            if issue.assigned_to:
                self.extract_assignee(issue_id, self.querier.get_issue_assignee(issue))

            if issue.see_also:
                self.extract_issue_commit_dependency(issue_id, [self.querier.get_issue_see_also(issue)])

    def get_issues(self):
        for issue_id in self.interval:
            try:
                self.get_issue_info(issue_id)
            except Exception, e:
                self.logger.error("something went wrong for issue id: " + str(issue_id) + " - tracker id " + str(self.issue_tracker_id), exc_info=True)
        self.dao.close_connection()

    def extract(self):
        try:
            start_time = datetime.now()
            self.get_issues()
            end_time = datetime.now()

            minutes_and_seconds = divmod((end_time-start_time).total_seconds(), 60)
            self.logger.info("BugzillaIssue2Db finished after " + str(minutes_and_seconds[0])
                           + " minutes and " + str(round(minutes_and_seconds[1], 1)) + " secs")
            self.logging_util.remove_file_handler_logger(self.logger, self.fileHandler)
        except Exception, e:
            self.logger.error("BugzillaIssue2Db failed", exc_info=True)