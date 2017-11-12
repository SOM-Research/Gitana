__author__ = 'valerio cosentino'

import logging


class LoggingUtil():
    """
    This class provides logging utilities
    """

    LOG_EXTENSION = ".log"

    def get_logger(self, log_filename):
        """
        gets the logger

        :type log_filename: str
        :param log_filename: logger file name
        """
        return logging.getLogger(log_filename + LoggingUtil.LOG_EXTENSION)

    def get_file_handler(self, logger, log_filename, level):
        """
        gets the file handler associated to a logger

        :type logger: Object
        :param logger: logger

        :type log_filename: str
        :param log_filename: logger file name

        :type level: str
        :param level: level of the logger (error, warning, info)
        """
        fileHandler = logging.FileHandler(log_filename + LoggingUtil.LOG_EXTENSION, mode='w')
        formatter = logging.Formatter("%(asctime)s:%(levelname)s:%(message)s", "%Y-%m-%d %H:%M:%S")
        fileHandler.setFormatter(formatter)
        logger.setLevel(self.get_logger_level(level))
        logger.addHandler(fileHandler)

        return fileHandler

    def calculate_execution_time(self, end_time, start_time):
        """
        calculates the execution time

        :type end_time: datetime
        :param end_time: end execution time

        :type start_time: datetime
        :param start_time: start execution time
        """
        return divmod((end_time - start_time).total_seconds(), 60)

    def get_logger_level(self, level):
        """
        gets the logger level

        :type level: str
        :param level: name of the level
        """
        if level == "warning":
            found = logging.WARNING
        elif level == "debug":
            found = logging.DEBUG
        elif level == "error":
            found = logging.ERROR
        else:
            found = logging.INFO

        return found

    def remove_file_handler_logger(self, logger, fileHandler):
        """
        removes file handler from logger

        :type logger: Object
        :param logger: logger

        :type fileHandler: Object
        :param fileHandler: file handler
        """
        logger.removeHandler(fileHandler)
