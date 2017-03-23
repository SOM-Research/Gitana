#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'valerio cosentino'

import time
import os

from selenium import webdriver
import util
WEB_DRIVER_PATH = os.path.dirname(util.__file__) + "\selenium_driver\phantomjs.exe"


class EclipseForumQuerier():

    def __init__(self, url, logger):
        try:
            self._url = url
            self._logger = logger
            self._driver = None
        except:
            self._logger.error("EclipseForumQuerier init failed")
            raise

    def start_browser(self):
        if not self._driver:
            #self._driver = webdriver.PhantomJS(executable_path=WEB_DRIVER_PATH)
            self._driver = webdriver.PhantomJS()
            self._driver.maximize_window()
        self._driver.get(self._url)

    def close_browser(self):
        self._driver.quit()

    def set_url(self, url):
        self._url = url

    def get_topic_own_id(self, topic_element):
        found = -1
        link = self.get_topic_url(topic_element)
        if link:
            found = int(link.strip("/").split("/")[-1].strip())
        return int(found)

    def get_topic_title(self, topic_element):
        try:
            found = topic_element.find_element_by_class_name("big").text
        #small = topic_element.find_element_by_class_name("small").text

        #if small:
        #    title = title + " ( " + small + " )"
        except:
            self._logger.error("EclipseForumQuerier topic title not found")
            found = None

        return found

    def get_topic_views(self, topic_element):
        try:
            found = int(topic_element.find_elements_by_tag_name("td")[-2].text)
        except:
            self._logger.error("EclipseForumQuerier topic views not found")
            found = None

        return found

    def get_last_change_at(self, topic_element):
        try:
            found = self.get_created_at(topic_element.find_elements_by_tag_name("td")[-1])
        except:
            self._logger.error("EclipseForumQuerier topic last change not found")
            found = None

        return found

    def get_topic_created_at(self, topic_element):
        try:
            found = topic_element.find_elements_by_tag_name("td")[2].find_element_by_class_name("DateText").text
        except:
            self._logger.error("EclipseForumQuerier topic created at not found")
            found = None

        return found

    def get_created_at(self, message_element):
        try:
            found = message_element.find_element_by_class_name("DateText").text
        except:
            self._logger.error("EclipseForumQuerier message created at not found")
            found = None

        return found

    def get_topic_url(self, topic_element):
        try:
            found = topic_element.find_element_by_class_name("big").get_attribute("href")
        except:
            self._logger.error("EclipseForumQuerier topic url not found")
            found = None

        return found

    def get_topics(self):
        while not self._driver.find_element_by_class_name("pad"):
            time.sleep(1)

        return self._driver.find_element_by_class_name("pad").find_elements_by_tag_name("tr")[1:]

    def get_message_own_id(self, message):
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
        try:
            found = message.find_element_by_class_name("MsgR3").find_element_by_class_name("MsgBodyText").text
        except:
            self._logger.error("EclipseForumQuerier message body not found")
            found = None

        return found

    def get_message_author_name(self, message):
        try:
            found = message.find_element_by_class_name("MsgR2").find_element_by_class_name("msgud").find_elements_by_tag_name("a")[0].text
        except:
            self._logger.error("EclipseForumQuerier message author name not found")
            found = None

        return found

    def message_has_attachments(self, message):
        try:
            found = message.find_element_by_class_name("AttachmentsList")
        except:
            found = False

        return found

    def message_get_attachments(self, message):
        try:
            found = message.find_element_by_class_name("AttachmentsList").find_elements_by_tag_name("li")
        except:
            found = None

        return found

    def get_attachment_url(self, attachment):
        try:
            found = attachment.find_elements_by_tag_name("a")[0].get_attribute("href")
        except:
            found = None

        return found

    def get_attachment_own_id(self, attachment):
        url = self.get_attachment_url(attachment)
        return url.split('&id=')[-1].strip('&').strip('')

    def get_attachment_name(self, attachment):
        try:
            found = attachment.find_elements_by_tag_name("a")[1].text
        except:
            found = None

        return found

    def get_attachment_size(self, attachment):
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
        while True:
            try:
                found = self._driver.find_element_by_class_name("ForumBackground").find_elements_by_tag_name("table")[2].text
                if found:
                    break
            except:
                continue
                time.sleep(1)

    def go_next_page(self):
        done = False
        try:
            found = [l for l in self._driver.find_elements_by_class_name("PagerLink") if l.get_attribute("accesskey") == "n"]
        except:
            found = []

        if found:
            found[0].click()
            self._load_next_page()
            done = True

        return done





