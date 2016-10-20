#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'valerio cosentino'

from extractor.util.db_util import DbUtil


class GitDao():

    def __init__(self, config, logger):
        self.config = config
        self.logger = logger
        self.db_util = DbUtil()
        try:
            self.cnx = self.db_util.get_connection(self.config)
        except:
            self.logger.error("GitDao failed", exc_info=True)

    def check_connection_alive(self):
        try:
            cursor = self.cnx.cursor()
            cursor.execute("SELECT VERSION()")
            results = cursor.fetchone()
            ver = results[0]
            if not ver:
                self.cnx = self.db_util.restart_connection(self.config, self.logger)
        except:
            self.cnx = self.db_util.restart_connection(self.config, self.logger)

    def close_connection(self):
        self.db_util.close_connection(self.cnx)

    def restart_connection(self):
        self.cnx = self.db_util.restart_connection(self.config, self.logger)

    def get_connection(self):
        return self.cnx

    def get_cursor(self):
        return self.cnx.cursor()

    def close_cursor(self, cursor):
        return cursor.close()

    def fetchone(self, cursor):
        return cursor.fetchone()

    def execute(self, cursor, query, arguments):
        cursor.execute(query, arguments)

    def array2string(self, array):
        return ','.join(str(x) for x in array)

    def line_detail_table_is_empty(self, repo_id):
        cursor = self.cnx.cursor()
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
        cursor = self.cnx.cursor()
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
        cursor = self.cnx.cursor()
        query = "SELECT MAX(id) as last_commit_id " \
                "FROM commit c " \
                "WHERE repo_id = %s"
        arguments = [repo_id]
        cursor.execute(query, arguments)

        row = cursor.fetchone()
        cursor.close()

        if row:
            found = row[0]

        return found

    def select_repo_id(self, project_id, repo_name):
        return self.db_util.select_repo_id(self.cnx, project_id, repo_name, self.logger)

    def insert_repo(self, project_id, repo_name):
        return self.db_util.insert_repo(self.cnx, project_id, repo_name, self.logger)

    def select_project_id(self, project_name):
        return self.db_util.select_project_id(self.cnx, project_name, self.logger)

    def get_user_id(self, user_name, user_email):
        user_id = self.db_util.select_user_id_by_email(self.cnx, user_email, self.logger)
        if not user_id:
            self.db_util.insert_user(self.cnx, user_name, user_email, self.logger)
            user_id = self.db_util.select_user_id_by_email(self.cnx, user_email, self.logger)

        return user_id

    def delete_commit(self, commit_id, repo_id):
        cursor = self.cnx.cursor()
        query = "DELETE FROM commit WHERE id = %s AND repo_id = %s"
        arguments = [commit_id, repo_id]
        cursor.execute(query, arguments)
        self.cnx.commit()
        cursor.close()

    def delete_file_related_info(self, commit_id):
        cursor = self.cnx.cursor()
        query = "SELECT id, file_id " \
                "FROM file_modification f " \
                "WHERE commit_id = %s"
        arguments = [commit_id]
        cursor.execute(query, arguments)

        row = cursor.fetchone()

        file_modification_ids = []
        while row:
            file_modification_ids.append(row[0])
            row = cursor.fetchone()
        cursor.close()

        if file_modification_ids:
            self.delete_line_details(file_modification_ids)
        self.delete_file_modification(commit_id)

    def delete_commit_parent(self, commit_id, repo_id):
        cursor = self.cnx.cursor()
        query = "DELETE FROM commit_parent WHERE commit_id = %s AND repo_id = %s"
        arguments = [commit_id, repo_id]
        cursor.execute(query, arguments)
        self.cnx.commit()
        cursor.close()

    def delete_commit_in_reference(self, commit_id, repo_id):
        cursor = self.cnx.cursor()
        query = "DELETE FROM commit_in_reference WHERE commit_id = %s AND repo_id = %s"
        arguments = [commit_id, repo_id]
        cursor.execute(query, arguments)
        self.cnx.commit()
        cursor.close()

    def delete_file_modification(self, commit_id):
        cursor = self.cnx.cursor()
        query = "DELETE FROM file_modification WHERE commit_id = %s"
        arguments = [commit_id]
        cursor.execute(query, arguments)
        self.cnx.commit()
        cursor.close()

    def delete_line_details(self, file_modification_ids):
        cursor = self.cnx.cursor()
        query = "DELETE FROM line_detail WHERE file_modification_id IN (" + self.array2string(file_modification_ids) + ")"
        cursor.execute(query)
        self.cnx.commit()
        cursor.close()

    def insert_commit_parents(self, parents, commit_id, sha, repo_id):
        cursor = self.cnx.cursor()
        for parent in parents:
            try:
                parent_id = self.select_commit_id(parent.hexsha, repo_id)
            except:
                parent_id = None
                self.logger.warning("parent commit id not found! SHA parent " + str(parent.hexsha))

            query = "INSERT IGNORE INTO commit_parent " \
                    "VALUES (%s, %s, %s, %s, %s)"

            if parent_id:
                arguments = [repo_id, commit_id, sha, parent_id, parent.hexsha]
            else:
                arguments = [repo_id, commit_id, sha, None, parent.hexsha]

            cursor.execute(query, arguments)
            self.cnx.commit()

        cursor.close()

    def insert_commit_in_reference(self, repo_id, commit_id, ref_id):
        cursor = self.cnx.cursor()
        query = "INSERT IGNORE INTO commit_in_reference " \
                "VALUES (%s, %s, %s)"
        arguments = [repo_id, commit_id, ref_id]
        cursor.execute(query, arguments)
        self.cnx.commit()
        cursor.close()

    def insert_line_details(self, file_modification_id, detail):
        cursor = self.cnx.cursor()
        query = "INSERT IGNORE INTO line_detail " \
                "VALUES (%s, %s, %s, %s, %s, %s, %s)"

        arguments = [file_modification_id, detail[0], detail[1], detail[2], detail[3], detail[4], detail[5]]

        cursor.execute(query, arguments)
        self.cnx.commit()
        cursor.close()

    def select_file_modification_id(self, commit_id, file_id):
        cursor = self.cnx.cursor()
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
        cursor = self.cnx.cursor()
        query = "INSERT IGNORE INTO file_modification " \
                "VALUES (NULL, %s, %s, %s, %s, %s, %s, %s)"
        arguments = [commit_id, file_id, status, additions, deletions, changes, patch_content]
        cursor.execute(query, arguments)
        self.cnx.commit()
        cursor.close()

    def insert_file_renamed(self, repo_id, current_file_id, previous_file_id):
        cursor = self.cnx.cursor()

        query = "INSERT IGNORE INTO file_renamed " \
                "VALUES (%s, %s, %s)"
        arguments = [repo_id, current_file_id, previous_file_id]
        cursor.execute(query, arguments)
        self.cnx.commit()
        cursor.close()

    def insert_file(self, repo_id, name, ext):
        cursor = self.cnx.cursor()
        query = "INSERT IGNORE INTO file " \
                "VALUES (%s, %s, %s, %s)"
        arguments = [None, repo_id, name, ext]
        cursor.execute(query, arguments)
        self.cnx.commit()
        cursor.close()

    def select_file_id(self, repo_id, name):
        cursor = self.cnx.cursor()
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
        cursor = self.cnx.cursor()
        query = "INSERT IGNORE INTO reference " \
                "VALUES (%s, %s, %s, %s)"
        arguments = [None, repo_id, ref_name, ref_type]
        cursor.execute(query, arguments)
        self.cnx.commit()
        cursor.close()

    def select_reference_name(self, repo_id, ref_id):
        cursor = self.cnx.cursor()
        query = "SELECT name " \
                "FROM reference " \
                "WHERE id = %s and repo_id = %s"
        arguments = [ref_id, repo_id]
        cursor.execute(query, arguments)
        name = cursor.fetchone()[0]
        cursor.close()
        return name

    def select_reference_id(self, repo_id, ref_name):
        cursor = self.cnx.cursor()
        query = "SELECT id " \
                "FROM reference " \
                "WHERE name = %s and repo_id = %s"
        arguments = [ref_name, repo_id]
        cursor.execute(query, arguments)
        id = cursor.fetchone()[0]
        cursor.close()
        return id

    def insert_commit(self, repo_id, sha, message, author_id, committer_id, authored_date, committed_date, size):
        cursor = self.cnx.cursor()
        query = "INSERT IGNORE INTO commit " \
                "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"
        arguments = [None, repo_id, sha, message.strip(), author_id, committer_id, authored_date, committed_date, size]
        cursor.execute(query, arguments)
        self.cnx.commit()
        cursor.close()

    def update_commit_parent(self, parent_id, parent_sha, repo_id):
        cursor = self.cnx.cursor()
        query_update = "UPDATE commit_parent " \
                       "SET parent_id = %s " \
                       "WHERE parent_id IS NULL AND parent_sha = %s AND repo_id = %s "
        arguments = [parent_id, parent_sha, repo_id]
        cursor.execute(query_update, arguments)
        self.cnx.commit()
        cursor.close()

    def fix_commit_parent_table(self, repo_id):
        cursor_it = self.cnx.cursor()
        query_select = "SELECT parent_sha " \
                       "FROM commit_parent " \
                       "WHERE parent_id IS NULL AND repo_id = %s"
        arguments = [repo_id]
        cursor_it.execute(query_select, arguments)
        row = cursor_it.fetchone()
        while row:
            parent_sha = row[0]
            parent_id = self.select_commit_id(parent_sha, repo_id)
            self.update_commit_parent(parent_id, parent_sha, repo_id)
            row = cursor_it.fetchone()
        cursor_it.close()

    def select_commit_id(self, sha, repo_id):
        found = None
        cursor = self.cnx.cursor()
        query = "SELECT id " \
                "FROM commit " \
                "WHERE sha = %s AND repo_id = %s"
        arguments = [sha, repo_id]
        cursor.execute(query, arguments)
        row = cursor.fetchone()
        cursor.close()

        if row:
            found = row[0]

        return found