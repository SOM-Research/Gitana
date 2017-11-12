#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'valerio cosentino'

import time
import os

from selenium import webdriver
import util

WEB_DRIVER_PATH = os.path.dirname(util.__file__) + "\selenium_driver\phantomjs.exe"


class EclipseForumQuerier():
    """
    This class collects the data available on the Eclipse forum via its API
    """

    def __init__(self, url, logger):
        """
        :type url: str
        :param url: the URL of the Eclipse forum

        :type logger: Object
        :param logger: logger
        """
        try:
            self._url = url
            self._logger = logger
            self._driver = None
        except:
            self._logger.error("EclipseForumQuerier init failed")
            raise

    def start_browser(self):
        """
        starts the browser used to crawl
        """
        if not self._driver:
            self._driver = webdriver.PhantomJS(executable_path=WEB_DRIVER_PATH)
            self._driver.maximize_window()
        self._driver.get(self._url)

    def close_browser(self):
        """
        closes the browser
        """
        self._driver.quit()

    def set_url(self, url):
        """
        sets the initial URL of the browser
        """
        self._url = url

    def get_topic_own_id(self, topic_element):
        """
        gets the data source topic id

        :type topic_element: Object
        :param topic_element: the Object representing the topic
        """
        found = -1
        link = self.get_topic_url(topic_element)
        if link:
            found = int(link.strip("/").split("/")[-1].strip())
        return int(found)

    def get_topic_title(self, topic_element):
        """
        gets the topic title

        :type topic_element: Object
        :param topic_element: the Object representing the topic
        """
        try:
            found = topic_element.find_element_by_class_name("big").text
        except:
            self._logger.error("EclipseForumQuerier topic title not found")
            found = None

        return found

    def get_topic_views(self, topic_element):
        """
        gets the topic views

        :type topic_element: Object
        :param topic_element: the Object representing the topic
        """
        try:
            found = int(topic_element.find_elements_by_tag_name("td")[-2].text)
        except:
            self._logger.error("EclipseForumQuerier topic views not found")
            found = None

        return found

    def get_last_change_at(self, topic_element):
        """
        gets last change date

        :type topic_element: Object
        :param topic_element: the Object representing the topic
        """
        try:
            found = self.get_created_at(topic_element.find_elements_by_tag_name("td")[-1])
        except:
            self._logger.error("EclipseForumQuerier topic last change not found")
            found = None

        return found

    def get_topic_created_at(self, topic_element):
        """
        gets topic creation date

        :type topic_element: Object
        :param topic_element: the Object representing the topic
        """
        try:
            found = topic_element.find_elements_by_tag_name("td")[2].find_element_by_class_name("DateText").text
        except:
            self._logger.error("EclipseForumQuerier topic created at not found")
            found = None

        return found

    def get_created_at(self, message_element):
        """
        gets message creation date

        :type message_element: Object
        :param message_element: the Object representing the message
        """
        try:
            found = message_element.find_element_by_class_name("DateText").text
        except:
            self._logger.error("EclipseForumQuerier message created at not found")
            found = None

        return found

    def get_topic_url(self, topic_element):
        """
        gets topic url

        :type topic_element: Object
        :param topic_element: the Object representing the topic
        """
        try:
            found = topic_element.find_element_by_class_name("big").get_attribute("href")
        except:
            self._logger.error("EclipseForumQuerier topic url not found")
            found = None

        return found

    def get_topics(self):
        """
        gets topics
        """
        while not self._driver.find_element_by_class_name("pad"):
            time.sleep(1)

        return self._driver.find_element_by_class_name("pad").find_elements_by_tag_name("tr")[1:]

    def get_message_own_id(self, message):
        """
        gets the data source message id

        :type message: Object
        :param message: the Object representing the message
        """
        found = None
        try:
            element = [m for m in message.find_elements_by_tag_name("a") if m.get_attribute("class") == "MsgSubText"][0]
            if element:
                found = element.get_attribute('href').split("#msg_")[-1]
        except:
            self._logger.error("EclipseForumQuerier message own id not found")
            found = None

        return found

    def get_message_body(self, message):
        """
        gets the message body

        :type message: Object
        :param message: the Object representing the message
        """
        try:
            found = message.find_element_by_class_name("MsgR3").find_element_by_class_name("MsgBodyText").text
        except:
            self._logger.error("EclipseForumQuerier message body not found")
            found = None

        return found

    def get_message_author_name(self, message):
        """
        gets the message author name

        :type message: Object
        :param message: the Object representing the message
        """
        try:
            class_content = message.find_element_by_class_name("MsgR2").find_element_by_class_name("msgud")
            found = class_content.find_elements_by_tag_name("a")[0].text
        except:
            self._logger.error("EclipseForumQuerier message author name not found")
            found = None

        return found

    def message_has_attachments(self, message):
        """
        checks that a message has attachments

        :type message: Object
        :param message: the Object representing the message
        """
        try:
            found = message.find_element_by_class_name("AttachmentsList")
        except:
            found = False

        return found

    def message_get_attachments(self, message):
        """
        gets attachments of a message

        :type message: Object
        :param message: the Object representing the message
        """
        try:
            found = message.find_element_by_class_name("AttachmentsList").find_elements_by_tag_name("li")
        except:
            found = None

        return found

    def get_attachment_url(self, attachment):
        """
        gets URL attachments

        :type attachment: Object
        :param attachment: the Object representing the attachment
        """
        try:
            found = attachment.find_elements_by_tag_name("a")[0].get_attribute("href")
        except:
            found = None

        return found

    def get_attachment_own_id(self, attachment):
        """
        gets data source attachment id

        :type attachment: Object
        :param attachment: the Object representing the attachment
        """
        url = self.get_attachment_url(attachment)
        return url.split('&id=')[-1].strip('&').strip('')

    def get_attachment_name(self, attachment):
        """
        gets attachment name

        :type attachment: Object
        :param attachment: the Object representing the attachment
        """
        try:
            found = attachment.find_elements_by_tag_name("a")[1].text
        except:
            found = None

        return found

    def get_attachment_size(self, attachment):
        """
        gets attachment size

        :type attachment: Object
        :param attachment: the Object representing the attachment
        """
        try:
            size = 0
            text = attachment.find_element_by_class_name("SmallText").text
            quantity = text.lower().split(',')[0].split(' ')[-1].lower()
            if 'kb' in quantity:
                size = float(quantity.strip('kb').strip('')) * 1000
            elif 'mb' in quantity:
                size = float(quantity.strip('mb').strip('')) * 1000000
            elif 'gb' in quantity:
                size = float(quantity.strip('gb').strip('')) * 1000000000
            elif 'tb' in quantity:
                size = float(quantity.strip('tb').strip('')) * 1000000000000
            else:
                self._logger.error("EclipseForumQuerier impossible to extract attachment size from " + quantity)
        except:
            size = 0

        return size

    def get_messages(self):
        """
        gets list of messages
        """
        while True:
            try:
                found = self._driver.find_elements_by_class_name("MsgTable")
                if found:
                    break
            except:
                continue
                time.sleep(1)

        return found

    def _load_next_page(self):
        # loads the next page
        while True:
            try:
                background = self._driver.find_element_by_class_name("ForumBackground")
                found = background.find_elements_by_tag_name("table")[2].text
                if found:
                    break
            except:
                continue
                time.sleep(1)

    def go_next_page(self):
        # goes to the next page
        done = False
        try:
            found = [l for l in self._driver.find_elements_by_class_name("PagerLink")
                     if l.get_attribute("accesskey") == "n"]
        except:
            found = []

        if found:
            found[0].click()
            self._load_next_page()
            done = True

        return done
