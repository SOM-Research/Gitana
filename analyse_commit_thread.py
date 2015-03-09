__author__ = 'atlanmod'

import threading
from datetime import datetime
import re
import mysql.connector
from mysql.connector import errorcode
from gitquerier import GitQuerier
import config


class AnalyseCommitThread(threading.Thread):

    def __init__(self,commit_sha, ref_id, repo_id, git_repo_path, db_name, logger):
        super(AnalyseCommitThread, self).__init__()
        self.commit_sha = commit_sha
        self.ref_id = ref_id
        self.repo_id = repo_id
        self.git_repo_path = git_repo_path
        self.db_name = db_name
        self.logger = logger

        self.cnx = mysql.connector.connect(**config.CONFIG)

    def run(self):
        self.analyse_commit(self.commit_sha, self.ref_id, self.repo_id)
        self.cnx.close()

    def analyse_commit(self, commit_sha, ref_id, repo_id):
        querier = GitQuerier(self.git_repo_path, self.logger)
        commit = querier.get_commit_by_sha(commit_sha)

        message = commit.message
        author_name = commit.author.name
        author_email = commit.author.email
        committer_name = commit.committer.name
        committer_email = commit.committer.email
        size = commit.size
        sha = commit.hexsha
        authored_date = datetime.fromtimestamp(commit.authored_date).strftime("%Y-%m-%d %H:%M:%S")
        committed_date = datetime.fromtimestamp(commit.committed_date).strftime("%Y-%m-%d %H:%M:%S")
        #insert author
        author_id = self.insert_developer(author_name, author_email)
        committer_id = self.insert_developer(committer_name, committer_email)
        #insert commit
        self.insert_commit(repo_id, sha, message, author_id, committer_id, authored_date, committed_date, size)

        commit_id = self.select_commit(sha)

        #insert parents of the commit
        self.insert_commit_parents(commit.parents, commit_id, sha, repo_id)
        #insert commits in reference
        self.insert_commit_in_reference(repo_id, commit_id, ref_id)

        try:
            if querier.commit_has_no_parents(commit):
                for diff in querier.get_diffs_no_parent_commit(commit):
                    file_path = diff[0]
                    ext = self.get_ext(file_path)

                    self.insert_file(repo_id, file_path, ext, ref_id)
                    file_id = self.select_file_id(repo_id, file_path, ref_id)

                    patch_content = re.sub(r'^(\w|\W)*\n@@', '@@', diff[1])
                    stats = querier.get_stats_for_file(commit, file_path)
                    status = querier.get_status(stats, diff)

                    #insert file modification
                    last_file_modification = self.insert_file_modification(commit_id, file_id, status,
                                                                      stats[0], stats[1], stats[2],
                                                                      patch_content, authored_date)
                    line_details = querier.get_line_details(patch_content, ext)
                    for line_detail in line_details:
                        self.insert_line_details(last_file_modification, line_detail)
            else:
                for diff in querier.get_diffs(commit):
                    if querier.is_renamed(diff):
                        if diff.rename_from:
                            file_previous = diff.rename_from
                        else:
                            file_previous = diff.diff.split('\n')[1].replace('rename from ', '')


                        if diff.rename_to:
                            file_current = diff.rename_to
                        else:
                            file_current = diff.diff.split('\n')[2].replace('rename to ', '')

                        ext_current = self.get_ext(file_current)

                        #insert new file
                        self.insert_file(repo_id, file_current, ext_current, ref_id)

                        #get id new file
                        current_file_id = self.select_file_id(repo_id, file_current, ref_id)

                        #retrieve the id of the previous file
                        previous_file_id = self.select_file_id(repo_id, file_previous, ref_id)

                        if not previous_file_id:
                            ext_previous = self.get_ext(file_previous)
                            self.insert_file(repo_id, file_previous, ext_previous, ref_id)
                            #self.logger.warning("Git2Db: previous file id not found. commit message " + commit.message)

                        # if current_file_id == previous_file_id:
                        #     self.logger.warning("Git2Db: previous file id is equal to current file id (" + str(current_file_id) + ") " + commit.message)

                        self.insert_file_renamed(repo_id, current_file_id, previous_file_id)
                        self.insert_file_modification(commit_id, current_file_id, "renamed", 0, 0, 0, None, authored_date)
                    else:
                        #insert file
                        #if the file does not have a path, it won't be inserted
                        try:
                            file_path = diff.a_blob.path
                            ext = self.get_ext(file_path)

                            stats = querier.get_stats_for_file(commit, file_path)
                            status = querier.get_status(stats, diff)

                            self.insert_file(repo_id, file_path, ext, ref_id)
                            file_id = self.select_file_id(repo_id, file_path, ref_id)

                            #insert file modification (additions, deletions)
                            patch_content = re.sub(r'^(\w|\W)*\n@@', '@@', diff.diff)
                            last_file_modification = self.insert_file_modification(commit_id, file_id, status,
                                                                              stats[0], stats[1], stats[2], patch_content, authored_date)

                            line_details = querier.get_line_details(patch_content, ext)
                            for line_detail in line_details:
                                self.insert_line_details(last_file_modification, line_detail)
                        except:
                            self.logger.warning("Git2Db: GitPython null file path " + str(sha) + " - " + str(message))
        except AttributeError as e:
            self.logger.error("Git2Db: GitPython just failed on commit " + str(sha) + " - " + str(message) + ". Details: " + str(e))

    def insert_developer(self, name, email):
        cursor = self.cnx.cursor()

        if not name:
            name = '_unknown'
        if not email:
            email = '_unknown'

        query = "INSERT IGNORE INTO " + self.db_name + ".developer " \
                "VALUES (%s, %s, %s)"
        arguments = [None, name, email]
        cursor.execute(query, arguments)
        self.cnx.commit()

        query = "SELECT id " \
                "FROM " + self.db_name + ".developer " \
                "WHERE name = %s AND email = %s"
        arguments = [name, email]
        cursor.execute(query, arguments)
        id = cursor.fetchone()[0]

        cursor.close()
        return id

    def insert_commit(self, repo_id, sha, message, author_id, committer_id, authored_date, committed_date, size):
        cursor = self.cnx.cursor()

        query = "INSERT IGNORE INTO " + self.db_name + ".commit " \
                "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"
        arguments = [None, repo_id, sha, message.strip(), author_id, committer_id, authored_date, committed_date, size]
        cursor.execute(query, arguments)
        self.cnx.commit()

        cursor.close()
        return

    def insert_commit_parents(self, parents, commit_id, sha, repo_id):
        cursor = self.cnx.cursor()
        for parent in parents:
            try:
                parent_id = self.select_commit(parent.hexsha)
            except:
                parent_id = None
                #self.logger.warning("Git2Db: parent commit id not found! SHA parent " + str(parent.hexsha))

            query = "INSERT IGNORE INTO " + self.db_name + ".commit_parent " \
                    "VALUES (%s, %s, %s, %s, %s)"

            if parent_id:
                arguments = [repo_id, commit_id, sha, parent_id, parent.hexsha]
            else:
                arguments = [repo_id, commit_id, sha, None, parent.hexsha]

            cursor.execute(query, arguments)
            self.cnx.commit()

        cursor.close()
        return

    def insert_commit_in_reference(self, repo_id, commit_id, ref_id):
        cursor = self.cnx.cursor()

        query = "INSERT IGNORE INTO " + self.db_name + ".commit_in_reference " \
                "VALUES (%s, %s, %s)"
        arguments = [repo_id, commit_id, ref_id]
        cursor.execute(query, arguments)
        self.cnx.commit()

        cursor.close()
        return

    def select_commit(self, sha):
        cursor = self.cnx.cursor()

        query = "SELECT id " \
                "FROM " + self.db_name + ".commit " \
                "WHERE sha = %s"
        arguments = [sha]
        cursor.execute(query, arguments)
        id = cursor.fetchone()[0]

        cursor.close()
        return id

    def select_file_id(self, repo_id, name, ref_id):
        cursor = self.cnx.cursor()

        query = "SELECT id " \
                "FROM " + self.db_name + ".file " \
                "WHERE name = %s AND repo_id = %s AND ref_id = %s"
        arguments = [name, repo_id, ref_id]
        cursor.execute(query, arguments)
        try:
            id = cursor.fetchone()[0]
        except:
            id = None

        cursor.close()
        return id

    def insert_file(self, repo_id, name, ext, ref_id):
        cursor = self.cnx.cursor()

        query = "INSERT IGNORE INTO " + self.db_name + ".file " \
                "VALUES (%s, %s, %s, %s, %s)"
        arguments = [None, repo_id, name, ext, ref_id]
        cursor.execute(query, arguments)
        self.cnx.commit()

        cursor.close()
        return

    def insert_file_renamed(self, repo_id, current_file_id, previous_file_id):
        cursor = self.cnx.cursor()

        query = "INSERT IGNORE INTO " + self.db_name + ".file_renamed " \
                "VALUES (%s, %s, %s)"
        arguments = [repo_id, current_file_id, previous_file_id]
        cursor.execute(query, arguments)
        self.cnx.commit()

        cursor.close()
        return

    def insert_file_modification(self, commit_id, file_id, status, additions, deletions, changes, patch_content, authored_date):
        cursor = self.cnx.cursor()

        query = "INSERT IGNORE INTO " + self.db_name + ".file_modification " \
                "VALUES (NULL, %s, %s, %s, %s, %s, %s, %s, %s)"
        arguments = [commit_id, file_id, status, additions, deletions, changes, patch_content, authored_date]
        cursor.execute(query, arguments)
        self.cnx.commit()

        query = "SELECT id " \
                "FROM " + self.db_name + ".file_modification " \
                "WHERE commit_id = %s AND file_id = %s AND authored_date = %s"
        arguments = [commit_id, file_id, authored_date]
        cursor.execute(query, arguments)
        id = cursor.fetchone()[0]

        cursor.close()
        return id

    def insert_line_details(self, file_modification_id, detail):
        cursor = self.cnx.cursor()
        query = "INSERT IGNORE INTO " + self.db_name + ".line_detail " \
                "VALUES (%s, %s, %s, %s, %s, %s, %s)"

        arguments = [file_modification_id, detail[0], detail[1], detail[2], detail[3], detail[4], detail[5]]

        cursor.execute(query, arguments)
        self.cnx.commit()

        cursor.close()
        return

    def get_ext(self, str):
        if '.' in str:
            ext = str.split('.')[-1]
        else:
            ext = 'no_ext'
        return ext

    #not used, future extension
    def get_type(self, str):
        type = "text"
        if str.startswith('Binary files'):
            type = "binary"
        return type