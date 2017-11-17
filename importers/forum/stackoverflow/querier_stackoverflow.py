#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'valerio cosentino'

import stackexchange
import re
from BeautifulSoup import BeautifulSoup

from util.token_util import TokenUtil
from util.date_util import DateUtil


class StackOverflowQuerier():
    """
    This class collects the data available on Stackoverflow via its API
    """

    def __init__(self, token, logger):
        """
        :type token: str
        :param token: the token to access the Stackoverflow API

        :type logger: Object
        :param logger: logger
        """
        try:
            self._token = token
            self._logger = logger
            self._token_util = TokenUtil(self._logger, "stackoverflow")
            self._date_util = DateUtil()
            self._so = stackexchange.Site(stackexchange.StackOverflow, app_key=self._token)
            self._so.impose_throttling = True
            self._so.throttle_stop = False
        except:
            self._logger.error("StackOverflowQuerier init failed")
            raise

    def get_topic_ids(self, search_query, before_date):
        """
        gets the data source topic ids

        :type search_query: str
        :param search_query: a label used to mark questions in Stackoverflow

        :type before_date: str
        :param before_date: selects questions with creation date before a given date (YYYY-mm-dd)
        """
        questions = []
        self._token_util.wait_is_usable(self._so)
        for question in self._so.questions(tagged=[search_query], pagesize=10).fetch():
            questions.append(question)
            self._token_util.wait_is_usable(self._so)

        if before_date:
            questions = [q for q in questions if q.creation_date <=
                         self._date_util.get_timestamp(before_date, "%Y-%m-%d")]

        return [question.id for question in questions]

    def get_topic(self, question_id):
        """
        gets the topic body

        :type question_id: int
        :param question_id: the data source question id
        """
        try:
            self._token_util.wait_is_usable(self._so)
            question = self._so.question(question_id, body="True")
        except:
            question = None
        return question

    def get_topic_name(self, question):
        """
        gets the topic title

        :type question: Object
        :param question: the Object representing the question
        """
        return question.title

    def get_container_own_id(self, container):
        """
        gets the data source container id

        :type container: Object
        :param container: the Object representing the container
        """
        return container.id

    def get_container_votes(self, container):
        """
        gets the data source container votes

        :type container: Object
        :param container: the Object representing the container
        """
        return container.score

    def get_topic_labels(self, question):
        """
        gets the topic labels

        :type question: Object
        :param question: the Object representing the question
        """
        try:
            labels = question.tags
        except:
            labels = []
        return labels

    def get_topic_views(self, question):
        """
        gets the topic view count

        :type question: Object
        :param question: the Object representing the question
        """
        return question.view_count

    def is_accepted_answer(self, answer):
        """
        checks if the answer is the accepted one

        :type answer: Object
        :param answer: the Object representing the answer
        """
        try:
            found = answer.accepted
        except:
            found = False

        return found

    def get_container_created_at(self, container):
        """
        gets the container creation date

        :type container: Object
        :param container: the Object representing the container
        """
        return container.creation_date

    def get_topic_last_change_at(self, question):
        """
        gets the topic last change date

        :type question: Object
        :param question: the Object representing the question
        """
        return question.last_activity_date

    def get_container_body(self, container):
        """
        gets the container body

        :type container: Object
        :param container: the Object representing the container
        """
        return container.body

    def remove_html_tags(self, html_text):
        """
        removes HTML tags from html text

        :type html_text: str
        :param html_text: the html text of a question/answer/comment
        """
        return BeautifulSoup(html_text).text

    def get_container_author(self, container):
        """
        gets the container author

        :type container: Object
        :param container: the Object representing the container
        """
        self._token_util.wait_is_usable(self._so)
        try:
            user = self._so.user(container.owner_id).display_name
        except:
            user = None
        return user

    def get_comments(self, container):
        """
        gets the container comments

        :type container: Object
        :param container: the Object representing the container
        """
        comments = []
        try:
            self._token_util.wait_is_usable(self._so)
            for comment in container.comments.fetch():
                comments.append(comment)
                self._token_util.wait_is_usable(self._so)
        except:
            self._logger.error("Stackexchange error when retrieving comments")

        return comments

    def get_answers(self, question):
        """
        gets the answer of a question

        :type question: Object
        :param question: the Object representing the question
        """
        answers = []
        self._token_util.wait_is_usable(self._so)
        for answer in question.answers:
            answers.append(answer)
            self._token_util.wait_is_usable(self._so)

        return answers

    def get_attachments(self, body):
        """
        extracts the attachments from a text

        :type body: str
        :param body: text of a question/comment/answer
        """
        p = re.compile("<a href=[^ ]*a>")
        matches = p.findall(body)

        attachments = []
        for m in matches:
            attachments.append(m)

        return attachments

    def get_attachment_name(self, html_tag):
        """
        extracts the attachment name

        :type html_tag: str
        :param html_tag: text
        """
        p = re.compile(">.*</a>")
        matches = p.findall(html_tag)

        found = None
        if matches:
            found = matches[0].strip('</a>')[0:]
        else:
            self._logger.info("url name not extracted for: " + html_tag)

        return found

    def get_attachment_url(self, html_tag):
        """
        extracts the attachment url

        :type html_tag: str
        :param html_tag: text
        """
        p = re.compile("\".*\"")
        matches = p.findall(html_tag)

        found = None
        if matches:
            found = matches[0].strip('"')
        else:
            self._logger.info("url not extracted for: " + html_tag)

        return found

    def generate_attachment_id(self, message_id, pos):
        """
        creates id for attachment using the message id and position

        :type message_id: int
        :param message_id: id of the message where the attachment was found

        :type pos: int
        :param pos: position of the message where the attachment was found
        """
        return str(message_id) + str(pos)
