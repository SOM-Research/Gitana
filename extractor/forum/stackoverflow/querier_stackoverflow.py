#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'valerio cosentino'

import stackexchange
import sys
import re
sys.path.insert(0, "..//..//..")


class StackOverflowQuerier():

    def __init__(self, token, logger):
        self.token = token
        self.logger = logger
        self.so = stackexchange.Site(stackexchange.StackOverflow, app_key = self.token)
        print "here"

    def get_topic_ids(self, search_query):
        question_ids = []
        for question in self.so.questions(tagged=[search_query], pagesize=10).fetch():
            question_ids.append(question.id)

        return question_ids

    def get_topic(self, question_id):
        return self.so.question(question_id, body="True")

    def get_topic_name(self, question):
        return question.title

    def get_container_own_id(self, container):
        return container.id

    def get_container_votes(self, container):
        return container.score

    def get_topic_views(self, question):
        return question.view_count

    def is_accepted_answer(self, answer):
        print "here"

    def get_container_created_at(self, container):
        return container.creation_date

    def get_topic_last_changed_at(self, question):
        return question.last_activity_date

    def get_container_body(self, container):
        return container.body.replace('<p>', '').replace('</p>', '')

    def get_container_author(self, container):
        return self.so.user(container.owner_id).display_name

    def get_comments(self, container):
        comments = []
        try:
            for comment in container.comments.fetch():
                comments.append(comment)
        except:
            self.logger.error("Stackexchange error when retrieving comments")

        return comments

    def get_answers(self, question):
        answers = []
        for answer in question.answers:
            answers.append(answer)

        return answers

    def get_answer(self, answer_id):
        return self.so.answer(answer_id, body=True)

    def get_attachments(self, body):
        p = re.compile("<a href=[^ ]*a>")
        matches = p.findall(body)

        attachments = []
        for m in matches:
            attachments.append(m)

        return attachments

    def get_attachment_name(self, html_tag):
        p = re.compile(">.*</a>")
        matches = p.findall(html_tag)

        found = None
        if matches:
            found = matches[0].strip('</a>')[0:]
        else:
            self.logger("url name not extracted for: " + html_tag)

        return found

    def get_attachment_url(self, html_tag):
        p = re.compile("\".*\"")
        matches = p.findall(html_tag)

        found = None
        if matches:
            found = matches[0].strip('"')
        else:
            self.logger("url not extracted for: " + html_tag)

        return found

    def generate_attachment_id(self, message_id, pos):
        return str(message_id) + str(pos)







