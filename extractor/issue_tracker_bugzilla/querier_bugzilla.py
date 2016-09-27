#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'valerio cosentino'

import bugzilla


class BugzillaQuerier():

    def __init__(self, url, product, logger):
        self.logger = logger
        self.bzapi = bugzilla.Bugzilla(url=url)
        self.product = product

    def get_issue_ids(self, from_issue_id, to_issue_id):
        query = self.bzapi.build_query(product=self.product,include_fields=["id"])
        result = self.bzapi.query(query)
        if from_issue_id and not to_issue_id:
            result = [r for r in result if r.id >= from_issue_id]
        elif from_issue_id and to_issue_id:
            result = [r for r in result if r.id >= from_issue_id and r.id <= to_issue_id]

        return [r.id for r in result]

    def get_user(self, user_email):
        return self.bzapi.getuser(user_email)

    def get_issue(self, bug_id):
        return self.bzapi.getbug(bug_id)

    def get_attachment(self, attachment_id):
        return self.bzapi.openattachment(attachment_id)

