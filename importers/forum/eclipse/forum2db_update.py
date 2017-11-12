#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'valerio cosentino'

from datetime import datetime
import multiprocessing

from querier_eclipse_forum import EclipseForumQuerier
from forum2db_extract_topic import EclipseTopic2Db
from util import multiprocessing_util
from eclipse_forum_dao import EclipseForumDao
from util.date_util import DateUtil
from util.logging_util import LoggingUtil


class EclipseForum2DbUpdate():
    """
    This class handles the update of Eclipse forum data
    """

    NUM_PROCESSES = 2

    def __init__(self, db_name, project_name, forum_name, eclipse_forum_url, num_processes,
                 config, log_root_path):
        """
        :type db_name: str
        :param db_name: the name of an existing DB

        :type project_name: str
        :param project_name: the name of an existing project in the DB

        :type forum_name: str
        :param forum_name: the name of an existing forum in the DB to update

        :type eclipse_forum_url: str
        :param eclipse_forum_url: the URL of the forum

        :type num_processes: int
        :param num_processes: number of processes to import the data (default 2)

        :type config: dict
        :param config: the DB configuration file

        :type log_root_path: str
        :param log_root_path: the log path
        """
        self._log_path = log_root_path + "update-eclipse-forum-" + db_name + "-" + project_name + "-" + forum_name
        self._project_name = project_name
        self._url = eclipse_forum_url
        self._db_name = db_name
        self._forum_name = forum_name

        config.update({'database': db_name})
        self._config = config

        if num_processes:
            self._num_processes = num_processes
        else:
            self._num_processes = EclipseForum2DbUpdate.NUM_PROCESSES

        self._logging_util = LoggingUtil()
        self._date_util = DateUtil()

        self._logger = None
        self._fileHandler = None
        self._querier = None
        self._dao = None

    def _update_topics_info(self, forum_id):
        # update topics of a given forum
        next_page = True
        while next_page:
            topics_on_page = self._querier.get_topics()

            for topic in topics_on_page:

                topic_own_id = self._querier.get_topic_own_id(topic)
                topic_in_db = self._dao.get_topic_id(topic_own_id, forum_id)

                if topic_in_db:
                    views = self._querier.get_topic_views(topic)
                    last_change_at = self._date_util.get_timestamp(self._querier.get_last_change_at(topic),
                                                                   "%a, %d %B %Y %H:%M")
                    self._dao.update_topic_info(topic_in_db, forum_id, views, last_change_at)

            next_page = self._querier.go_next_page()

    def _get_topics(self, forum_id):
        #update topics of a forum
        topic_ids = self._dao.get_topic_ids(forum_id)

        if topic_ids:
            self._update_topics_info(forum_id)

            intervals = [i for i in multiprocessing_util.get_tasks_intervals(topic_ids, self._num_processes)
                         if len(i) > 0]

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

    def update(self):
        """
        updates the Eclipse forum data stored in the DB
        """
        try:
            self._logger = self._logging_util.get_logger(self._log_path)
            self._fileHandler = self._logging_util.get_file_handler(self._logger, self._log_path, "info")

            self._logger.info("EclipseForum2DbUpdate started")
            start_time = datetime.now()

            self._querier = EclipseForumQuerier(self._url, self._logger)
            self._dao = EclipseForumDao(self._config, self._logger)

            self._querier.start_browser()

            project_id = self._dao.select_project_id(self._project_name)
            forum_id = self._dao.select_forum_id(self._forum_name, project_id)

            if forum_id:
                self._get_topics(forum_id)

            self._querier.close_browser()

            end_time = datetime.now()
            minutes_and_seconds = self._logging_util.calculate_execution_time(end_time, start_time)
            self._logger.info("EclipseForum2DbUpdate finished after " + str(minutes_and_seconds[0]) +
                              " minutes and " + str(round(minutes_and_seconds[1], 1)) + " secs")

            self._logging_util.remove_file_handler_logger(self._logger, self._fileHandler)
        except:
            self._logger.error("EclipseForum2DbUpdate failed", exc_info=True)
        finally:
            if self._dao:
                self._dao.close_connection()
