#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'valerio cosentino'

from util.db_util import DbUtil


class GitDao():
    """
    This class handles the persistence and retrieval of Git data
    """


    def __init__(self, config, logger):
        """
        :type config: dict
        :param config: the DB configuration file

        :type logger: Object
        :param logger: logger
        """
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
        """
        checks line detail table is empty

        :type repo_id: int
        :param repo_id: id of an existing repository in the DB
        """
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
        """
        checks patch column in file modification table is empty

        :type repo_id: int
        :param repo_id: id of an existing repository in the DB
        """
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
        """
        gets last commit id

        :type repo_id: int
        :param repo_id: id of an existing repository in the DB
        """
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
        """
        selects id of a repository by its name

        :type repo_name: str
        :param repo_name: name of an existing repository in the DB
        """
        return self._db_util.select_repo_id(self._cnx, repo_name, self._logger)

    def insert_repo(self, project_id, repo_name):
        """
        inserts repository to DB

        :type project_id: int
        :param project_id: id of an existing project in the DB

        :type repo_name: str
        :param repo_name: name of a repository to insert
        """
        return self._db_util.insert_repo(self._cnx, project_id, repo_name, self._logger)

    def select_project_id(self, project_name):
        """
        selects id of a project by its name

        :type project_name: str
        :param project_name: name of an existing project in the DB
        """
        return self._db_util.select_project_id(self._cnx, project_name, self._logger)

    def get_user_id(self, user_name, user_email):
        """
        gets id of a user

        :type user_name: str
        :param user_name: name of the user

        :type user_email: str
        :param user_name: email of the user
        """

        if user_email == None and user_name == None:
            user_name = "uknonwn_user"
            user_email = "uknonwn_user"

        if user_email:
            user_id = self._db_util.select_user_id_by_email(self._cnx, user_email, self._logger)
        else:
            user_id = self._db_util.select_user_id_by_name(self._cnx, user_name, self._logger)

        if not user_id:
            self._db_util.insert_user(self._cnx, user_name, user_email, self._logger)
            user_id = self._db_util.select_user_id_by_email(self._cnx, user_email, self._logger)

        return user_id

    def insert_commit_parents(self, parents, commit_id, sha, repo_id):
        """
        inserts commit parents to DB, one by one

        :type parents: list of Object
        :param parents: parents of a commit

        :type commit_id: int
        :param commit_id: id of the commit

        :type sha: str
        :param sha: SHA of the commit

        :type repo_id: int
        :param repo_id: id of the repository
        """
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
        """
        inserts commit parents to DB all together

        :type parents: list of Object
        :param parents: parents of a commit

        :type commit_id: int
        :param commit_id: id of the commit

        :type sha: str
        :param sha: SHA of the commit

        :type repo_id: int
        :param repo_id: id of the repository
        """
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
        """
        inserts commits to DB all together

        :type commits_data: list of Object
        :param commits_data: commit data
        """
        if commits_data:
            cursor = self._cnx.cursor()
            query = "INSERT IGNORE INTO commit_in_reference(repo_id, commit_id, ref_id) VALUES (%s, %s, %s)"
            cursor.executemany(query, commits_data)
            self._cnx.commit()
            cursor.close()

    def insert_commit_in_reference(self, repo_id, commit_id, ref_id):
        """
        inserts commit to DB

        :type repo_id: int
        :param repo_id: id of the repository

        :type commit_id: int
        :param commit_id: id of the commit

        :type ref_id: int
        :param ref_id: id of the reference
        """
        cursor = self._cnx.cursor()
        query = "INSERT IGNORE INTO commit_in_reference " \
                "VALUES (%s, %s, %s)"
        arguments = [repo_id, commit_id, ref_id]
        cursor.execute(query, arguments)
        self._cnx.commit()
        cursor.close()

    def insert_line_details(self, file_modification_id, detail):
        """
        inserts line details to DB

        :type file_modification_id: int
        :param file_modification_id: id of the file modification

        :type detail: str
        :param detail: line content
        """
        cursor = self._cnx.cursor()
        query = "INSERT IGNORE INTO line_detail " \
                "VALUES (%s, %s, %s, %s, %s, %s, %s)"

        arguments = [file_modification_id, detail[0], detail[1], detail[2], detail[3], detail[4], detail[5]]

        cursor.execute(query, arguments)
        self._cnx.commit()
        cursor.close()

    def select_file_modification_id(self, commit_id, file_id):
        """
        selects file modification id

        :type commit_id: int
        :param commit_id: id of the commit

        :type file_id: int
        :param file_id: id of the file
        """
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
        """
        inserts file modification to DB

        :type commit_id: int
        :param commit_id: id of the commit

        :type file_id: int
        :param file_id: id of the file

        :type status: str
        :param status: type of the modification

        :type additions: int
        :param additions: number of additions

        :type deletions: int
        :param deletions: number of deletions

        :type changes: int
        :param changes: number of changes

        :type patch_content: str
        :param patch_content: content of the patch
        """
        cursor = self._cnx.cursor()
        query = "INSERT IGNORE INTO file_modification " \
                "VALUES (NULL, %s, %s, %s, %s, %s, %s, %s)"
        arguments = [commit_id, file_id, status, additions, deletions, changes, patch_content]
        cursor.execute(query, arguments)
        self._cnx.commit()
        cursor.close()

    def insert_file_renamed(self, repo_id, current_file_id, previous_file_id):
        """
        inserts file renamed information

        :type repo_id: int
        :param repo_id: id of the repository

        :type current_file_id: int
        :param current_file_id: id of the renamed file

        :type previous_file_id: int
        :param previous_file_id: id of the file before renaming
        """
        cursor = self._cnx.cursor()

        query = "INSERT IGNORE INTO file_renamed " \
                "VALUES (%s, %s, %s)"
        arguments = [repo_id, current_file_id, previous_file_id]
        cursor.execute(query, arguments)
        self._cnx.commit()
        cursor.close()

    def insert_file(self, repo_id, name, ext):
        """
        inserts file

        :type repo_id: int
        :param repo_id: id of the repository

        :type name: str
        :param name: name of the file (full path)

        :type ext: str
        :param ext: extension of the file
        """
        cursor = self._cnx.cursor()
        query = "INSERT IGNORE INTO file " \
                "VALUES (%s, %s, %s, %s)"
        arguments = [None, repo_id, name, ext]
        cursor.execute(query, arguments)
        self._cnx.commit()
        cursor.close()

    def select_file_id_before_date(self, repo_id, name, before_date):
        """
        selects id of the file before date

        :type repo_id: int
        :param repo_id: id of the repository

        :type name: str
        :param name: name of the file (full path)

        :type before_date: timestamp
        :param before_date: date
        """
        cursor = self._cnx.cursor()
        query = "SELECT DISTINCT f.id " \
                "FROM file f JOIN file_modification fm ON f.id = fm.file_id " \
                "JOIN commit c ON c.id = fm.commit_id " \
                "WHERE f.name = %s AND f.repo_id = %s AND fm.status = 'added' AND c.authored_date <= '" + str(before_date) + "' "
        arguments = [name, repo_id]
        cursor.execute(query, arguments)
        try:
            id = cursor.fetchone()[0]
        except:
            id = None
        cursor.close()
        return id

    def select_file_id(self, repo_id, name):
        """
        selects id of the file

        :type repo_id: int
        :param repo_id: id of the repository

        :type name: str
        :param name: name of the file (full path)
        """
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
        """
        inserts reference

        :type repo_id: int
        :param repo_id: id of the repository

        :type ref_name: str
        :param ref_name: name of the reference

        :type ref_type: str
        :param ref_type: type of the reference (branch or tag)
        """
        cursor = self._cnx.cursor()
        query = "INSERT IGNORE INTO reference " \
                "VALUES (%s, %s, %s, %s)"
        arguments = [None, repo_id, ref_name, ref_type]
        cursor.execute(query, arguments)
        self._cnx.commit()
        cursor.close()

    def select_reference_name(self, repo_id, ref_id):
        """
        selects reference name by its id

        :type repo_id: int
        :param repo_id: id of the repository

        :type ref_id: int
        :param ref_id: id of the reference
        """
        found = None
        cursor = self._cnx.cursor()
        query = "SELECT name " \
                "FROM reference " \
                "WHERE id = %s and repo_id = %s"
        arguments = [ref_id, repo_id]
        cursor.execute(query, arguments)

        row = cursor.fetchone()

        if row:
            found = row[0]

        cursor.close()

        return found

    def select_reference_id(self, repo_id, ref_name):
        """
        selects reference id by its name

        :type repo_id: int
        :param repo_id: id of the repository

        :type ref_name: str
        :param ref_name: name of the reference
        """
        found = None
        cursor = self._cnx.cursor()
        query = "SELECT id " \
                "FROM reference " \
                "WHERE name = %s and repo_id = %s"
        arguments = [ref_name, repo_id]
        cursor.execute(query, arguments)

        row = cursor.fetchone()
        if row:
            found = row[0]

        cursor.close()
        return found

    def insert_commit(self, repo_id, sha, message, author_id, committer_id, authored_date, committed_date, size):
        """
        inserts commit to DB

        :type repo_id: int
        :param repo_id: id of the repository

        :type sha: str
        :param sha: SHA of the commit

        :type message: str
        :param message: message of the commit

        :type author_id: int
        :param author_id: author id of the commit

        :type committer_id: int
        :param committer_id: committer id of the commit

        :type authored_date: str
        :param authored_date: authored date of the commit

        :type committed_date: str
        :param committed_date: committed date of the commit

        :type size: int
        :param size: size of the commit
        """
        cursor = self._cnx.cursor()
        query = "INSERT IGNORE INTO commit " \
                "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"
        arguments = [None, repo_id, sha, message.strip(), author_id, committer_id, authored_date, committed_date, size]
        cursor.execute(query, arguments)
        self._cnx.commit()
        cursor.close()

    def update_commit_parent(self, parent_id, parent_sha, repo_id):
        """
        inserts commit parent to DB

        :type parent_id: int
        :param parent_id: id of the commit parent

        :type parent_sha: str
        :param parent_sha: SHA of the commit parent

        :type repo_id: int
        :param repo_id: id of the repository
        """
        cursor = self._cnx.cursor()
        query_update = "UPDATE commit_parent " \
                       "SET parent_id = %s " \
                       "WHERE parent_id IS NULL AND parent_sha = %s AND repo_id = %s "
        arguments = [parent_id, parent_sha, repo_id]
        cursor.execute(query_update, arguments)
        self._cnx.commit()
        cursor.close()

    def fix_commit_parent_table(self, repo_id):
        """
        checks for missing commit parent information and fixes it

        :type repo_id: int
        :param repo_id: id of the repository
        """
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
        """
        selects id of a commit by its SHA

        :type sha: str
        :param sha: SHA of the commit

        :type repo_id: int
        :param repo_id: id of the repository
        """
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

    def select_commit_id_before_date(self, sha, repo_id, before_date):
        """
        selects id of a commit by its SHA before a given date

        :type sha: str
        :param sha: SHA of the commit

        :type repo_id: int
        :param repo_id: id of the repository

        :type before_date: timestamp
        :param before_date: date
        """
        found = None
        cursor = self._cnx.cursor()
        query = "SELECT id " \
                "FROM commit " \
                "WHERE sha = %s AND repo_id = %s AND authored_date <= '" + str(before_date) + "' "
        arguments = [sha, repo_id]
        cursor.execute(query, arguments)
        row = cursor.fetchone()

        if row:
            found = row[0]

        cursor.close()
        return found

    def select_all_developer_ids(self, repo_id):
        """
        selects all developers (committers or authors) of a given repo

        :type repo_id: int
        :param repo_id: id of the repository
        """
        user_ids = []
        cursor = self._cnx.cursor()
        query = "SELECT c.author_id " \
                "FROM commit c JOIN repository r ON c.repo_id = r.id JOIN user u ON u.id = c.author_id " \
                "WHERE repo_id = %s AND u.name IS NOT NULL AND u.email IS NOT NULL " \
                "UNION " \
                "SELECT c.committer_id " \
                "FROM commit c JOIN repository r ON c.repo_id = r.id JOIN user u ON u.id = c.committer_id " \
                "WHERE repo_id = %s AND u.name IS NOT NULL AND u.email IS NOT NULL "
        arguments = [repo_id, repo_id]
        cursor.execute(query, arguments)
        row = cursor.fetchone()

        while row:
            user_id = row[0]
            user_ids.append(user_id)
            row = cursor.fetchone()

        cursor.close()
        return user_ids

    def select_sha_commit_by_user(self, user_id, repo_id):
        """
        selects the SHA of the first commit (authored or committed) by a given user id

        :type user_id: int
        :param user_id: id of the user

        :type repo_id: int
        :param repo_id: id of the repository
        """
        found = None
        cursor = self._cnx.cursor()
        query = "SELECT sha " \
                "FROM commit " \
                "WHERE (author_id = %s OR committer_id = %s) AND repo_id = %s " \
                "LIMIT 1"
        arguments = [user_id, user_id, repo_id]
        cursor.execute(query, arguments)
        row = cursor.fetchone()

        if row:
            found = row[0]

        return found

