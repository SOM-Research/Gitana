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


class Slack2DbMain():
    """
    This class handles the import of Slack data
    """

    def __init__(self, db_name, project_name,
                 type, instant_messaging_name, before_date, channels, tokens,
                 config, log_root_path):
        """
        :type db_name: str
        :param db_name: the name of an existing DB

        :type project_name: str
        :param project_name: the name of an existing project in the DB

        :type type: str
        :param type: type of the instant messaging (Slack, IRC)

        :type instant_messaging_name: str
        :param instant_messaging_name: the name of the instant messaging to import

        :type channels: list str
        :param channels: list of channels to import

        :type before_date: str
        :param before_date: import data before date (YYYY-mm-dd)

        :type tokens: list str
        :param tokens: list of Slack tokens

        :type config: dict
        :param config: the DB configuration file

        :type log_root_path: str
        :param log_root_path: the log path
        """
        self._log_path = log_root_path + "import-slack-" + db_name + "-" + project_name + "-" + instant_messaging_name
        self._type = type
        self._instant_messaging_name = instant_messaging_name
        self._project_name = project_name
        self._db_name = db_name
        self._channels = channels
        self._before_date = before_date
        self._tokens = tokens

        config.update({'database': db_name})
        self._config = config

        self._logging_util = LoggingUtil()

        self._logger = None
        self._fileHandler = None
        self._querier = None
        self._dao = None

    def _get_channel_ids(self, instant_messaging_id):
        # get data source channel ids
        channel_ids = []
        channel_own_ids = self._querier.get_channel_ids(self._before_date, self._channels)
        for own_id in channel_own_ids:
            channel = self._querier.get_channel(own_id)
            last_change_at = self._querier.get_channel_last_change_at(channel)

            if self._dao.get_channel_last_change_at(own_id, instant_messaging_id) != last_change_at:
                name = self._querier._get_channel_name(channel)
                description = self._querier.get_channel_description(channel)
                created_at = self._querier._get_channel_created_at(channel)

                channel_id = self._dao.insert_channel(own_id, instant_messaging_id, name,
                                                      description, created_at, last_change_at)
                channel_ids.append(channel_id)

        return channel_ids

    def _get_channels(self, instant_messaging_id):
        # processes Slack channels
        channel_ids = self._get_channel_ids(instant_messaging_id)

        intervals = [i for i in multiprocessing_util.get_tasks_intervals(channel_ids, len(self._tokens)) if len(i) > 0]

        queue_extractors = multiprocessing.JoinableQueue()
        results = multiprocessing.Queue()

        # Start consumers
        multiprocessing_util.start_consumers(len(self._tokens), queue_extractors, results)

        pos = 0
        for interval in intervals:
            topic_extractor = SlackChannel2Db(self._db_name, instant_messaging_id, interval, self._tokens[pos],
                                              self._config, self._log_path)
            queue_extractors.put(topic_extractor)
            pos += 1

        # Add end-of-queue markers
        multiprocessing_util.add_poison_pills(len(self._tokens), queue_extractors)

        # Wait for all of the tasks to finish
        queue_extractors.join()

    def extract(self):
        """
        extracts Slack data and stores it in the DB
        """
        try:
            self._logger = self._logging_util.get_logger(self._log_path)
            self._fileHandler = self._logging_util.get_file_handler(self._logger, self._log_path, "info")

            self._logger.info("SlackDbMain started")
            start_time = datetime.now()

            self._querier = SlackQuerier(self._tokens[0], self._logger)
            self._dao = SlackDao(self._config, self._logger)

            project_id = self._dao.select_project_id(self._project_name)
            instant_messaging_id = self._dao.insert_instant_messaging(project_id,
                                                                      self._instant_messaging_name, self._type)
            self._get_channels(instant_messaging_id)

            end_time = datetime.now()
            minutes_and_seconds = self._logging_util.calculate_execution_time(end_time, start_time)
            self._logger.info("SlackDbMain extract finished after " + str(minutes_and_seconds[0]) +
                              " minutes and " + str(round(minutes_and_seconds[1], 1)) + " secs")

            self._logging_util.remove_file_handler_logger(self._logger, self._fileHandler)
        except:
            self._logger.error("SlackDbMain extract failed", exc_info=True)
        finally:
            if self._dao:
                self._dao.close_connection()
