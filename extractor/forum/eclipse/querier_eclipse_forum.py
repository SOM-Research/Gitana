#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'valerio cosentino'

from datetime import datetime
from selenium import webdriver
import time


class EclipseForumQuerier():

    def __init__(self, url, logger):
        self.url = url
        self.logger = logger
        self.driver = None

    def start_browser(self):
        self.driver = webdriver.Chrome(executable_path='C:/chromedriver_win32/chromedriver.exe')
        self.driver.maximize_window()
        self.driver.get(self.url)

    def close_browser(self):
        self.driver.close()

    def set_logger(self, logger):
        self.logger = logger

    def set_url(self, url):
        self.url = url

    def get_timestamp(self, creation_time, format):
        return datetime.strptime(creation_time, format)

    def get_topic_own_id(self, topic_element):
        found = None
        link = self.get_topic_url(topic_element)
        if link:
            found = int(link.strip("/").split("/")[-1].strip())
        return int(found)

    def get_topic_title(self, topic_element):
        title = topic_element.find_element_by_class_name("big").text
        #small = topic_element.find_element_by_class_name("small").text

        #if small:
        #    title = title + " ( " + small + " )"

        return title

    def get_topic_replies(self, topic_element):
        try:
            found = int(topic_element.find_elements_by_tag_name("td")[-3].text)
        except:
            found = None

        return found

    def get_topic_views(self, topic_element):
        try:
            found = int(topic_element.find_elements_by_tag_name("td")[-2].text)
        except:
            found = None

        return found

    def get_created_at(self, message_element):
        datetime = message_element.find_element_by_class_name("DateText").text
        return self.get_timestamp(datetime, "%a, %d %B %Y %H:%M")

    def get_topic_url(self, topic_element):
        return topic_element.find_element_by_class_name("big").get_attribute("href")

    def get_topics(self):
        while not self.driver.find_element_by_class_name("pad"):
            time.sleep(1)

        return self.driver.find_element_by_class_name("pad").find_elements_by_tag_name("tr")[1:]

    def get_message_own_id(self, message):
        found = None
        element = [m for m in message.find_elements_by_tag_name("a") if m.get_attribute("class") == "MsgSubText"][0]
        if element:
            found = element.get_attribute('href').split("#msg_")[-1]

        return found

    def get_message_body(self, message):
        return message.find_element_by_class_name("MsgR3").text

    def get_message_author_name(self, message):
        return message.find_element_by_class_name("MsgR2").find_element_by_class_name("msgud").find_elements_by_tag_name("a")[0].text

    def message_has_attachments(self, message):
        try:
            found = message.find_element_by_class_name("AttachmentsList")
        except:
            found = False

        return found

    def message_get_attachments(self, message):
        return message.find_element_by_class_name("AttachmentsList").find_elements_by_tag_name("li")

    def get_attachment_url(self, attachment):
        return attachment.find_elements_by_tag_name("a")[0].get_attribute("href")

    def get_attachment_own_id(self, attachment):
        url = self.get_attachment_url(attachment)
        return url.split('&id=')[-1].strip('&').strip('')

    def get_attachment_name(self, attachment):
        return attachment.find_elements_by_tag_name("a")[1].text

    def get_attachment_size(self, attachment):
        text = attachment.find_element_by_class_name("SmallText").text
        size = float(text.lower().split(',')[0].split(' ')[-1].strip('kb').strip('')) * 1000

        return size

    def get_messages(self):
        while True:
            try:
                found = self.driver.find_elements_by_class_name("MsgTable")
                if found:
                    break
            except:
                continue
                time.sleep(1)

        return found

    def load_next_page(self):
        while True:
            try:
                found = self.driver.find_element_by_class_name("ForumBackground").find_elements_by_tag_name("table")[2].text
                if found:
                    break
            except:
                continue
                time.sleep(1)

    def go_next_page(self):
        done = False
        found = [l for l in self.driver.find_elements_by_class_name("PagerLink") if l.get_attribute("accesskey") == "n"]
        if found:
            found[0].click()
            self.load_next_page()
            done = True

        return done





