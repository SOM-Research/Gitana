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
        self.driver.get(self.url)

    def get_timestamp(self, creation_time):
        return datetime.strptime(creation_time, "%Y-%m-%d")

    def get_topics(self):
        table = self.driver.find_element_by_class_name("pad")
        return table.find_elements_by_tag_name("tr")[1:]

    def load_next_page(self):
        while True:
            try:
                found = [th for th in self.driver.find_elements_by_tag_name("th") if th.text.lower() == "topic"]
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





