__author__ = 'atlanmod'

import simplejson as json
import codecs
from datetime import datetime


class Aliaser():
    NAME_ALIASES = {}

    def __init__(self, json_source_path, json_target_path, name_aliases_path, logging):
        self.json_source_path = json_source_path
        self.json_target_path = json_target_path
        self.name_aliases_path = name_aliases_path

        self.logging = logging

    def get_users_to_dict(self):
        file = codecs.open(self.name_aliases_path, 'r', 'utf-8')
        for line in file:
            splitted_line = line.split(':')
            from_user = splitted_line[0].strip()
            to_user = splitted_line[1].strip()
            Aliaser.NAME_ALIASES.update({from_user: to_user})
        file.close()

    def update_commits(self, commits):
        update_commits = []
        for commit in commits:
            ref = commit.get('ref')
            message = commit.get('message')
            sha = commit.get('sha')
            authored_date = commit.get('authored_date')
            committed_date = commit.get('committed_date')
            author = commit.get('author')
            committer = commit.get('committer')

            update_commits.append({'author': self.update_developer(author),
                                   'committer': self.update_developer(committer),
                                   'authored_date': authored_date,
                                   'committed_date': committed_date,
                                   'sha': sha,
                                   'message': message,
                                   'ref': ref})
        return update_commits

    def update_file_changes(self, changes):
        updated_file_changes = []
        for change in changes:
            deletions = change.get('deletions')
            additions = change.get('additions')
            worked_at = change.get('worked_at')
            patch = change.get('patch')
            author = change.get('author')
            committer = change.get('committer')

            updated_file_changes.append({'author': self.update_developer(author),
                                         'committer': self.update_developer(committer),
                                         'worked_at': worked_at,
                                         'patch': patch,
                                         'additions': additions,
                                         'deletions': deletions})
        return updated_file_changes

    def update_developer(self, developer):
        developer_name = developer.get('name')
        developer_email = developer.get('email')
        if Aliaser.NAME_ALIASES.get(developer_name):
            mapped = Aliaser.NAME_ALIASES.get(developer_name)
            aliased = {'name': mapped, 'email': developer_email}
        else:
            aliased = developer
        return aliased

    def update_lines(self, lines):
        updated_lines = []
        for line in lines:
            line_number = line.get('line')
            updated_line_changes = []
            changes = line.get('line_changes')
            for change in changes:
                partially_commented = change.get('partially_commented')
                is_empty = change.get('is_empty')
                commented = change.get('commented')
                worked_at = change.get('worked_at')
                author = change.get('author')
                committer = change.get('committer')

                updated_line_changes.append({'author': self.update_developer(author),
                                             'committer': self.update_developer(committer),
                                             'worked_at': worked_at,
                                             'commented': commented,
                                             'partially_commented': partially_commented,
                                             'is_empty': is_empty})
            updated_lines.append({'line': line_number, 'changes': updated_line_changes})

        return updated_lines

    def merge_users(self):
        repo_json = codecs.open(self.json_source_path, 'r', 'utf-8')
        repo_merged_users_json = codecs.open(self.json_target_path, 'w', 'utf-8')
        #Each JSON data per line

        for json_line in repo_json:
            json_entry = json.loads(json_line)
            dirs = json_entry.get('dirs')
            id = json_entry.get('id')
            info = json_entry.get('info')
            name = json_entry.get('name')
            ext = json_entry.get('ext')
            line_count = json_entry.get('line_count')
            ref = json_entry.get('ref')
            repo = json_entry.get('repo')
            commits = self.update_commits(json_entry.get('commits'))
            file_changes = self.update_file_changes(json_entry.get('file_changes'))

            #if the json contains line information
            if json_entry.get('lines'):
                lines = self.update_lines(json_entry.get('lines'))
                file_info = {
                    'dirs': dirs,
                    'commits': commits,
                    'id': id,
                    'info': info,
                    'file_changes': file_changes,
                    'name': name,
                    'line_count': line_count,
                    'lines': lines,
                    'repo': repo,
                    'ext': ext,
                    'ref': ref}
            else:
                file_info = {
                    'dirs': dirs,
                    'commits': commits,
                    'id': id,
                    'info': info,
                    'file_changes': file_changes,
                    'name': name,
                    'line_count': line_count,
                    'repo': repo,
                    'ext': ext,
                    'ref': ref}

            repo_merged_users_json.write(json.dumps(file_info) + "\n")

        repo_json.close()
        repo_merged_users_json.close()

    def execute(self):
        start_time = datetime.now()
        if self.name_aliases_path:
            self.get_users_to_dict()
        self.merge_users()
        end_time = datetime.now()

        minutes_and_seconds = divmod((end_time - start_time).total_seconds(), 60)
        self.logging.info("Aliasing: process finished after " + str(minutes_and_seconds[0])
                          + " minutes and " + str(round(minutes_and_seconds[1], 1)) + " secs")