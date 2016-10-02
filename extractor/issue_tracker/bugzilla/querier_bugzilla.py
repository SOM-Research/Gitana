#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'valerio cosentino'

import bugzilla
from datetime import datetime

class BugzillaQuerier():

    def __init__(self, url, product, logger):
        self.logger = logger
        self.bzapi = bugzilla.Bugzilla(url=url)
        self.product = product

    def get_timestamp(self, creation_time):
        return datetime.strptime(creation_time, "%Y-%m-%d")

    def get_issue_ids(self, from_issue_id, to_issue_id, before_date):
        query = self.bzapi.build_query(product=self.product, include_fields=["id", "creation_time"])
        result = self.bzapi.query(query)
        if from_issue_id and not to_issue_id:
            result = [r for r in result if r.id >= from_issue_id]
        elif from_issue_id and to_issue_id:
            result = [r for r in result if r.id >= from_issue_id and r.id <= to_issue_id]

        if before_date:
            result = [r for r in result if r.creation_time <= self.get_timestamp(before_date)]

        return [r.id for r in result]

    def get_user_name(self, user_email):
        try:
            user = self.bzapi.getuser(user_email)
            name = user.real_name.lower()
        except Exception, e:
            self.logger.warning("BugzillaError, user with email " + user_email + " not found")
            name = user_email.split('@')[0]

        return name

    def get_issue(self, bug_id):
        return self.bzapi.getbug(bug_id)

    def get_attachment(self, attachment_id):
        return self.bzapi.openattachment(attachment_id)

