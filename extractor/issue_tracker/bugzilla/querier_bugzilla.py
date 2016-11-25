#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'valerio cosentino'

import bugzilla
from util.date_util import DateUtil


class BugzillaQuerier():

    def __init__(self, url, product, logger):
        self.logger = logger
        self.bzapi = bugzilla.Bugzilla(url=url)
        self.product = product

        self.date_util = DateUtil()

    def get_issue_ids(self, before_date):
        #TODO - include_fields seems not to work properly, http://bugzilla.readthedocs.io/en/latest/api/core/v1/bug.html
        query = self.bzapi.build_query(product=self.product, include_fields=["id", "creation_time"])
        result = self.bzapi.query(query)

        if before_date:
            result = [r for r in result if r.creation_time <= self.date_util.get_timestamp(before_date, "%Y-%m-%d")]

        return [r.id for r in result]

    def get_user_name(self, user_email):
        try:
            user = self.bzapi.getuser(user_email)
            name = user.real_name.lower()
        except Exception, e:
            self.logger.warning("BugzillaError, user with email " + user_email + " not found")
            name = user_email.split('@')[0]

        return name

    def get_issue_creator(self, issue):
        return issue.creator

    def get_issue_version(self, issue):
        return issue.version

    def get_issue_last_change_time(self, issue):
        return self.date_util.get_timestamp(issue.last_change_time, '%Y%m%dT%H:%M:%S')

    def get_issue_creation_time(self, issue):
        return self.date_util.get_timestamp(issue.creation_time, '%Y%m%dT%H:%M:%S')

    def get_issue_priority(self, issue):
        return issue.priority

    def get_issue_severity(self, issue):
        return issue.severity

    def get_issue_operating_system(self, issue):
        return issue.op_sys

    def get_issue_summary(self, issue):
        return issue.summary

    def get_issue_component(self, issue):
        return issue.component

    def get_issue_history(self, issue):
        return issue.get_history().get('bugs')[0].get('history')

    def get_comment_property(self, comment, property):
        return comment.get(property)

    def get_event_property(self, event, property):
        return event.get(property)

    def get_change_property(self, change, property):
        return change.get(property)

    def get_issue_tags(self, issue):
        return issue.gettags()

    def get_issue_keywords(self, issue):
        return issue.keywords

    def get_issue_comments(self, issue):
        return issue.getcomments()

    def get_issue_cc(self, issue):
        return issue.cc

    def get_issue_assignee(self, issue):
        return issue.assigned_to

    def get_issue_see_also(self, issue):
        return issue.see_also

    def get_issue_blocks(self, issue):
        return issue.blocks

    def get_issue_dupe_of(self, issue):
        return issue.dupe_of

    def get_issue_depends_on(self, issue):
        return issue.depends_on

    def get_issue(self, bug_id):
        return self.bzapi.getbug(bug_id)

    def get_attachment(self, attachment_id):
        return self.bzapi.openattachment(attachment_id)