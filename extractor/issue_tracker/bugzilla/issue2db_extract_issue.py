#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'valerio cosentino'

import mysql.connector
from mysql.connector import errorcode
from datetime import datetime
import re
from email.utils import parseaddr
import sys
import logging
import logging.handlers
sys.path.insert(0, "..//..//..")

from querier_bugzilla import BugzillaQuerier
from extractor.util.db_util import DbUtil
from extractor.util.date_util import DateUtil


class Issue2Db(object):

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
        config.update({'database': db_name})
        self.config = config

        self.db_util = DbUtil()
        self.date_util = DateUtil()

    def __call__(self):
        LOG_FILENAME = self.log_path + "-issue2db"
        self.logger = logging.getLogger(LOG_FILENAME)
        fileHandler = logging.FileHandler(LOG_FILENAME + "-" + str(self.interval[0]) + "-" + str(self.interval[-1]) + ".log", mode='w')
        formatter = logging.Formatter("%(asctime)s:%(levelname)s:%(message)s", "%Y-%m-%d %H:%M:%S")

        fileHandler.setFormatter(formatter)
        self.logger.setLevel(logging.INFO)
        self.logger.addHandler(fileHandler)

        try:
            self.querier = BugzillaQuerier(self.url, self.product, self.logger)
            self.cnx = mysql.connector.connect(**self.config)
            self.extract()
        except Exception, e:
            self.logger.error("Issue2Db failed", exc_info=True)

    def update_issue(self, issue_id, issue_tracker_id, summary, component, version, hardware, priority, severity, reference_id, last_change_at):
        cursor = self.cnx.cursor()
        query = "UPDATE issue SET last_change_at = %s, summary = %s, component = %s, version = %s, hardware = %s, priority = %s, severity = %s, reference_id = %s WHERE own_id = %s AND issue_tracker_id = %s"
        arguments = [last_change_at, summary, component, version, hardware, priority, severity, reference_id, issue_id, issue_tracker_id]
        cursor.execute(query, arguments)
        self.cnx.commit()
        cursor.close()

    def insert_issue(self, issue_own_id, issue_tracker_id, summary, component, version, hardware, priority, severity, reference_id, user_id, created_at, last_change_at):
        cursor = self.cnx.cursor()
        query = "INSERT IGNORE INTO issue " \
                "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
        arguments = [None, issue_own_id, issue_tracker_id, summary, component, version, hardware, priority, severity, reference_id, user_id, created_at, last_change_at]
        cursor.execute(query, arguments)
        self.cnx.commit()
        cursor.close()

    def select_last_change_issue(self, issue_id):
        found = None

        cursor = self.cnx.cursor()
        query = "SELECT i.last_change_at " \
                "FROM issue i JOIN issue_tracker it ON i.issue_tracker_id = it.id " \
                "WHERE own_id = %s AND issue_tracker_id = %s AND repo_id = %s"
        arguments = [issue_id, self.issue_tracker_id, self.repo_id]
        cursor.execute(query, arguments)

        row = cursor.fetchone()
        cursor.close()

        if row:
            found = row[0]

        return found

    def find_reference_id(self, version, issue_id):
        found = None
        try:
            cursor = self.cnx.cursor()
            query = "SELECT id FROM reference WHERE name = %s AND repo_id = %s"
            arguments = [version, self.repo_id]
            cursor.execute(query, arguments)
            row = cursor.fetchone()
            if row:
                found = row[0]
            else:
                #sometimes the version is followed by extra information such as alpha, beta, RC, M.
                query = "SELECT id FROM reference WHERE name LIKE '" + version + "%' AND repo_id = " + str(self.repo_id)
                cursor.execute(query)
                row = cursor.fetchone()

                if row:
                    found = row[0]

            cursor.close()
        except Exception, e:
            self.logger.warning("version (" + version + ") not inserted for issue id: " + str(issue_id) + " - tracker id " + str(self.issue_tracker_id), exc_info=True)

        return found

    def insert_label(self, name):
        cursor = self.cnx.cursor()
        query = "INSERT IGNORE INTO label " \
                "VALUES (%s, %s)"
        arguments = [None, name]
        cursor.execute(query, arguments)
        self.cnx.commit()
        cursor.close()

    def select_label_id(self, name):
        cursor = self.cnx.cursor()
        query = "SELECT id FROM label WHERE name = %s"
        arguments = [name]
        cursor.execute(query, arguments)
        row = cursor.fetchone()
        found = None
        if row:
            found = row[0]
        cursor.close()

        return found

    def assign_label_to_issue(self, issue_id, label_id):
        cursor = self.cnx.cursor()
        query = "INSERT IGNORE INTO issue_labelled " \
                "VALUES (%s, %s)"
        arguments = [issue_id, label_id]
        cursor.execute(query, arguments)
        self.cnx.commit()
        cursor.close()

    def insert_issue_comment(self, own_id, position, issue_id, body, author_id, created_at):
        cursor = self.cnx.cursor()
        query = "INSERT IGNORE INTO message " \
                "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
        arguments = [None, own_id, position, self.db_util.get_message_type_id(self.cnx, "comment"),
                     issue_id, 0, 0, body, None, author_id, created_at]
        cursor.execute(query, arguments)
        self.cnx.commit()
        cursor.close()

    def select_issue_comment_id(self, own_id, issue_id, created_at):
        cursor = self.cnx.cursor()
        query = "SELECT id FROM message WHERE own_id = %s AND issue_id = %s AND created_at = %s"
        arguments = [own_id, issue_id, created_at]
        cursor.execute(query, arguments)
        row = cursor.fetchone()
        found = None
        if row:
            found = row[0]
        cursor.close()

        return found

    def insert_attachment(self, attachment_id, issue_comment_id, name, extension, size):
        cursor = self.cnx.cursor()
        query = "INSERT IGNORE INTO attachment " \
                "VALUES (%s, %s, %s, %s, %s, %s, %s)"
        arguments = [None, attachment_id, issue_comment_id, name, extension, size, None]
        cursor.execute(query, arguments)
        self.cnx.commit()
        cursor.close()

    def insert_event_type(self, name):
        cursor = self.cnx.cursor()
        query = "INSERT IGNORE INTO issue_event_type " \
                "VALUES (%s, %s)"
        arguments = [None, name]
        cursor.execute(query, arguments)
        self.cnx.commit()
        cursor.close()

    def select_event_type(self, name):
        cursor = self.cnx.cursor()
        query = "SELECT id FROM issue_event_type WHERE name = %s"
        arguments = [name]
        cursor.execute(query, arguments)
        row = cursor.fetchone()
        found = None
        if row:
            found = row[0]
        cursor.close()

        return found

    def insert_issue_event(self, issue_id, event_type_id, detail, creator_id, created_at, target_user_id):
        cursor = self.cnx.cursor()
        query = "INSERT IGNORE INTO issue_event " \
                "VALUES (%s, %s, %s, %s, %s, %s, %s)"
        arguments = [None, issue_id, event_type_id, detail, creator_id, created_at, target_user_id]
        cursor.execute(query, arguments)
        self.cnx.commit()
        cursor.close()

    def insert_issue_commit_dependency(self, issue_id, commit_id):
        cursor = self.cnx.cursor()
        query = "INSERT IGNORE INTO issue_commit_dependency " \
                "VALUES (%s, %s)"
        arguments = [issue_id, commit_id]
        cursor.execute(query, arguments)
        self.cnx.commit()
        cursor.close()

    def get_user_id(self, user_email):
        user_id = self.db_util.select_user_id_by_email(self.cnx, user_email, self.logger)
        if not user_id:
            user_name = self.querier.get_user_name(user_email)
            self.db_util.insert_user(self.cnx, user_name, user_email, self.logger)
            user_id = self.db_util.select_user_id_by_email(self.cnx, user_email, self.logger)

        return user_id

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
        self.insert_attachment(attachment_id, issue_comment_id, name, extension, size)

    def extract_issue_event(self, action, action_content, creator_id, created_at, issue_id, field_name):
        event_type = action + '-' + field_name
        self.insert_event_type(event_type)
        event_type_id = self.select_event_type(event_type)
        target_user_id = None

        if ',' in action_content and field_name in ["keywords", "depends_on", "cc", "flagtypes.name", "blocks", "whiteboard", "see_also"]:
            contents = action_content.split(',')
            for content in contents:
                content = content.strip()
                if self.is_email(content):
                    target_user_id = self.get_user_id(content)

                self.insert_issue_event(issue_id, event_type_id, content, creator_id, created_at, target_user_id)
        else:
            if self.is_email(action_content):
                target_user_id = self.get_user_id(action_content)

            self.insert_issue_event(issue_id, event_type_id, action_content, creator_id, created_at, target_user_id)

    def extract_history(self, issue_id, history):
        for event in history:
            try:
                created_at = self.date_util.get_timestamp(self.querier.get_event_property(event, 'when'), '%Y%m%dT%H:%M:%S')
                creator_id = self.get_user_id(self.querier.get_event_property(event, 'who'))

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
                subscriber_id = self.get_user_id(subscriber)
                self.insert_subscriber(issue_id, subscriber_id)
            except Exception, e:
                self.logger.warning("subscriber (" + subscriber + ") not inserted for issue id: " + str(issue_id) + " - tracker id " + str(self.issue_tracker_id), exc_info=True)

    def extract_assignee(self, issue_id, assignee):
        try:
            assignee_id = self.get_user_id(assignee)
            self.insert_assignee(issue_id, assignee_id)
        except Exception, e:
            self.logger.warning("assignee (" + assignee + ") not inserted for issue id: " + str(issue_id) + " - tracker id " + str(self.issue_tracker_id), exc_info=True)

    def extract_comments(self, issue_id, comments):
        for comment in comments:
            try:
                own_id = self.querier.get_comment_property(comment, 'id')
                body = self.querier.get_comment_property(comment, 'text')
                position = self.querier.get_comment_property(comment, 'count')
                author_id = self.get_user_id(self.querier.get_comment_property(comment, 'author'))
                created_at = self.date_util.get_timestamp(self.querier.get_comment_property(comment, 'creation_time'), '%Y%m%dT%H:%M:%S')
                self.insert_issue_comment(own_id, position, issue_id, body, author_id, created_at)

                attachment_id = self.querier.get_comment_property(comment, 'attachment_id')
                if attachment_id:
                    issue_comment_id = self.select_issue_comment_id(own_id, issue_id, created_at)
                    self.extract_attachment(issue_comment_id, attachment_id)
            except Exception, e:
                self.logger.warning("comment(" + str(position) + ") not extracted for issue id: " + str(issue_id) + " - tracker id " + str(self.issue_tracker_id), exc_info=True)
                continue

    def extract_labels(self, issue_id, labels):
        for label in labels:
            try:
                digested_label = re.sub("^\W+", "", re.sub("\W+$", "", label.lower()))
                self.insert_label(digested_label.strip())
                label_id = self.select_label_id(digested_label)
                self.assign_label_to_issue(issue_id, label_id)
            except Exception, e:
                self.logger.warning("label (" + label + ") not extracted for issue id: " + str(issue_id) + " - tracker id " + str(self.issue_tracker_id), exc_info=True)

    def select_commit(self, sha, repo_id):
        found = None
        cursor = self.cnx.cursor()
        query = "SELECT id " \
                "FROM " + self.db_name + ".commit " \
                "WHERE sha = %s AND repo_id = %s"
        arguments = [sha, repo_id]
        cursor.execute(query, arguments)
        row = cursor.fetchone()
        cursor.close()

        if row:
            found = row[0]

        return found

    def select_issue_id(self, issue_own_id):
        found = None
        cursor = self.cnx.cursor()
        query = "SELECT i.id FROM issue i " \
                "JOIN issue_tracker it ON i.issue_tracker_id = it.id " \
                "WHERE own_id = %s AND issue_tracker_id = %s AND repo_id = %s"
        arguments = [issue_own_id, self.issue_tracker_id, self.repo_id]
        cursor.execute(query, arguments)

        row = cursor.fetchone()
        cursor.close()

        if row:
            found = row[0]

        return found

    def insert_subscriber(self, issue_id, subscriber_id):
        cursor = self.cnx.cursor()
        query = "INSERT IGNORE INTO issue_subscriber " \
                "VALUES (%s, %s)"
        arguments = [issue_id, subscriber_id]
        cursor.execute(query, arguments)
        self.cnx.commit()
        cursor.close()

    def insert_assignee(self, issue_id, assignee_id):
        cursor = self.cnx.cursor()
        query = "INSERT IGNORE INTO issue_assignee " \
                "VALUES (%s, %s)"
        arguments = [issue_id, assignee_id]
        cursor.execute(query, arguments)
        self.cnx.commit()
        cursor.close()

    def extract_issue_commit_dependency(self, issue_id, commits):
        flattened_list = [y for x in commits for y in x]
        for id in flattened_list:
            if "commit" in id:
                extracted = id.split("?id=")[1].strip()
                commit_id = self.select_commit(extracted, self.repo_id)
                self.insert_issue_commit_dependency(issue_id, commit_id)

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
        summary = issue.summary
        component = issue.component
        version = issue.version
        hardware = issue.op_sys
        priority = issue.priority
        severity = issue.severity
        created_at = self.date_util.get_timestamp(issue.creation_time, '%Y%m%dT%H:%M:%S')
        last_change_at = self.date_util.get_timestamp(issue.last_change_time, '%Y%m%dT%H:%M:%S')

        reference_id = self.find_reference_id(issue.version, issue_own_id)

        user_id = self.get_user_id(issue.creator)

        stored_issue_last_change = self.select_last_change_issue(issue_own_id)
        if stored_issue_last_change:
            if last_change_at != stored_issue_last_change:
                flag_insert_issue_data = True
                self.update_issue(issue_own_id, self.issue_tracker_id, summary, component, version, hardware, priority, severity, reference_id, last_change_at)
        else:
            flag_insert_issue_data = True
            self.insert_issue(issue_own_id, self.issue_tracker_id, summary, component, version, hardware, priority, severity, reference_id, user_id, created_at, last_change_at)

        if flag_insert_issue_data:
            issue_id = self.select_issue_id(issue_own_id)
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
        self.cnx.close()

    def extract(self):
        try:
            start_time = datetime.now()
            self.get_issues()
            end_time = datetime.now()

            minutes_and_seconds = divmod((end_time-start_time).total_seconds(), 60)
            self.logger.info("process finished after " + str(minutes_and_seconds[0])
                           + " minutes and " + str(round(minutes_and_seconds[1], 1)) + " secs")
        except Exception, e:
            self.logger.error("Issue2Db failed", exc_info=True)