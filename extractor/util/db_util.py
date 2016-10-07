#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'valerio cosentino'

import mysql.connector
from mysql.connector import errorcode

class DbUtil():

    def lowercase(self, str):
        if str:
            str = str.lower()

        return str

    def select_project_id(self, cnx, project_name, logger):
        found = None
        cursor = cnx.cursor()
        query = "SELECT p.id " \
                "FROM project p " \
                "WHERE p.name = %s"
        arguments = [project_name]
        cursor.execute(query, arguments)
        row = cursor.fetchone()
        cursor.close()

        if row:
            found = row[0]
        else:
            logger.error("the project " + project_name + " does not exist")

        return found

    def insert_repo(self, cnx, project_id, repo_name, logger):
        cursor = cnx.cursor()
        query = "INSERT IGNORE INTO repository " \
                "VALUES (%s, %s, %s)"
        arguments = [None, project_id, repo_name]
        cursor.execute(query, arguments)
        cnx.commit()
        cursor.close()

    def select_repo_id(self, cnx, project_id, repo_name, logger):
        cursor = cnx.cursor()
        query = "SELECT id " \
                "FROM repository " \
                "WHERE name = %s AND project_id = %s"
        arguments = [repo_name, project_id]
        cursor.execute(query, arguments)

        row = cursor.fetchone()
        cursor.close()
        if row:
            found = row[0]
        else:
            logger.error("the repository " + repo_name + " does not exist")

        return found

    def insert_user(self, cnx, name, email, logger):
        cursor = cnx.cursor()

        query = "INSERT IGNORE INTO user " \
                "VALUES (%s, %s, %s)"
        arguments = [None, self.lowercase(name), self.lowercase(email)]
        cursor.execute(query, arguments)
        cnx.commit()
        cursor.close()

    def select_user_id_by_email(self, cnx, email, logger):
        cursor = cnx.cursor()
        query = "SELECT id " \
                "FROM user " \
                "WHERE email = %s"
        arguments = [email]
        cursor.execute(query, arguments)

        row = cursor.fetchone()
        cursor.close()

        found = None
        if row:
            found = row[0]
        else:
            logger.warning("there is not user with this email " + email )

        return found

    def select_user_id_by_name(self, cnx, name, logger):
        cursor = cnx.cursor()
        query = "SELECT id " \
                "FROM user " \
                "WHERE name = %s"
        arguments = [name]
        cursor.execute(query, arguments)

        row = cursor.fetchone()
        cursor.close()

        found = None
        if row:
            found = row[0]
        else:
            logger.warning("there is not user with this name " + name )

        return found

    def get_message_type_id(self, cnx, name):
        found = None
        cursor = cnx.cursor()
        query = "SELECT id FROM message_type WHERE name = %s"
        arguments = [name]
        cursor.execute(query, arguments)
        row = cursor.fetchone()
        cursor.close()

        if row:
            found = row[0]

        return found

    def restart_connection(self, config, logger):
        logger.info("restarting connection...")
        return mysql.connector.connect(**config)
