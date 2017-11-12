__author__ = 'valerio cosentino'

import sys
from util.db_util import DbUtil

sys.path.insert(0, "..")


class DslUtil():
    """
    This class provides utilities for the Domain Specific Languages used in the export processes
    """

    def __init__(self):
        self.db_util = DbUtil()

    def find_entity_id(self, cnx, type, name, logger):
        """
        finds id of a entity  stored in the DB (project, repository, issue tracker, forum or instant messaging)

        :type cnx: Object
        :param cnx: DB connection

        :type type: str
        :param type: type of the entity

        :type name: str
        :param name: name of the entity

        :type logger: Object
        :param logger: logger
        """
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
