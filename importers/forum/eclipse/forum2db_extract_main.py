#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'valerio cosentino'

from datetime import datetime
import multiprocessing

from querier_eclipse_forum import EclipseForumQuerier
from forum2db_extract_topic import EclipseTopic2Db
from util import multiprocessing_util
from util.date_util import DateUtil
from eclipse_forum_dao import EclipseForumDao
from util.logging_util import LoggingUtil


class EclipseForum2DbMain():
    """
    This class handles the import of Eclipse forum data
    """

    NUM_PROCESSES = 2

    def __init__(self, db_name, project_name,
                 type, forum_name, url, before_date, num_processes,
                 config, log_root_path):
        """
        :type db_name: str
        :param db_name: the name of an existing DB

        :type project_name: str
        :param project_name: the name of an existing project in the DB

        :type type: str
        :param type: type of the forum (Stackoverflow, Eclipse forum)

        :type forum_name: str
        :param forum_name: the name of the forum to import

        :type url: str
        :param url: the URL of the forum

        :type before_date: str
        :param before_date: import data before date (YYYY-mm-dd)

        :type num_processes: int
        :param num_processes: number of processes to import the data (default 2)

        :type config: dict
        :param config: the DB configuration file

        :type log_root_path: str
        :param log_root_path: the log path
        """
        self._log_path = log_root_path + "import-eclipse-forum-" + db_name + "-" + project_name + "-" + forum_name
        self._type = type
        self._url = url
        self._forum_name = forum_name
        self._project_name = project_name
        self._db_name = db_name
        self._before_date = before_date

        config.update({'database': db_name})
        self._config = config

        if num_processes:
            self._num_processes = num_processes
        else:
            self._num_processes = EclipseForum2DbMain.NUM_PROCESSES

        self._logging_util = LoggingUtil()
        self._date_util = DateUtil()

        self._logger = None
        self._fileHandler = None
        self._querier = None
        self._dao = None

    def _get_topic_info(self, forum_id, topic):
        # get topic information
        own_id = self._querier.get_topic_own_id(topic)
        title = self._querier.get_topic_title(topic)
        views = self._querier.get_topic_views(topic)
        last_change_at = self._date_util.get_timestamp(self._querier.get_last_change_at(topic), "%a, %d %B %Y %H:%M")

        topic_id = self._dao.select_topic_id(forum_id, own_id)
        if not topic_id:
            if self._before_date:
                topic_created_at = self._querier.get_topic_created_at(topic)
                if self._date_util.get_timestamp(topic_created_at, "%a, %d %B %Y") <= \
                        self._date_util.get_timestamp(self._before_date, "%Y-%m-%d"):
                    self._dao.insert_topic(own_id, forum_id, title, views, last_change_at)
            else:
                self._dao.insert_topic(own_id, forum_id, title, views, last_change_at)
            topic_id = self._dao.select_topic_id(forum_id, own_id)

        return topic_id

    def _get_topic_ids(self, forum_id):
        # get list of topic ids of a forum
        topic_ids = []

        next_page = True
        while next_page:
            topics_on_page = self._querier.get_topics()

            for t in topics_on_page:
                topic_id = self._get_topic_info(forum_id, t)
                topic_ids.append(topic_id)

            next_page = self._querier.go_next_page()

        return [ti for ti in topic_ids if ti is not None]

    def _get_topics(self, forum_id):
        # insert topics to DB
        self._querier.start_browser()
        topic_ids = self._get_topic_ids(forum_id)
        self._querier.close_browser()

        intervals = [i for i in multiprocessing_util.get_tasks_intervals(topic_ids, self._num_processes) if len(i) > 0]

        queue_extractors = multiprocessing.JoinableQueue()
        results = multiprocessing.Queue()

        # Start consumers
        multiprocessing_util.start_consumers(self._num_processes, queue_extractors, results)

        for interval in intervals:
            topic_extractor = EclipseTopic2Db(self._db_name, forum_id, interval, self._config, self._log_path)
            queue_extractors.put(topic_extractor)

        # Add end-of-queue markers
        multiprocessing_util.add_poison_pills(self._num_processes, queue_extractors)

        # Wait for all of the tasks to finish
        queue_extractors.join()

    def extract(self):
        """
        extracts Eclipse forum data and stores it in the DB
        """
        try:
            self._logger = self._logging_util.get_logger(self._log_path)
            self._fileHandler = self._logging_util.get_file_handler(self._logger, self._log_path, "info")

            self._logger.info("EclipseForum2DbMain started")
            start_time = datetime.now()

            self._querier = EclipseForumQuerier(self._url, self._logger)
            self._dao = EclipseForumDao(self._config, self._logger)

            project_id = self._dao.select_project_id(self._project_name)
            forum_id = self._dao.insert_forum(project_id, self._forum_name, self._type)
            self._get_topics(forum_id)

            end_time = datetime.now()
            minutes_and_seconds = self._logging_util.calculate_execution_time(end_time, start_time)
            self._logger.info("EclipseForum2DbMain finished after " + str(minutes_and_seconds[0]) +
                              " minutes and " + str(round(minutes_and_seconds[1], 1)) + " secs")
            self._logging_util.remove_file_handler_logger(self._logger, self._fileHandler)
        except:
            self._logger.error("EclipseForum2DbMain failed", exc_info=True)
        finally:
            if self._dao:
                self._dao.close_connection()
