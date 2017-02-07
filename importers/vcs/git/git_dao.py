#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'valerio cosentino'

from util.db_util import DbUtil


class GitDao():

    def __init__(self, config, logger):
        try:
            self._config = config
            self._logger = logger
            self._db_util = DbUtil()
            self._cnx = self._db_util.get_connection(self._config)
        except:
            self._logger.error("GitDao init failed")
            raise

    def check_connection_alive(self):
        try:
            cursor = self._cnx.cursor()
            cursor.execute("SELECT VERSION()")
            results = cursor.fetchone()
            ver = results[0]
            cursor.close()
            if not ver:
                self._cnx = self._db_util.restart_connection(self._config, self._logger)
        except:
            self._cnx = self._db_util.restart_connection(self._config, self._logger)

    def close_connection(self):
        self._db_util.close_connection(self._cnx)

    def restart_connection(self):
        self._cnx = self._db_util.restart_connection(self._config, self._logger)

    def get_connection(self):
        return self._cnx

    def get_cursor(self):
        return self._cnx.cursor()

    def close_cursor(self, cursor):
        return cursor.close()

    def fetchone(self, cursor):
        return cursor.fetchone()

    def execute(self, cursor, query, arguments):
        cursor.execute(query, arguments)

    def array2string(self, array):
        return ','.join(str(x) for x in array)

    def line_detail_table_is_empty(self, repo_id):
        cursor = self._cnx.cursor()
        query = "SELECT COUNT(*) " \
                "FROM commit c " \
                "JOIN file_modification fm ON c.id = fm.commit_id " \
                "JOIN line_detail l ON fm.id = l.file_modification_id " \
                "WHERE l.content IS NOT NULL AND repo_id = %s"
        arguments = [repo_id]
        cursor.execute(query, arguments)

        row = cursor.fetchone()
        count = 0
        if row:
            count = int(row[0])

        cursor.close()

        return int(count > 0)

    def file_modification_patch_is_empty(self, repo_id):
        cursor = self._cnx.cursor()
        query = "SELECT COUNT(*) " \
                "FROM commit c " \
                "JOIN file_modification fm ON c.id = fm.commit_id " \
                "WHERE patch IS NOT NULL and repo_id = %s"
        arguments = [repo_id]
        cursor.execute(query, arguments)

        row = cursor.fetchone()
        count = 0
        if row:
            count = int(row[0])

        cursor.close()

        return int(count > 0)

    def get_last_commit_id(self, repo_id):
        found = None
        cursor = self._cnx.cursor()
        query = "SELECT MAX(id) as last_commit_id " \
                "FROM commit c " \
                "WHERE repo_id = %s"
        arguments = [repo_id]
        cursor.execute(query, arguments)

        row = cursor.fetchone()
        if row:
            found = row[0]

        cursor.close()
        return found

    def select_repo_id(self, repo_name):
        return self._db_util.select_repo_id(self._cnx, repo_name, self._logger)

    def insert_repo(self, project_id, repo_name):
        return self._db_util.insert_repo(self._cnx, project_id, repo_name, self._logger)

    def select_project_id(self, project_name):
        return self._db_util.select_project_id(self._cnx, project_name, self._logger)

    def get_user_id(self, user_name, user_email):
        user_id = self._db_util.select_user_id_by_email(self._cnx, user_email, self._logger)
        if not user_id:
            self._db_util.insert_user(self._cnx, user_name, user_email, self._logger)
            user_id = self._db_util.select_user_id_by_email(self._cnx, user_email, self._logger)

        return user_id

    def insert_commit_parents(self, parents, commit_id, sha, repo_id):
        cursor = self._cnx.cursor()
        for parent in parents:
            parent_id = self.select_commit_id(parent.hexsha, repo_id)

            if not parent_id:
                self._logger.warning("parent commit id not found! SHA parent " + str(parent.hexsha))

            query = "INSERT IGNORE INTO commit_parent " \
                    "VALUES (%s, %s, %s, %s, %s)"

            if parent_id:
                arguments = [repo_id, commit_id, sha, parent_id, parent.hexsha]
            else:
                arguments = [repo_id, commit_id, sha, None, parent.hexsha]

            cursor.execute(query, arguments)
            self._cnx.commit()

        cursor.close()

    def insert_all_commit_parents(self, parents, commit_id, sha, repo_id):
        to_insert = []
        for parent in parents:
            parent_id = self.select_commit_id(parent.hexsha, repo_id)

            if not parent_id:
                self._logger.warning("parent commit id not found! SHA parent " + str(parent.hexsha))

            if parent_id:
                to_insert.append((repo_id, commit_id, sha, parent_id, parent.hexsha))
            else:
                to_insert.append((repo_id, commit_id, sha, None, parent.hexsha))

        if to_insert:
            cursor = self._cnx.cursor()
            query = "INSERT IGNORE INTO commit_parent(repo_id, commit_id, commit_sha, parent_id, parent_sha) VALUES (%s, %s, %s, %s, %s)"
            cursor.executemany(query, [i for i in to_insert])
            self._cnx.commit()
            cursor.close()

    def insert_commits_in_reference(self, commits_data):
        if commits_data:
            cursor = self._cnx.cursor()
            query = "INSERT IGNORE INTO commit_in_reference(repo_id, commit_id, ref_id) VALUES (%s, %s, %s)"
            cursor.executemany(query, commits_data)
            self._cnx.commit()
            cursor.close()

    def insert_commit_in_reference(self, repo_id, commit_id, ref_id):
        cursor = self._cnx.cursor()
        query = "INSERT IGNORE INTO commit_in_reference " \
                "VALUES (%s, %s, %s)"
        arguments = [repo_id, commit_id, ref_id]
        cursor.execute(query, arguments)
        self._cnx.commit()
        cursor.close()

    def insert_line_details(self, file_modification_id, detail):
        cursor = self._cnx.cursor()
        query = "INSERT IGNORE INTO line_detail " \
                "VALUES (%s, %s, %s, %s, %s, %s, %s)"

        arguments = [file_modification_id, detail[0], detail[1], detail[2], detail[3], detail[4], detail[5]]

        cursor.execute(query, arguments)
        self._cnx.commit()
        cursor.close()

    def select_file_modification_id(self, commit_id, file_id):
        cursor = self._cnx.cursor()
        query = "SELECT id " \
                "FROM file_modification " \
                "WHERE commit_id = %s AND file_id = %s"
        arguments = [commit_id, file_id]
        cursor.execute(query, arguments)

        row = cursor.fetchone()
        found = None
        if row:
            found = row[0]

        cursor.close()
        return found

    def insert_file_modification(self, commit_id, file_id, status, additions, deletions, changes, patch_content):
        cursor = self._cnx.cursor()
        query = "INSERT IGNORE INTO file_modification " \
                "VALUES (NULL, %s, %s, %s, %s, %s, %s, %s)"
        arguments = [commit_id, file_id, status, additions, deletions, changes, patch_content]
        cursor.execute(query, arguments)
        self._cnx.commit()
        cursor.close()

    def insert_file_renamed(self, repo_id, current_file_id, previous_file_id):
        cursor = self._cnx.cursor()

        query = "INSERT IGNORE INTO file_renamed " \
                "VALUES (%s, %s, %s)"
        arguments = [repo_id, current_file_id, previous_file_id]
        cursor.execute(query, arguments)
        self._cnx.commit()
        cursor.close()

    def insert_file(self, repo_id, name, ext):
        cursor = self._cnx.cursor()
        query = "INSERT IGNORE INTO file " \
                "VALUES (%s, %s, %s, %s)"
        arguments = [None, repo_id, name, ext]
        cursor.execute(query, arguments)
        self._cnx.commit()
        cursor.close()

    def select_file_id(self, repo_id, name):
        cursor = self._cnx.cursor()
        query = "SELECT id " \
                "FROM file " \
                "WHERE name = %s AND repo_id = %s"
        arguments = [name, repo_id]
        cursor.execute(query, arguments)
        try:
            id = cursor.fetchone()[0]
        except:
            id = None
        cursor.close()
        return id

    def insert_reference(self, repo_id, ref_name, ref_type):
        cursor = self._cnx.cursor()
        query = "INSERT IGNORE INTO reference " \
                "VALUES (%s, %s, %s, %s)"
        arguments = [None, repo_id, ref_name, ref_type]
        cursor.execute(query, arguments)
        self._cnx.commit()
        cursor.close()

    def select_reference_name(self, repo_id, ref_id):
        cursor = self._cnx.cursor()
        query = "SELECT name " \
                "FROM reference " \
                "WHERE id = %s and repo_id = %s"
        arguments = [ref_id, repo_id]
        cursor.execute(query, arguments)
        name = cursor.fetchone()[0]
        cursor.close()
        return name

    def select_reference_id(self, repo_id, ref_name):
        cursor = self._cnx.cursor()
        query = "SELECT id " \
                "FROM reference " \
                "WHERE name = %s and repo_id = %s"
        arguments = [ref_name, repo_id]
        cursor.execute(query, arguments)
        id = cursor.fetchone()[0]
        cursor.close()
        return id

    def insert_commit(self, repo_id, sha, message, author_id, committer_id, authored_date, committed_date, size):
        cursor = self._cnx.cursor()
        query = "INSERT IGNORE INTO commit " \
                "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"
        arguments = [None, repo_id, sha, message.strip(), author_id, committer_id, authored_date, committed_date, size]
        cursor.execute(query, arguments)
        self._cnx.commit()
        cursor.close()

    def update_commit_parent(self, parent_id, parent_sha, repo_id):
        cursor = self._cnx.cursor()
        query_update = "UPDATE commit_parent " \
                       "SET parent_id = %s " \
                       "WHERE parent_id IS NULL AND parent_sha = %s AND repo_id = %s "
        arguments = [parent_id, parent_sha, repo_id]
        cursor.execute(query_update, arguments)
        self._cnx.commit()
        cursor.close()

    def fix_commit_parent_table(self, repo_id):
        cursor = self._cnx.cursor()
        query_select = "SELECT parent_sha " \
                       "FROM commit_parent " \
                       "WHERE parent_id IS NULL AND repo_id = %s"
        arguments = [repo_id]
        cursor.execute(query_select, arguments)
        row = cursor.fetchone()
        while row:
            parent_sha = row[0]
            parent_id = self.select_commit_id(parent_sha, repo_id)
            self.update_commit_parent(parent_id, parent_sha, repo_id)
            row = cursor.fetchone()
        cursor.close()

    def select_commit_id(self, sha, repo_id):
        found = None
        cursor = self._cnx.cursor()
        query = "SELECT id " \
                "FROM commit " \
                "WHERE sha = %s AND repo_id = %s"
        arguments = [sha, repo_id]
        cursor.execute(query, arguments)
        row = cursor.fetchone()

        if row:
            found = row[0]

        cursor.close()
        return found