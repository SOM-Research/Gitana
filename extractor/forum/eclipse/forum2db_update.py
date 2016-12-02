#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'valerio cosentino'

from datetime import datetime
import multiprocessing

from querier_eclipse_forum import EclipseForumQuerier
from forum2db_extract_topic import EclipseTopic2Db
from util import multiprocessing_util
from eclipse_forum_dao import EclipseForumDao


class EclipseForum2DbUpdate():

    NUM_PROCESSES = 2

    def __init__(self, db_name, project_name, forum_name, eclipse_forum_url, num_processes,
                 config, logger):
        self.logger = logger
        self.log_path = self.logger.name.rsplit('.', 1)[0] + "-" + project_name
        self.project_name = project_name
        self.url = eclipse_forum_url
        self.db_name = db_name
        self.forum_name = forum_name

        if num_processes:
            self.num_processes = num_processes
        else:
            self.num_processes = EclipseForum2DbUpdate.NUM_PROCESSES

        config.update({'database': db_name})
        self.config = config

        try:
            self.dao = EclipseForumDao(self.config, self.logger)
        except:
            self.logger.error("EclipseForum2DbUpdate extract failed", exc_info=True)

    def update_topics_info(self, forum_id):
        next_page = True
        while next_page:
            topics_on_page = self.querier.get_topics()

            for topic in topics_on_page:

                topic_own_id = self.querier.get_topic_own_id(topic)
                topic_in_db = self.dao.get_topic_id(topic_own_id, forum_id)

                if topic_in_db:
                    views = self.querier.get_topic_views(topic)
                    last_change_at = self.date_util.get_timestamp(self.querier.get_last_change_at(topic), "%a, %d %B %Y %H:%M")
                    self.dao.update_topic_info(topic_in_db, forum_id, views, last_change_at)

            next_page = self.querier.go_next_page()

    def get_topics(self, forum_id):
        topic_ids = self.dao.get_topic_ids(forum_id)

        if topic_ids:
            self.update_topics_info(forum_id)

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

    def update(self):
        try:
            start_time = datetime.now()
            project_id = self.dao.select_project_id(self.project_name)
            forum_id = self.dao.select_forum_id(self.forum_name, project_id)
            self.querier = EclipseForumQuerier(self.url, self.logger)
            self.get_topics(forum_id)
            self.cnx.close()
            end_time = datetime.now()

            minutes_and_seconds = divmod((end_time-start_time).total_seconds(), 60)
            self.logger.info("EclipseForum2DbUpdate finished after " + str(minutes_and_seconds[0])
                         + " minutes and " + str(round(minutes_and_seconds[1], 1)) + " secs")
        except:
            self.logger.error("EclipseForum2DbUpdate failed", exc_info=True)