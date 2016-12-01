__author__ = 'valerio cosentino'

import logging


class LoggingUtil():

    def get_logger(self, log_filename):
        return logging.getLogger(log_filename)

    def get_file_handler(self, logger, log_filename, level):
        fileHandler = logging.FileHandler(log_filename + ".log", mode='w')
        formatter = logging.Formatter("%(asctime)s:%(levelname)s:%(message)s", "%Y-%m-%d %H:%M:%S")
        fileHandler.setFormatter(formatter)
        logger.setLevel(self.get_logger_level(level))
        logger.addHandler(fileHandler)

        return fileHandler

    def get_logger_level(self, level):
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
        logger.removeHandler(fileHandler)