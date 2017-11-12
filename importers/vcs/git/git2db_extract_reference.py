#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'valerio cosentino'

import re
from datetime import datetime

from querier_git import GitQuerier
from git_dao import GitDao
from util.logging_util import LoggingUtil


class Git2DbReference(object):
    """
    This class handles the import of Git references
    """

    # do not import patches
    LIGHT_IMPORT_TYPE = 1
    # import patches but not at line level
    MEDIUM_IMPORT_TYPE = 2
    # import patches also at line level
    FULL_IMPORT_TYPE = 3

    def __init__(self, db_name,
                 repo_id, git_repo_path, before_date, import_type, ref_name, ref_type, from_sha,
                 config, log_root_path):
        """
        :type db_name: str
        :param db_name: the name of an existing DB

        :type repo_id: int
        :param repo_id: the id of an existing repository in the DB

        :type git_repo_path: str
        :param git_repo_path: local path of the Git repository

        :type before_date: str
        :param before_date: import data before date (YYYY-mm-dd)

        :type import_type: int
        :param import_type:
        1 does not import patches,
        2 imports patches but not at line level,
        3 imports patches with line detail

        :type ref_name: str
        :param ref_name: the name of the reference to import

        :type from_sha: str
        :param from_sha: the SHA of the commit from where to start the import

        :type config: dict
        :param config: the DB configuration file

        :type log_root_path: str
        :param log_root_path: the log path
        """
        self._log_root_path = log_root_path
        self._git_repo_path = git_repo_path
        self._repo_id = repo_id
        self._db_name = db_name
        self._ref_name = ref_name
        self._ref_type = ref_type
        self._before_date = before_date
        self._import_type = import_type
        self._from_sha = from_sha
        self._config = config
        self._logging_util = LoggingUtil()
        self._fileHandler = None
        self._logger = None
        self._querier = None
        self._dao = None

    def __call__(self):
        try:
            log_path = self._log_root_path + "-git2db-" + self._make_it_printable(self._ref_name)
            self._logger = self._logging_util.get_logger(log_path)
            self._fileHandler = self._logging_util.get_file_handler(self._logger, log_path, "info")

            self._querier = GitQuerier(self._git_repo_path, self._logger)
            self._dao = GitDao(self._config, self._logger)
            self.extract()
        except Exception:
            self._logger.error("Git2Db failed", exc_info=True)
        finally:
            if self._dao:
                self._dao.close_connection()

    def _make_it_printable(self, str):
        # converts string to UTF-8 and removes empty and non-alphanumeric characters
        u = str.decode('utf-8', 'ignore').lower()
        return re.sub(r'(\W|\s)+', '-', u)

    def _get_info_contribution_in_reference(self, reference_name, reference_type, repo_id, from_sha):
        if from_sha:
            if self._before_date:
                commits = self._querier.collect_all_commits_after_sha_before_date(reference_name, from_sha,
                                                                                  self._before_date)
            else:
                commits = self._querier.collect_all_commits_after_sha(reference_name, from_sha)

            self._analyse_commits(commits, reference_name, repo_id)
        else:
            if self._before_date:
                commits = self._querier.collect_all_commits_before_date(reference_name, self._before_date)
            else:
                commits = self._querier.collect_all_commits(reference_name)

            self._analyse_commits(commits, reference_name, repo_id)

    def _load_all_references(self, repo_id):
        # load all git branches and tags into database
        for reference in self._querier.get_references():
            ref_name = reference[0]
            ref_type = reference[1]
            # inserts reference to DB
            self._dao.insert_reference(repo_id, ref_name, ref_type)

    def _get_diffs_from_commit(self, commit, files_in_commit):
        # calculates diffs within files in a commit
        if self._import_type > Git2DbReference.LIGHT_IMPORT_TYPE:
            diffs = self._querier.get_diffs(commit, files_in_commit, True)
        else:
            diffs = self._querier.get_diffs(commit, files_in_commit, False)

        return diffs

    def _analyse_commit(self, commit, repo_id, ref_id):
        # analyses a commit
        try:
            message = self._querier.get_commit_property(commit, "message")
            author_name = self._querier.get_commit_property(commit, "author.name")
            author_email = self._querier.get_commit_property(commit, "author.email")
            committer_name = self._querier.get_commit_property(commit, "committer.name")
            committer_email = self._querier.get_commit_property(commit, "committer.email")
            size = self._querier.get_commit_property(commit, "size")
            sha = self._querier.get_commit_property(commit, "hexsha")
            authored_date = self._querier.get_commit_time(self._querier.get_commit_property(commit, "authored_date"))
            committed_date = self._querier.get_commit_time(self._querier.get_commit_property(commit, "committed_date"))

            if author_name is None and author_email is None:
                self._logger.warning("author name and email are null for commit: " + sha)

            if committer_name is None and committer_email is None:
                self._logger.warning("committer name and email are null for commit: " + sha)

            # insert author
            author_id = self._dao.get_user_id(author_name, author_email)
            committer_id = self._dao.get_user_id(committer_name, committer_email)

            commit_found = self._dao.select_commit_id(sha, repo_id)

            if not commit_found:
                # insert commit
                self._dao.insert_commit(repo_id, sha, message, author_id, committer_id, authored_date,
                                        committed_date, size)
                commit_found = self._dao.select_commit_id(sha, repo_id)

                commit_stats_files = commit.stats.files
                try:
                    if self._querier.commit_has_no_parents(commit):
                        for diff in self._querier.get_diffs_no_parent_commit(commit):
                            file_path = diff[0]
                            ext = self._querier.get_ext(file_path)

                            self._dao.insert_file(repo_id, file_path, ext)
                            file_id = self._dao.select_file_id(repo_id, file_path)

                            if self._import_type > Git2DbReference.LIGHT_IMPORT_TYPE:
                                patch_content = re.sub(r'^(\w|\W)*\n@@', '@@', diff[1])
                            else:
                                patch_content = None

                            stats = self._querier.get_stats_for_file(commit_stats_files, file_path)
                            status = self._querier.get_status_with_diff(stats, diff)

                            # insert file modification
                            self._dao.insert_file_modification(commit_found, file_id, status,
                                                               stats[0], stats[1], stats[2], patch_content)

                            if self._import_type == Git2DbReference.FULL_IMPORT_TYPE:
                                file_modification_id = self._dao.select_file_modification_id(commit_found, file_id)
                                line_details = self._querier.get_line_details(patch_content, ext)
                                for line_detail in line_details:
                                    self._dao.insert_line_details(file_modification_id, line_detail)
                    else:
                        for diff in self._get_diffs_from_commit(commit, commit_stats_files.keys()):
                            # self.dao.check_connection_alive()
                            if self._querier.is_renamed(diff):
                                file_previous = self._querier.get_rename_from(diff)
                                ext_previous = self._querier.get_ext(file_previous)

                                file_current = self._querier.get_file_current(diff)
                                ext_current = self._querier.get_ext(file_current)

                                # insert new file
                                self._dao.insert_file(repo_id, file_current, ext_current)

                                # get id new file
                                current_file_id = self._dao.select_file_id(repo_id, file_current)

                                # retrieve the id of the previous file
                                previous_file_id = self._dao.select_file_id(repo_id, file_previous)

                                # insert file modification
                                self._dao.insert_file_modification(commit_found, current_file_id, "renamed",
                                                                   0, 0, 0, None)

                                if not previous_file_id:
                                    self._dao.insert_file(repo_id, file_previous, ext_previous)
                                    previous_file_id = self._dao.select_file_id(repo_id, file_previous)

                                if current_file_id == previous_file_id:
                                    self._logger.warning("previous file id is equal to current file id "
                                                         "(" + str(current_file_id) + ") " + str(sha))
                                else:
                                    file_modification_id = self._dao.select_file_modification_id(commit_found,
                                                                                                 current_file_id)
                                    self._dao.insert_file_renamed(repo_id, current_file_id, previous_file_id,
                                                                  file_modification_id)

                            else:
                                # insert file
                                # if the file does not have a path, it won't be inserted
                                try:
                                    file_path = self._querier.get_file_path(diff)

                                    ext = self._querier.get_ext(file_path)

                                    stats = self._querier.get_stats_for_file(commit_stats_files, file_path)
                                    status = self._querier.get_status_with_diff(stats, diff)

                                    # if the file is new, add it
                                    if self._querier.is_new_file(diff):
                                        self._dao.insert_file(repo_id, file_path, ext)
                                    file_id = self._dao.select_file_id(repo_id, file_path)

                                    if not file_id:
                                        self._dao.insert_file(repo_id, file_path, ext)
                                        file_id = self._dao.select_file_id(repo_id, file_path)

                                    if self._import_type > Git2DbReference.LIGHT_IMPORT_TYPE:
                                        # insert file modification (additions, deletions)
                                        patch_content = self._querier.get_patch_content(diff)
                                    else:
                                        patch_content = None

                                    self._dao.insert_file_modification(commit_found, file_id, status,
                                                                       stats[0], stats[1], stats[2], patch_content)

                                    if self._import_type == Git2DbReference.FULL_IMPORT_TYPE:
                                        file_modification_id = self._dao.select_file_modification_id(commit_found,
                                                                                                     file_id)
                                        line_details = self._querier.get_line_details(patch_content, ext)
                                        for line_detail in line_details:
                                            self._dao.insert_line_details(file_modification_id, line_detail)
                                except Exception:
                                    self._logger.error("Something went wrong with commit " + str(sha), exc_info=True)
                except Exception:
                    self._logger.error("Git2Db failed on commit " + str(sha), exc_info=True)

            # insert parents of the commit
            self._dao.insert_commit_parents(commit.parents, commit_found, sha, repo_id)
            # insert commits in reference
            self._dao.insert_commit_in_reference(repo_id, commit_found, ref_id)

        except Exception:
            self._logger.error("Git2Db failed on commit " + str(sha), exc_info=True)

    def _analyse_commits(self, commits, ref, repo_id):
        ref_id = self._dao.select_reference_id(repo_id, ref)

        for c in commits:
            self._analyse_commit(c, repo_id, ref_id)

    def extract(self):
        """
        extracts Git data and stores it in the DB
        """
        try:
            self._logger.info("Git2DbReference started")
            start_time = datetime.now()
            self._load_all_references(self._repo_id)
            self._get_info_contribution_in_reference(self._ref_name, self._ref_type, self._repo_id, self._from_sha)

            end_time = datetime.now()
            minutes_and_seconds = self._logging_util.calculate_execution_time(end_time, start_time)
            self._logger.info("Git2DbReference finished after " + str(minutes_and_seconds[0]) +
                              " minutes and " + str(round(minutes_and_seconds[1], 1)) + " secs")
            self._logging_util.remove_file_handler_logger(self._logger, self._fileHandler)
        except Exception:
            self._logger.error("Git2DbReference failed", exc_info=True)
