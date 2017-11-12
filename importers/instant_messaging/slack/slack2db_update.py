#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'valerio cosentino'

from datetime import datetime
import multiprocessing

from util import multiprocessing_util
from querier_slack import SlackQuerier
from slack2db_extract_channel import SlackChannel2Db
from slack_dao import SlackDao
from util.logging_util import LoggingUtil


class Slack2DbUpdate():
    """
    This class handles the update of Slack data
    """

    def __init__(self, db_name, project_name, instant_messaging_name, tokens,
                 config, log_root_path):
        """
        :type db_name: str
        :param db_name: the name of an existing DB

        :type project_name: str
        :param project_name: the name of an existing project in the DB

        :type instant_messaging_name: str
        :param instant_messaging_name: the name of an existing instant messaging in the DB to update

        :type tokens: list of tokens
        :param tokens: a list of Slack tokens

        :type config: dict
        :param config: the DB configuration file

        :type log_root_path: str
        :param log_root_path: the log path
        """
        self._log_path = log_root_path + "update-slack-" + db_name + "-" + project_name + "-" + instant_messaging_name
        self._project_name = project_name
        self._db_name = db_name
        self._instant_messaging_name = instant_messaging_name
        self._tokens = tokens

        config.update({'database': db_name})
        self._config = config

        self._logging_util = LoggingUtil()

        self._logger = None
        self._fileHandler = None
        self._querier = None
        self._dao = None

    def _update_channels(self, instant_messaging_id):
        # updates channels of a instant messaging
        channel_ids = self._dao.get_channel_ids(instant_messaging_id)

        if channel_ids:
            intervals = [i for i in multiprocessing_util.get_tasks_intervals(channel_ids, len(self._tokens))
                         if len(i) > 0]

            queue_extractors = multiprocessing.JoinableQueue()
            results = multiprocessing.Queue()

            # Start consumers
            multiprocessing_util.start_consumers(len(self._tokens), queue_extractors, results)

            for i in range(len(intervals)):
                channel_extractor = SlackChannel2Db(self._db_name, instant_messaging_id, intervals[i], self._tokens[i],
                                                    self._config, self._log_path)
                queue_extractors.put(channel_extractor)

            # Add end-of-queue markers
            multiprocessing_util.add_poison_pills(len(self._tokens), queue_extractors)

            # Wait for all of the tasks to finish
            queue_extractors.join()

    def update(self):
        """
        updates the Slack data stored in the DB
        """
        try:
            self._logger = self._logging_util.get_logger(self._log_path)
            self._fileHandler = self._logging_util.get_file_handler(self._logger, self._log_path, "info")

            self._logger.info("SlackUpdate started")
            start_time = datetime.now()

            self._querier = SlackQuerier(self._tokens[0], self._logger)
            self._dao = SlackDao(self._config, self._logger)

            project_id = self._dao.select_project_id(self._project_name)
            instant_messaging_id = self._dao.select_instant_messaging_id(self._instant_messaging_name, project_id)

            if instant_messaging_id:
                self._update_channels(instant_messaging_id)

            end_time = datetime.now()
            minutes_and_seconds = self._logging_util.calculate_execution_time(end_time, start_time)
            self._logger.info("SlackDbUpdate extract finished after " + str(minutes_and_seconds[0]) +
                              " minutes and " + str(round(minutes_and_seconds[1], 1)) + " secs")
            self._logging_util.remove_file_handler_logger(self._logger, self._fileHandler)
        except:
            self._logger.error("SlackDbUpdate extract failed", exc_info=True)
        finally:
            if self._dao:
                self._dao.close_connection()
