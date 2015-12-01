__author__ = 'atlanmod'

import mysql.connector
from mysql.connector import errorcode
from datetime import datetime
import simplejson as json
import re
import codecs


class Db2Json:

    def __init__(self, db_name, json_repo_path, line_details, logger):
        self.logger = logger
        self.db_name = db_name
        self.repo_id = 0
        self.json_repo_path = json_repo_path
        self.line_details = line_details

        CONFIG = {
            'user': 'root',
            'password': 'root',
            'host': 'localhost',
            'port': '3306',
            'database': db_name,
            'raise_on_warnings': False,
            'charset': 'utf8',
            'buffered': True
        }

        self.cnx = mysql.connector.connect(**CONFIG)

    def set_repo_id(self):
        cursor = self.cnx.cursor()
        query = "SELECT id FROM repository WHERE name = %s"
        arguments = [self.db_name]
        cursor.execute(query, arguments)
        row = cursor.fetchone()
        self.repo_id = row[0]
        cursor.close()

    def get_diff_info(self, patch_content):
        if patch_content:
            first_line = patch_content.split('\n')[0]
            if re.match(r"^@@(\s|\+|\-|\d|,)+@@", first_line, re.M):
                diff_info = first_line.split("@@")[1]
            else:
                diff_info = "Binary file"
        else:
            diff_info = 'Renamed file'

        return diff_info

    def get_diff_content(self, patch_content):
        if patch_content:
            lines = patch_content.split('\n')
            if re.match(r"^@@(\s|\+|\-|\d|,)+@@", lines[0], re.M):
                first_line_content = lines[0].split("@@")[2]
                diff_content = lines[1:]
                diff_content.insert(0, first_line_content)
                diff_content = '\n'.join(diff_content)
            else:
                diff_content = "No content"
        else:
            diff_content = "No content"

        return diff_content

    def get_patch_info(self, content):
        diff_info = self.get_diff_info(content)
        diff_content = self.get_diff_content(content)
        return {'info': diff_info, 'content': diff_content.decode('utf-8', 'ignore')}

    def get_line_info_per_file(self, file_history):
        lines = []
        cursor = self.cnx.cursor()
        query = "SELECT a.name, a.email, com.name, com.email, ld.line_number, c.sha, c.committed_date, c.authored_date, ld.is_commented, ld.is_partially_commented, ld.is_empty " \
                "FROM (SELECT * FROM file_modification fm WHERE file_id IN (" + self.array2string(file_history) + ")) as fm " \
                "JOIN line_detail ld " \
                "ON fm.id = ld.file_modification_id " \
                "JOIN (SELECT * FROM commit WHERE repo_id = %s) AS c " \
                "ON c.id = fm.commit_id " \
                "JOIN developer a " \
                "ON c.author_id = a.id " \
                "JOIN developer com " \
                "ON c.committer_id = com.id " \
                "GROUP BY c.author_id, c.committer_id, ld.line_number, c.authored_date " \
                "ORDER BY line_number, authored_date DESC;"
        arguments = [self.repo_id]
        cursor.execute(query, arguments)
        row = cursor.fetchone()

        line_info = {}
        while row:
            author_name = row[0]
            author_email = row[1]
            committer_name = row[2]
            committer_email = row[3]
            line_number = int(row[4])
            sha = str(row[5])
            committed_date = str(row[6])
            authored_date = str(row[7])
            is_commented = bool(row[8])
            is_partially_commented = bool(row[9])
            is_empty = bool(row[10])

            author = {'name': author_name, 'email': author_email}
            committer = {'name': committer_name, 'email': committer_email}
            if line_info.get('line'):
                if line_info.get('line') == line_number:
                    line_info.get('line_changes').append({'author': author,
                                                          'committer': committer,
                                                          'authored_date': authored_date,
                                                          'committed_date': committed_date,
                                                          'sha': sha,
                                                          'commented': is_commented,
                                                          'partially_commented': is_partially_commented,
                                                          'is_empty': is_empty})
                else:
                    lines.append(line_info)
                    line_info = {}
                    line_info.update({'line': line_number, 'line_changes': [{'author': author,
                                                                             'committer': committer,
                                                                             'authored_date': authored_date,
                                                                             'committed_date': committed_date,
                                                                             'sha': sha,
                                                                             'commented': is_commented,
                                                                             'partially_commented': is_partially_commented,
                                                                             'is_empty': is_empty}]})
            else:
                line_info.update({'line': line_number, 'line_changes': [{'author': author,
                                                                         'committer': committer,
                                                                         'authored_date': authored_date,
                                                                         'committed_date': committed_date,
                                                                         'sha': sha,
                                                                         'commented': is_commented,
                                                                         'partially_commented': is_partially_commented,
                                                                         'is_empty': is_empty}]})

            row = cursor.fetchone()
        cursor.close()

        return lines

    def get_modification_info_per_file(self, file_history):
        file_modifications = []
        cursor = self.cnx.cursor()
        query = "SELECT c.author_id, a.name, a.email, com.name, com.email, c.sha, c.committed_date, c.authored_date, fm.additions, fm.deletions, fm.patch " \
                "FROM (SELECT * FROM file_modification fm WHERE file_id IN (" + self.array2string(file_history) + ")) as fm " \
                "JOIN (SELECT * FROM commit WHERE repo_id = %s) as c " \
                "ON c.id = fm.commit_id " \
                "JOIN developer a " \
                "ON c.author_id = a.id " \
                "JOIN developer com " \
                "ON c.committer_id = com.id " \
                "GROUP BY c.author_id, c.committer_id, c.authored_date " \
                "ORDER BY c.authored_date DESC;"
        arguments = [self.repo_id]
        cursor.execute(query, arguments)
        row = cursor.fetchone()

        while row:
            author_name = row[1]
            author_email = row[2]
            committer_name = row[3]
            committer_email = row[4]
            sha = row[5]
            committed_date = str(row[6])
            authored_date = str(row[7])
            additions = str(row[8])
            deletions = str(row[9])
            patch = str(row[10])

            patch_info = self.get_patch_info(patch)
            author = {'name': author_name, 'email': author_email}
            committer = {'name': committer_name, 'email': committer_email}
            file_modifications.append({'author': author,
                                       'authored_date': authored_date,
                                       'committer': committer,
                                       'committed_date': committed_date,
                                       'additions': additions,
                                       'deletions': deletions,
                                       'sha': sha,
                                       'patch': patch_info})

            row = cursor.fetchone()
        cursor.close()

        return file_modifications

    def get_previous_renamed_files(self, file_ids):
        cursor = self.cnx.cursor()
        query = "SELECT previous_file_id " \
                "FROM file_renamed " \
                "WHERE current_file_id in (" + self.array2string(file_ids) + ") AND repo_id = %s"
        arguments = [self.repo_id]
        cursor.execute(query, arguments)
        row = cursor.fetchone()
        cursor.close()

        previous = []
        while row:
            previous.append(row[0])
            row = cursor.fetchone()

        cursor.close()
        return previous

    def get_history_for_file(self, file_id):
        history = [file_id]
        previous = self.get_previous_renamed_files([file_id])
        while previous:
            if all(p in history for p in previous):
                break
            history.extend(previous)
            previous = self.get_previous_renamed_files(previous)
        return history

    def get_lines_for_file(self, file_history):
        return self.get_line_info_per_file(file_history)

    def get_changes_for_file(self, file_history):
        return self.get_modification_info_per_file(file_history)

    def array2string(self, array):
        return ','.join(str(x) for x in array)

    def get_directory_path(self, path_elements):
        directory_path = ''
        path_elements.reverse()
        for p in path_elements:
            directory_path = directory_path + p + '/'

        return directory_path

    def get_file_name(self, file_id):
        cursor = self.cnx.cursor()
        query = "SELECT name " \
                "FROM file " \
                "WHERE id = %s"
        arguments = [file_id]
        cursor.execute(query, arguments)
        row = cursor.fetchone()
        cursor.close()

        return row[0]

    def get_directories_for_file(self, file_id):
        directories = []
        name = self.get_file_name(file_id)
        dir = name.split('/')[:-1]
        dir.reverse()

        for d in range(0, len(dir)):
            dir_path = self.get_directory_path(dir[d:])
            directories.append(dir_path)

        return directories

    def get_commits_info(self, file_id):
        commits = []
        cursor = self.cnx.cursor()
        query = "SELECT c.sha, c.message, r.name, a.name, a.email, com.name, com.email, c.authored_date, c.committed_date " \
                "FROM " \
                "(SELECT commit_id FROM file_modification fm WHERE file_id = %s) as fm " \
                "JOIN (SELECT * FROM commit WHERE repo_id = %s) AS c " \
                "ON fm.commit_id = c.id " \
                "JOIN developer a " \
                "ON c.author_id = a.id " \
                "JOIN developer com " \
                "ON c.committer_id = com.id " \
                "JOIN commit_in_reference cin " \
                "ON cin.commit_id = fm.commit_id " \
                "JOIN reference r " \
                "ON r.id = cin.ref_id " \
                "ORDER BY authored_date"
        arguments = [file_id, self.repo_id]
        cursor.execute(query, arguments)
        row = cursor.fetchone()
        while row:
            sha = str(row[0])
            message = str(row[1].encode('utf8'))
            ref = str(row[2])
            author_name = row[3]
            author_email = row[4]
            committer_name = row[5]
            committer_email = row[6]
            authored_date = str(row[7])
            committed_date = str(row[8])

            author = {'name': author_name, 'email': author_email}
            committer = {'name': committer_name, 'email': committer_email}
            commits.append({'sha': sha,
                            'author': author,
                            'committer': committer,
                            'message': message,
                            'ref': ref,
                            'authored_date': authored_date,
                            'committed_date': committed_date})
            row = cursor.fetchone()
        cursor.close()

        return commits

    def get_status_file(self, file_id):
        cursor = self.cnx.cursor()
        query = "SELECT status, last_modification " \
                "FROM " \
                "(SELECT f.file_id, f.status, c.committed_date " \
                "FROM (SELECT file_id, commit_id, status FROM file_modification WHERE file_id = %s) AS f " \
                "JOIN (SELECT * FROM commit WHERE repo_id = %s) AS c " \
                "ON f.commit_id = c.id) AS fm " \
                "JOIN " \
                "(SELECT fm.file_id, max(c.committed_date) AS last_modification " \
                "FROM file_modification fm " \
                "JOIN (SELECT * FROM commit WHERE repo_id = %s) AS c " \
                "WHERE fm.commit_id = c.id AND fm.file_id = %s) AS lm " \
                "ON fm.file_id = lm.file_id " \
                "WHERE fm.committed_date = lm.last_modification"
        arguments = [file_id, self.repo_id, self.repo_id, file_id]
        cursor.execute(query, arguments)

        row = cursor.fetchone()
        cursor.close()
        if row:
            if row[0]:
                status = row[0]
            else:
                status = ""
                self.logger.warning("Db2Json: status of file id " + str(file_id) + " not found")

            if row[1]:
                last_modification = str(row[1])
            else:
                last_modification = ""
                self.logger.warning("Db2Json: last modification of file id " + str(file_id) + " not found")
        else:
            status = ""
            last_modification = ""
            self.logger.warning("Db2Json: status and last modification of file id " + str(file_id) + " not found")

        return {'status': status, 'last_modification': last_modification}

    def add_file_info_to_json(self, repo_json):
        cursor = self.cnx.cursor()
        query = "SELECT f.id, r.name, f.name, f.ext " \
                "FROM file f " \
                "JOIN reference r " \
                "ON f.ref_id = r.id " \
                "WHERE f.repo_id = %s " \
                "ORDER BY ref_id, LENGTH(f.name) - LENGTH(REPLACE(f.name, '/', ''))"
        arguments = [self.repo_id]
        cursor.execute(query, arguments)
        row = cursor.fetchone()
        while row:
            file_id = row[0]
            ref = row[1]
            name = row[2]
            ext = row[3]

            self.logger.info("Db2Json: adding info for ref/file: " + ref + "/" + name)

            if ext:
                ext = ext.split('.')[-1].lower()
            else:
                ext = ''

            status = self.get_status_file(file_id)
            commits = self.get_commits_info(file_id)
            directories_info = self.get_directories_for_file(file_id)
            file_history = self.get_history_for_file(file_id)
            changes_info = self.get_changes_for_file(file_history)

            if self.line_details:
                lines_info = self.get_lines_for_file(file_history)
                file_info = {'repo': self.db_name,
                             'info': status,
                             'commits': commits,
                             'ref': ref,
                             'id': str(file_id),
                             'name': name.split('/')[-1],
                             'ext': ext,
                             'dirs': directories_info,
                             'line_count': len(lines_info),
                             'lines': lines_info,
                             'file_changes': changes_info}
            else:
                file_info = {'repo': self.db_name,
                             'info': status,
                             'commits': commits,
                             'ref': ref,
                             'id': str(file_id),
                             'name': name.split('/')[-1],
                             'ext': ext,
                             'dirs': directories_info,
                             'file_changes': changes_info}
            repo_json.write(json.dumps(file_info) + "\n")
            row = cursor.fetchone()
        cursor.close()

    def export(self):
        start_time = datetime.now()
        repo_json = codecs.open(self.json_repo_path, 'w', "utf-8")
        self.set_repo_id()
        self.add_file_info_to_json(repo_json)
        repo_json.close()
        end_time = datetime.now()
        self.cnx.close()

        minutes_and_seconds = divmod((end_time-start_time).total_seconds(), 60)
        self.logger.info("Db2Json: process finished after " + str(minutes_and_seconds[0])
                     + " minutes and " + str(round(minutes_and_seconds[1], 1)) + " secs")