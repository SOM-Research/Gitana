#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'valerio cosentino'

from datetime import datetime
import multiprocessing
import sys
sys.path.insert(0, "..//..//..")

from querier_eclipse_forum import EclipseForumQuerier
from forum2db_extract_topic import EclipseTopic2Db
from extractor.util import multiprocessing_util
from extractor.util.date_util import DateUtil
from eclipse_forum_dao import EclipseForumDao


class EclipseForum2DbMain():

    NUM_PROCESSES = 2

    def __init__(self, db_name, project_name,
                 type, forum_name, url, before_date, recover_import, num_processes,
                 config, logger):
        self.logger = logger
        self.log_path = self.logger.name.rsplit('.', 1)[0] + "-" + project_name
        self.type = type
        self.url = url
        self.forum_name = forum_name
        self.project_name = project_name
        self.db_name = db_name
        self.before_date = before_date
        self.recover_import = recover_import

        if num_processes:
            self.num_processes = num_processes
        else:
            self.num_processes = EclipseForum2DbMain.NUM_PROCESSES

        self.date_util = DateUtil()

        config.update({'database': db_name})
        self.config = config

        try:
            self.querier = EclipseForumQuerier(self.url, self.logger)
            self.dao = EclipseForumDao(self.config, self.logger)
        except:
            self.logger.error("EclipseForum2DbMain extract failed", exc_info=True)

    def get_topic_info(self, forum_id, topic):
        own_id = self.querier.get_topic_own_id(topic)
        title = self.querier.get_topic_title(topic)
        views = self.querier.get_topic_views(topic)
        last_changed_at = self.date_util.get_timestamp(self.querier.get_last_changed_at(topic), "%a, %d %B %Y %H:%M")

        topic_id = self.dao.select_topic_id(forum_id, own_id)
        if topic_id:
            self.dao.update_topic_info(topic_id, forum_id, views, last_changed_at)
        else:
            if self.before_date:
                topic_created_at = self.querier.get_topic_created_at(topic)
                if self.date_util.get_timestamp(topic_created_at, "%a, %d %B %Y") <= self.date_util.get_timestamp(self.before_date, "%Y-%m-%d"):
                    self.dao.insert_topic(own_id, forum_id, title, views, last_changed_at)
            else:
                self.dao.insert_topic(own_id, forum_id, title, views, last_changed_at)
            topic_id = self.dao.select_topic_id(forum_id, own_id)

        return topic_id

    def get_topic_ids(self, forum_id):
        topic_ids = []

        next_page = True
        while next_page:
            topics_on_page = self.querier.get_topics()

            for t in topics_on_page:

                topic_id = self.get_topic_info(forum_id, t)
                topic_ids.append(topic_id)

            next_page = self.querier.go_next_page()

        return [ti for ti in topic_ids if ti is not None]

    def get_topics(self, forum_id):
        self.querier.start_browser()
        topic_ids = self.get_topic_ids(forum_id)
        self.querier.close_browser()

        intervals = [i for i in multiprocessing_util.get_tasks_intervals(topic_ids, self.num_processes) if len(i) > 0]

        queue_extractors = multiprocessing.JoinableQueue()
        results = multiprocessing.Queue()

        # Start consumers
        multiprocessing_util.start_consumers(self.num_processes, queue_extractors, results)

        for interval in intervals:
            topic_extractor = EclipseTopic2Db(self.db_name, forum_id, interval, self.config, self.log_path)
            queue_extractors.put(topic_extractor)

        # Add end-of-queue markers
        multiprocessing_util.add_poison_pills(self.num_processes, queue_extractors)

        # Wait for all of the tasks to finish
        queue_extractors.join()

    def extract(self):
        try:
            start_time = datetime.now()
            project_id = self.dao.select_project_id(self.project_name)
            forum_id = self.dao.insert_forum(project_id, self.forum_name, self.url, self.type)
            self.get_topics(forum_id)
            self.dao.close_connection()

            end_time = datetime.now()

            minutes_and_seconds = divmod((end_time-start_time).total_seconds(), 60)
            self.logger.info("EclipseForum2DbMain finished after " + str(minutes_and_seconds[0])
                         + " minutes and " + str(round(minutes_and_seconds[1], 1)) + " secs")
        except:
            self.logger.error("EclipseForum2DbMain failed", exc_info=True)