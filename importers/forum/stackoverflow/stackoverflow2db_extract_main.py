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


class StackOverflow2DbMain():
    """
    This class handles the import of Stackoverflow data
    """

    def __init__(self, db_name, project_name,
                 type, forum_name, search_query, before_date, tokens,
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

        :type search_query: str
        :param search_query: a label used to mark questions in Stackoverflow

        :type before_date: str
        :param before_date: import data before date (YYYY-mm-dd)

        :type tokens: list str
        :param tokens: list of Stackoverflow tokens

        :type config: dict
        :param config: the DB configuration file

        :type log_root_path: str
        :param log_root_path: the log path
        """

        self._log_path = log_root_path + "import-stackoverflow-" + db_name + "-" + project_name + "-" + forum_name
        self._type = type
        self._forum_name = forum_name
        self._search_query = search_query.strip()
        self._project_name = project_name
        self._db_name = db_name
        self._before_date = before_date
        self._tokens = tokens

        config.update({'database': db_name})
        self._config = config

        self._logging_util = LoggingUtil()

        self._logger = None
        self._fileHandler = None
        self._querier = None
        self._dao = None

    def _get_topics(self, forum_id):
        # processes Stackoverflow questions
        topic_imported = self._dao.get_topic_own_ids(forum_id)
        topic_ids = list(set(self._querier.get_topic_ids(self._search_query, self._before_date)) - set(topic_imported))
        topic_ids.sort()

        intervals = [i for i in multiprocessing_util.get_tasks_intervals(topic_ids, len(self._tokens)) if len(i) > 0]

        queue_extractors = multiprocessing.JoinableQueue()
        results = multiprocessing.Queue()

        # Start consumers
        multiprocessing_util.start_consumers(len(self._tokens), queue_extractors, results)

        pos = 0
        for interval in intervals:
            topic_extractor = StackOverflowTopic2Db(self._db_name, forum_id, interval, self._tokens[pos],
                                                    self._config, self._log_path)
            queue_extractors.put(topic_extractor)
            pos += 1

        # Add end-of-queue markers
        multiprocessing_util.add_poison_pills(len(self._tokens), queue_extractors)

        # Wait for all of the tasks to finish
        queue_extractors.join()

    def extract(self):
        """
        extracts Stackoverflow data and stores it in the DB
        """
        try:
            self._logger = self._logging_util.get_logger(self._log_path)
            self._fileHandler = self._logging_util.get_file_handler(self._logger, self._log_path, "info")

            self._logger.info("StackOverflow2DbMain started")
            start_time = datetime.now()

            self._querier = StackOverflowQuerier(self._tokens[0], self._logger)
            self._dao = StackOverflowDao(self._config, self._logger)

            project_id = self._dao.select_project_id(self._project_name)
            forum_id = self._dao.insert_forum(project_id, self._forum_name, self._type)
            self._get_topics(forum_id)

            end_time = datetime.now()
            minutes_and_seconds = self._logging_util.calculate_execution_time(end_time, start_time)
            self._logger.info("StackOverflow2DbMain finished after " + str(minutes_and_seconds[0]) +
                              " minutes and " + str(round(minutes_and_seconds[1], 1)) + " secs")

            self._logging_util.remove_file_handler_logger(self._logger, self._fileHandler)
        except:
            self._logger.error("StackOverflow2DbMain failed", exc_info=True)
        finally:
            if self._dao:
                self._dao.close_connection()
