__author__ = 'atlanmod'

import simplejson as json
import codecs
from datetime import datetime


class Filter():


    FILTERED_RESOURCES = {}

    FILTERED_EXTENSIONS = []

    def __init__(self, json_repo_path, json_filtered_repo_path, filtered_resources_path, filtered_extensions_path, type, logger):
        self.JSON_REPO_PATH = json_repo_path
        self.JSON_REPO_FILTERED_PATH = json_filtered_repo_path
        self.FILTERED_RESOURCES_PATH = filtered_resources_path
        self.FILTERED_EXTENSIONS_PATH = filtered_extensions_path
        self.type = type
        self.logger = logger

    def get_filtered_files_to_dict(self):
        filtered_file = codecs.open(self.FILTERED_RESOURCES_PATH, 'r', 'utf-8')
        for line in filtered_file:
            splitted_line = line.split(':')
            ref = splitted_line[0].strip()
            dir = splitted_line[1].strip()
            file = splitted_line[2].strip()

            if Filter.FILTERED_RESOURCES.get(ref):
                dir2file_dict = Filter.FILTERED_RESOURCES.get(ref)
                if dir == "*":
                    dir2file_dict.update({'*': '*'})
                    Filter.FILTERED_RESOURCES.update({ref: dir2file_dict})
                elif dir2file_dict.get(dir):
                    files = dir2file_dict.get(dir)
                    if file == "*":
                        dir2file_dict.update({dir: ['*']})
                        Filter.FILTERED_RESOURCES.update({ref: dir2file_dict})
                    else:
                        files.append(file)
                        dir2file_dict.update({dir: files})
                        Filter.FILTERED_RESOURCES.update({ref: dir2file_dict})
                else:
                    if file == "*":
                        dir2file_dict.update({dir: ['*']})
                        Filter.FILTERED_RESOURCES.update({ref: dir2file_dict})
                    else:
                        dir2file_dict.update({dir: [file]})
                        Filter.FILTERED_RESOURCES.update({ref: dir2file_dict})
            else:
                if dir == "*":
                    Filter.FILTERED_RESOURCES.update({ref: {'*': '*'}})
                else:
                    if file == "*":
                        Filter.FILTERED_RESOURCES.update({ref: {dir: ['*']}})
                    else:
                        Filter.FILTERED_RESOURCES.update({ref: {dir: [file]}})
        filtered_file.close()

    def get_filtered_extensions_to_list(self):
        file = codecs.open(self.FILTERED_EXTENSIONS_PATH, 'r', 'utf-8')
        for line in file:
            ext = line.strip()
            Filter.FILTERED_EXTENSIONS.append(ext)
        file.close()

    def is_filtered(self, ext, ref, dir, file):
        found = False

        if ext in Filter.FILTERED_EXTENSIONS:
            found = True
        else:
            if Filter.FILTERED_RESOURCES.get(ref):
                filtered_dirs_in_ref = Filter.FILTERED_RESOURCES.get(ref)
                if filtered_dirs_in_ref.get('*'):
                    found = True
                else:
                    if filtered_dirs_in_ref.get(dir):
                        filtered_files_in_dir = filtered_dirs_in_ref.get(dir)
                        if '*' in filtered_files_in_dir:
                            found = True
                        else:
                            if file in filtered_files_in_dir:
                                found = True
        return found

    def get_dirs(self, dirs):
        #if the file is in the root directory
        if not dirs:
            dirs.append('')

        return dirs

    def select_files(self):
        repo_json = codecs.open(self.JSON_REPO_PATH, 'r', 'utf-8')
        filtered_repo_json = codecs.open(self.JSON_REPO_FILTERED_PATH, 'w', 'utf-8')
        #Each JSON data per line

        for json_line in repo_json:
            json_entry = json.loads(json_line)

            ref = json_entry.get('ref')
            dirs = self.get_dirs(json_entry.get('dirs'))
            ext = json_entry.get('ext')
            file = json_entry.get('name')

            filtered = True
            for dir in dirs:
                if self.is_filtered(ext, ref, dir, file):
                    filtered = False
                    break

            if not filtered:
                filtered_repo_json.write(json.dumps(json_entry) + '\n')
            else:
                self.logger.info("Filtering:" + ref + " - " + dirs[0] + " - " + file + " - " + ext + " --> filtered")

        repo_json.close()
        filtered_repo_json.close()

    def reject_files(self):
        repo_json = codecs.open(self.JSON_REPO_PATH, 'r', 'utf-8')
        filtered_repo_json = codecs.open(self.JSON_REPO_FILTERED_PATH, 'w', 'utf-8')
        #Each JSON data per line

        for json_line in repo_json:
            json_entry = json.loads(json_line)

            ref = json_entry.get('ref')
            dirs = self.get_dirs(json_entry.get('dirs'))
            ext = json_entry.get('ext')
            file = json_entry.get('name')

            #if a directory that includes the file is filtered, the file will be filtered
            filtered = False
            for dir in dirs:
                if self.is_filtered(ext, ref, dir, file):
                    filtered = True
                    break

            if not filtered:
                filtered_repo_json.write(json.dumps(json_entry) + '\n')
            else:
                self.logger.info("Filtering:" + ref + " - " + dirs[0] + " - " + file + " - " + ext + " --> filtered")

        repo_json.close()
        filtered_repo_json.close()

    def filter(self):
        start_time = datetime.now()
        if self.FILTERED_EXTENSIONS_PATH:
            self.get_filtered_extensions_to_list()
        if self.FILTERED_RESOURCES_PATH:
            self.get_filtered_files_to_dict()

        if self.type == "in":
            self.select_files()
        elif self.type == "out":
            self.reject_files()
        else:
            self.logger.error("Filtering: no action type = " + self.type)
        end_time = datetime.now()

        minutes_and_seconds = divmod((end_time-start_time).total_seconds(), 60)
        self.logger.info("Filtering: process finished after " + str(minutes_and_seconds[0])
                     + " minutes and " + str(round(minutes_and_seconds[1], 1)) + " secs")