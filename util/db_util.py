#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'valerio cosentino'

import mysql.connector
from mysql.connector import errorcode


class DbUtil():
    """
    This class provides database utilities
    """

    def get_connection(self, config):
        """
        gets DB connection

        :type config: dict
        :param config: the DB configuration file
        """
        return mysql.connector.connect(**config)

    def close_connection(self, cnx):
        """
        closes DB connection

        :type cnx: Object
        :param cnx: DB connection to close
        """
        cnx.close()

    def lowercase(self, str):
        """
        conver str to lowercase

        :type str: str
        :param str: str to convert
        """
        if str:
            str = str.lower()

        return str

    def select_project_id(self, cnx, project_name, logger):
        """
        gets project id

        :type cnx: Object
        :param cnx: DB connection

        :type project_name: str
        :param project_name: name of the project

        :type logger: Object
        :param logger: logger
        """
        found = None
        cursor = cnx.cursor()
        query = "SELECT p.id " \
                "FROM project p " \
                "WHERE p.name = %s"
        arguments = [project_name]
        cursor.execute(query, arguments)
        row = cursor.fetchone()

        if row:
            found = row[0]
        else:
            logger.error("the project " + str(project_name) + " does not exist")

        cursor.close()
        return found

    def insert_repo(self, cnx, project_id, repo_name, logger):
        """
        inserts repository

        :type cnx: Object
        :param cnx: DB connection

        :type project_id: int
        :param project_id: id of the project

        :type repo_name: str
        :param repo_name: name of the repository

        :type logger: Object
        :param logger: logger
        """
        cursor = cnx.cursor()
        query = "INSERT IGNORE INTO repository " \
                "VALUES (%s, %s, %s)"
        arguments = [None, project_id, repo_name]
        cursor.execute(query, arguments)
        cnx.commit()
        cursor.close()

    def insert_issue_tracker(self, cnx, repo_id, issue_tracker_name, type, logger):
        """
        inserts issue tracker

        :type cnx: Object
        :param cnx: DB connection

        :type repo_id: int
        :param repo_id: id of the repository

        :type issue_tracker_name: str
        :param issue_tracker_name: name of the issue tracker

        :type type: str
        :param type: type of the issue tracker

        :type logger: Object
        :param logger: logger
        """
        cursor = cnx.cursor()
        query = "INSERT IGNORE INTO issue_tracker " \
                "VALUES (%s, %s, %s, %s)"
        arguments = [None, repo_id, issue_tracker_name, type]
        cursor.execute(query, arguments)
        cnx.commit()

        query = "SELECT id " \
                "FROM issue_tracker " \
                "WHERE name = %s"
        arguments = [issue_tracker_name]
        cursor.execute(query, arguments)

        row = cursor.fetchone()

        if row:
            found = row[0]
        else:
            logger.warning("no issue with name " + str(issue_tracker_name))

        cursor.close()
        return found

    def select_repo_id(self, cnx, repo_name, logger):
        """
        selects repository id

        :type cnx: Object
        :param cnx: DB connection

        :type repo_name: str
        :param repo_name: name of the repository

        :type logger: Object
        :param logger: logger
        """
        found = None
        cursor = cnx.cursor()
        query = "SELECT id " \
                "FROM repository " \
                "WHERE name = %s"
        arguments = [repo_name]
        cursor.execute(query, arguments)

        row = cursor.fetchone()

        if row:
            found = row[0]
        else:
            logger.error("the repository " + repo_name + " does not exist")

        cursor.close()
        return found

    def select_instant_messaging_id(self, cnx, im_name, logger):
        """
        selects instant messaging id

        :type cnx: Object
        :param cnx: DB connection

        :type im_name: str
        :param im_name: name of the instant messaging

        :type logger: Object
        :param logger: logger
        """
        found = None
        cursor = cnx.cursor()
        query = "SELECT id " \
                "FROM instant_messaging " \
                "WHERE name = %s"
        arguments = [im_name]
        cursor.execute(query, arguments)

        row = cursor.fetchone()

        if row:
            found = row[0]
        else:
            logger.error("the instant messaging " + im_name + " does not exist")

        cursor.close()
        return found

    def insert_user(self, cnx, name, email, logger):
        """
        inserts user

        :type cnx: Object
        :param cnx: DB connection

        :type name: str
        :param name: name of the user

        :type email: str
        :param email: email of the user

        :type logger: Object
        :param logger: logger
        """
        cursor = cnx.cursor()

        query = "INSERT IGNORE INTO user " \
                "VALUES (%s, %s, %s)"
        arguments = [None, name, email]
        cursor.execute(query, arguments)
        cnx.commit()
        cursor.close()

    def select_user_id_by_email(self, cnx, email, logger):
        """
        selects user id by email

        :type cnx: Object
        :param cnx: DB connection

        :type email: str
        :param email: email of the user

        :type logger: Object
        :param logger: logger
        """
        found = None
        if email:
            cursor = cnx.cursor()
            query = "SELECT id " \
                    "FROM user " \
                    "WHERE email = %s"
            arguments = [email]
            cursor.execute(query, arguments)

            row = cursor.fetchone()

            if row:
                found = row[0]
            else:
                logger.warning("there is not user with this email " + email)

            cursor.close()
        return found

    def select_user_id_by_name(self, cnx, name, logger):
        """
        selects user id by name

        :type cnx: Object
        :param cnx: DB connection

        :type name: str
        :param name: name of the user

        :type logger: Object
        :param logger: logger
        """
        found = None
        if name:
            found = None
            cursor = cnx.cursor()
            query = "SELECT id " \
                    "FROM user " \
                    "WHERE name = %s"
            arguments = [name]
            cursor.execute(query, arguments)

            row = cursor.fetchone()

            if row:
                found = row[0]
            else:
                logger.warning("there is not user with this name " + name)

            cursor.close()
        return found

    def select_forum_id(self, cnx, forum_name, logger):
        """
        selects forum id

        :type cnx: Object
        :param cnx: DB connection

        :type forum_name: str
        :param forum_name: name of the forum

        :type logger: Object
        :param logger: logger
        """
        found = None
        cursor = cnx.cursor()
        query = "SELECT id " \
                "FROM forum " \
                "WHERE name = %s"
        arguments = [forum_name]
        cursor.execute(query, arguments)

        row = cursor.fetchone()

        if row:
            found = row[0]
        else:
            logger.error("the forum " + forum_name + " does not exist")

        cursor.close()
        return found

    def select_issue_tracker_id(self, cnx, issue_tracker_name, logger):
        """
        selects issue tracker id

        :type cnx: Object
        :param cnx: DB connection

        :type issue_tracker_name: str
        :param issue_tracker_name: name of the issue tracker

        :type logger: Object
        :param logger: logger
        """
        found = None
        cursor = cnx.cursor()
        query = "SELECT id " \
                "FROM issue_tracker " \
                "WHERE name = %s"
        arguments = [issue_tracker_name]
        cursor.execute(query, arguments)

        row = cursor.fetchone()

        if row:
            found = row[0]
        else:
            logger.error("the issue tracker " + issue_tracker_name + " does not exist")

        cursor.close()
        return found

    def get_issue_dependency_type_id(self, cnx, name):
        """
        selects issue dependency type id

        :type cnx: Object
        :param cnx: DB connection

        :type name: str
        :param name: dependency type name
        """
        found = None
        cursor = cnx.cursor()
        query = "SELECT id FROM issue_dependency_type WHERE name = %s"
        arguments = [name]
        cursor.execute(query, arguments)

        row = cursor.fetchone()
        cursor.close()

        if row:
            found = row[0]

        return found

    def get_message_type_id(self, cnx, name):
        """
        selects message type id

        :type cnx: Object
        :param cnx: DB connection

        :type name: str
        :param name: message type name
        """

        found = None
        cursor = cnx.cursor()
        query = "SELECT id FROM message_type WHERE name = %s"
        arguments = [name]
        cursor.execute(query, arguments)
        row = cursor.fetchone()

        if row:
            found = row[0]

        cursor.close()
        return found

    def set_database(self, cnx, db_name):
        """
        set database

        :type cnx: Object
        :param cnx: DB connection

        :type db_name: str
        :param db_name: name of the database
        """
        cursor = cnx.cursor()
        use_database = "USE " + db_name
        cursor.execute(use_database)
        cursor.close()

    def set_settings(self, cnx):
        """
        set database settings

        :type cnx: Object
        :param cnx: DB connection
        """
        cursor = cnx.cursor()
        cursor.execute("set global innodb_file_format = BARRACUDA")
        cursor.execute("set global innodb_file_format_max = BARRACUDA")
        cursor.execute("set global innodb_large_prefix = ON")
        cursor.execute("set global character_set_server = utf8")
        cursor.execute("set global max_connections = 500")
        cursor.close()

    def restart_connection(self, config, logger):
        """
        restart DB connection

        :type config: dict
        :param config: the DB configuration file

        :type logger: Object
        :param logger: logger
        """
        logger.info("restarting connection...")
        return mysql.connector.connect(**config)
