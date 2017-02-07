#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'valerio cosentino'

from datetime import datetime
import multiprocessing

from util import multiprocessing_util
from querier_stackoverflow import StackOverflowQuerier
from stackoverflow2db_extract_topic import StackOverflowTopic2Db
from stackoverflow_dao import StackOverflowDao
from util.logging_util import LoggingUtil


class StackOverflow2DbUpdate():

    def __init__(self, db_name, project_name, forum_name, tokens,
                 config, log_root_path):
        self._log_path = log_root_path + "update-stackoverflow-" + db_name + "-" + project_name + "-" + forum_name
        self._project_name = project_name
        self._db_name = db_name
        self._forum_name = forum_name
        self._tokens = tokens

        config.update({'database': db_name})
        self._config = config

        self._logging_util = LoggingUtil()

        self._logger = None
        self._fileHandler = None
        self._querier = None
        self._dao = None

    def _get_topics(self, forum_id):
        topic_ids = self._dao.get_topic_ids(forum_id)

        if topic_ids:
            intervals = [i for i in multiprocessing_util.get_tasks_intervals(topic_ids, len(self._tokens)) if len(i) > 0]

            queue_extractors = multiprocessing.JoinableQueue()
            results = multiprocessing.Queue()

            # Start consumers
            multiprocessing_util.start_consumers(len(self._tokens), queue_extractors, results)

            for i in range(len(intervals)):
                topic_extractor = StackOverflowTopic2Db(self._db_name, forum_id, intervals[i], self._tokens[i], self._config, self._log_path)
                queue_extractors.put(topic_extractor)

            # Add end-of-queue markers
            multiprocessing_util.add_poison_pills(len(self._tokens), queue_extractors)

            # Wait for all of the tasks to finish
            queue_extractors.join()

    def update(self):
        try:
            self._logger = self._logging_util.get_logger(self._log_path)
            self._fileHandler = self._logging_util.get_file_handler(self._logger, self._log_path, "info")

            self._logger.info("StackOverflow2DbUpdate started")
            start_time = datetime.now()

            self._querier = StackOverflowQuerier(self._tokens[0], self._logger)
            self._dao = StackOverflowDao(self._config, self._logger)

            project_id = self._dao.select_project_id(self._project_name)
            forum_id = self._dao.select_forum_id(self._forum_name, project_id)
            self._get_topics(forum_id)

            end_time = datetime.now()
            minutes_and_seconds = self._logging_util.calculate_execution_time(end_time, start_time)
            self._logger.info("StackOverflow2DbUpdate finished after " + str(minutes_and_seconds[0])
                         + " minutes and " + str(round(minutes_and_seconds[1], 1)) + " secs")

            self._logging_util.remove_file_handler_logger(self._logger, self._fileHandler)
        except:
            self._logger.error("StackOverflow2DbUpdate failed", exc_info=True)
        finally:
            if self._dao:
                self._dao.close_connection()
