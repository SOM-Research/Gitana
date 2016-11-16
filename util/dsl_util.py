__author__ = 'valerio cosentino'

import mysql.connector
from mysql.connector import errorcode
import sys
from util.db_util import DbUtil

sys.path.insert(0, "..")


class DslUtil():

    def __init__(self):
        self.db_util = DbUtil()

    def find_entity_id(self, cnx, type, name, logger):
        found = None

        if type == "project":
            found = self.db_util.select_project_id(cnx, name, logger)
        elif type == "repo":
            found = self.db_util.select_repo_id(cnx, name, logger)
        elif type == "issuetracker":
            found = self.db_util.select_issue_tracker_id(cnx, name, logger)
        elif type == "forum":
            found = self.db_util.select_forum_id(cnx, name, logger)
        elif type == "instantmessaging":
            found = self.db_util.select_instant_messaging_id(cnx, name, logger)

        if not found:
            logger.error("DslUtil: entity " + str(type) + " with name " + str(name) + " not found!")

        return found