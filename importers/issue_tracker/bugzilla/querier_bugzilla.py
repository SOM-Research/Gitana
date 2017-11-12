#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'valerio cosentino'

import bugzilla
from util.date_util import DateUtil
import time


class BugzillaQuerier():
    """
    This class collects the data available on the Bugzilla issue tracker via its API
    """

    WAITING_TIME = 1800

    def __init__(self, url, product, logger):
        """
        :type url: str
        :param url: the URL of the Bugzilla issue tracker

        :type product: str
        :param product: the name of the product to import from the Bugzilla issue tracker

        :type logger: Object
        :param logger: logger
        """
        self._logger = logger
        self._bzapi = self._init_bzapi(url)
        self._product = product
        self._date_util = DateUtil()

    def _init_bzapi(self, url):
        # connect to the Bugzilla API
        success = False

        while not success:
            try:
                bzapi = bugzilla.Bugzilla(url=url)
                success = True
            except:
                time.sleep(BugzillaQuerier.WAITING_TIME)
                self._logger.warning("BugzillaQuerier init standby for " +
                                     str(BugzillaQuerier.WAITING_TIME) + " seconds")

        return bzapi

    def get_issue_ids(self, before_date):
        """
        gets data source issue ids

        :type before_date: str
        :param before_date: selects issues with creation date before a given date (YYYY-mm-dd)
        """
        # TODO - include_fields seems not to work properly
        query = self._bzapi.build_query(product=self._product, include_fields=["id", "creation_time"])
        result = self._bzapi.query(query)

        if before_date:
            result = [r for r in result if r.creation_time <= self._date_util.get_timestamp(before_date, "%Y-%m-%d")]

        return [r.id for r in result]

    def get_user_name(self, user_email):
        """
        gets user name by her email

        :type user_email: str
        :param user_email: user email
        """
        try:
            user = self._bzapi.getuser(user_email)
            name = user.real_name.lower()
        except Exception:
            self._logger.warning("BugzillaError, user with email " + user_email + " not found")
            name = user_email.split('@')[0]

        return name

    def get_issue_creator(self, issue):
        """
        gets issue creator

        :type issue: Object
        :param issue: the Object representing an issue
        """
        return issue.creator

    def get_issue_version(self, issue):
        """
        gets issue version

        :type issue: Object
        :param issue: the Object representing an issue
        """
        return issue.version

    def get_issue_last_change_time(self, issue):
        """
        gets issue last change date

        :type issue: Object
        :param issue: the Object representing an issue
        """
        return self._date_util.get_timestamp(issue.last_change_time, '%Y%m%dT%H:%M:%S')

    def get_issue_creation_time(self, issue):
        """
        gets issue creation time

        :type issue: Object
        :param issue: the Object representing an issue
        """
        return self._date_util.get_timestamp(issue.creation_time, '%Y%m%dT%H:%M:%S')

    def get_issue_priority(self, issue):
        """
        gets issue priority

        :type issue: Object
        :param issue: the Object representing an issue
        """
        return issue.priority

    def get_issue_severity(self, issue):
        """
        gets issue severity

        :type issue: Object
        :param issue: the Object representing an issue
        """
        return issue.severity

    def get_issue_operating_system(self, issue):
        """
        gets issue operating system

        :type issue: Object
        :param issue: the Object representing an issue
        """
        return issue.op_sys

    def get_issue_summary(self, issue):
        """
        gets issue summary

        :type issue: Object
        :param issue: the Object representing an issue
        """
        return issue.summary

    def get_issue_component(self, issue):
        """
        gets issue component

        :type issue: Object
        :param issue: the Object representing an issue
        """
        return issue.component

    def get_issue_history(self, issue):
        """
        gets issue event history

        :type issue: Object
        :param issue: the Object representing an issue
        """
        return issue.get_history_raw().get('bugs')[0].get('history')

    def get_comment_property(self, comment, property):
        """
        gets property of an issue comment

        :type comment: Object
        :param comment: the Object representing a comment

        :type property: str
        :param property: the name of the property to retrieve
        """
        return comment.get(property)

    def get_event_property(self, event, property):
        """
        gets property of an event

        :type event: Object
        :param event: the Object representing an event

        :type property: str
        :param property: the name of the property to retrieve
        """
        return event.get(property)

    def get_change_property(self, change, property):
        """
        gets property of a change

        :type change: Object
        :param change: the Object representing a change

        :type property: str
        :param property: the name of the property to retrieve
        """
        return change.get(property)

    def get_issue_tags(self, issue):
        """
        gets tags of an issue

        :type issue: Object
        :param issue: the Object representing an issue
        """
        return issue.gettags()

    def get_issue_keywords(self, issue):
        """
        gets keywords of an issue

        :type issue: Object
        :param issue: the Object representing an issue
        """
        return issue.keywords

    def get_issue_comments(self, issue):
        """
        gets comments of an issue

        :type issue: Object
        :param issue: the Object representing an issue
        """
        return issue.getcomments()

    def get_issue_cc(self, issue):
        """
        gets subscribers of an issue

        :type issue: Object
        :param issue: the Object representing an issue
        """
        return issue.cc

    def get_issue_assignee(self, issue):
        """
        gets assignee of an issue

        :type issue: Object
        :param issue: the Object representing an issue
        """
        return issue.assigned_to

    def get_issue_see_also(self, issue):
        """
        gets see-also issue relations of an issue

        :type issue: Object
        :param issue: the Object representing an issue
        """
        return issue.see_also

    def get_issue_blocks(self, issue):
        """
        gets blocks issue relations of an issue

        :type issue: Object
        :param issue: the Object representing an issue
        """
        return issue.blocks

    def get_issue_dupe_of(self, issue):
        """
        gets duplicate issue relations of an issue

        :type issue: Object
        :param issue: the Object representing an issue
        """
        return issue.dupe_of

    def get_issue_depends_on(self, issue):
        """
        gets depends-on issue relations of an issue

        :type issue: Object
        :param issue: the Object representing an issue
        """
        return issue.depends_on

    def get_issue(self, issue_id):
        """
        gets issue by its id

        :type issue_id: int
        :param issue_id: the data source issue id
        """
        return self._bzapi.getbug(issue_id)

    def get_attachment(self, attachment_id):
        """
        gets attachment by its id

        :type attachment_id: int
        :param attachment_id: the data source attachment id
        """
        return self._bzapi.openattachment(attachment_id)
