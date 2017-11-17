#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'valerio cosentino'

from git import *
import re
from datetime import datetime
import string
from util.date_util import DateUtil
import time


class GitQuerier():
    """
    This class collects the data available on Git by using Git python library
    """

    # python, java, html, xml, sql, javascript, c, c++, scala, php, ruby, matlab
    ALLOWED_EXTENSIONS = ['py', 'java', 'html', 'xml', 'sql', 'js', 'c', 'cpp', 'cc', 'scala', 'php', 'rb', 'm']

    def __init__(self, git_repo_path, logger):
        """
        :type git_repo_path: str
        :param git_repo_path: local path of the Git repository

        :type logger: Object
        :param logger: logger
        """
        try:
            self._logger = logger
            self._repo = Repo(git_repo_path, odbt=GitCmdObjectDB)
            self._gitt = self._repo.git
            self._date_util = DateUtil()
        except:
            self._logger.error("GitQuerier init failed")
            raise

    def get_ext(self, filepath):
        """
        gets the extension of the file

        :type filepath: str
        :param filepath: local path of the file
        """
        ext = None
        if filepath:
            ext = filepath.split('.')[-1]
        return ext

    def _get_type(self, str):
        # not used, future extension
        type = "text"
        if str.startswith('Binary files'):
            type = "binary"
        return type

    def _get_diffs_manually(self, parent, commit, retrieve_patch):
        # gets diffs using the Git command
        diffs = []
        content = self._repo.git.execute(["git", "show", commit.hexsha])
        lines = content.split('\n')
        flag = False
        file_a = None
        file_b = None
        for line in lines:
            if flag:
                if line.startswith("similarity"):
                    diff = {"rename_from": file_a, "rename_to": file_b, "renamed": True}
                    diffs = diffs + [diff]
                else:
                    try:
                        if retrieve_patch:
                            diff = parent.diff(commit, paths=file_a, create_patch=True)
                        else:
                            diff = parent.diff(commit, paths=file_a, create_patch=False)
                    except Exception:
                        self._logger.error("diff not retrieved ", exc_info=True)
                        diff = []

                    diffs = diffs + diff

                flag = False

                if not diff:
                    self._logger.warning("GitQuerier: diff empty for commit: " +
                                         commit.hexsha + " file_a: " + str(file_a) + " file_b: " + str(file_b))

            if re.match("^diff \-\-git", line):
                try:
                    line_content = re.sub("^diff \-\-git ", "", line).strip().replace("\"", "")
                    file_a = line_content.split("a/", 1)[1].split(" b/")[0].strip()
                    file_b = line_content.split(" b/")[1].strip()

                    flag = True
                except Exception:
                    self._logger.error("Error when parsing diff git ", exc_info=True)

        return diffs

    def get_diffs(self, commit, files_in_commit, retrieve_patch):
        """
        gets the diffs of a commit

        :type commit: Object
        :param commit: the Object representing the commit

        :type retrieve_patch: bool
        :param retrieve_patch: retrieve patch content
        """
        parent = commit.parents[0]

        diffs = self._get_diffs_manually(parent, commit, retrieve_patch)

        return diffs

    def commit_has_no_parents(self, commit):
        """
        checks a commit has no parents

        :type commit: Object
        :param commit: the Object representing the commit
        """
        flag = False
        if not commit.parents:
            flag = True

        return flag

    def get_commit_time(self, string_time):
        """
        gets commit time from timestamp

        :type string_time: str
        :param string_time: timestamp
        """
        return self._date_util.get_time_fromtimestamp(string_time, "%Y-%m-%d %H:%M:%S")

    def get_files_in_ref(self, ref):
        """
        gets files in a given reference

        :type ref: str
        :param ref: name of the reference
        """
        files = []
        git = self._repo.git
        content = git.execute(["git", "ls-tree", "-r", ref])
        for line in content.split("\n"):
            files.append(line.split("\t")[-1])
        return files

    def get_file_content(self, ref, _file):
        """
        gets content of a file for a given reference

        :type ref: str
        :param ref: name of the reference

        :type _file: str
        :param _file: repo file path
        """
        git = self._repo.git
        return git.execute(["git", "show", ref + ":" + _file])

    def get_diffs_no_parent_commit(self, commit):
        """
        gets diff of a commit without parent

        :type commit: Object
        :param commit: the Object representing the commit
        """
        diffs = []
        content = self._repo.git.execute(["git", "show", commit.hexsha])
        lines = content.split('\n')
        flag = False
        file_a = None
        for line in lines:
            if re.match("^diff \-\-git", line):
                line_content = re.sub("^diff \-\-git ", "", line)

                if file_a:
                    diffs.append((file_a, content))
                    flag = False
                file_a = line_content.split(' ')[0].replace("a/", "", 1)
            elif re.match("^@@", line):
                if not flag:
                    flag = True
                    content = line
                else:
                    diffs.append((file_a, content))
                    content = line
            elif flag:
                if line != '\\ No newline at end of file':
                    content = content + '\n' + line

        if file_a:
            diffs.append((file_a, content))
        else:
            self._logger.warning("GitQuerier: diff with first commit not found")
        return diffs

    def get_file_path(self, diff):
        """
        gets the file path from a diff

        :type diff: Object
        :param diff: the Object representing the diff
        """
        file_path = None
        try:
            if diff.a_blob:
                if diff.a_blob.path:
                    file_path = diff.a_blob.path
                else:
                    file_path = diff.a_path
            else:
                # if it is a new file
                if diff.b_blob.path:
                    file_path = diff.b_blob.path
                else:
                    file_path = diff.b_path
        except:
            pass

        return file_path

    def get_file_current(self, diff):
        """
        gets the file name after renaming from a diff

        :type diff: Object
        :param diff: the Object representing the diff
        """
        if isinstance(diff, dict):
            file_current = diff.get('rename_to')
        else:
            if diff.rename_to:
                file_current = diff.rename_to
            else:
                file_current = diff.diff.split('\n')[2].replace('rename to ', '')

        return file_current

    def get_status_with_diff(self, stats, diff):
        """
        gets the status from a diff

        :type diff: Object
        :param diff: the Object representing the diff
        """
        additions = stats[0]
        deletions = stats[1]
        if additions > 0 and deletions == 0:
            status = "added"
        elif additions == 0 and deletions > 0:
            status = "deleted"
        elif additions > 0 and deletions > 0:
            status = "modified"
        else:
            try:
                if diff.new_file:
                    status = "added"
                elif diff.deleted_file:
                    status = "deleted"
                elif additions == 0 and deletions == 0:
                    status = "added"
                else:
                    status = "modified"
            except:
                status = "modified"

        return status

    def is_renamed(self, diff):
        """
        checks a diff is about renaming

        :type diff: Object
        :param diff: the Object representing the diff
        """
        flag = False

        if isinstance(diff, dict):
            flag = diff.get('renamed')
        else:
            try:
                if diff.renamed:
                    flag = True
            except:
                flag = False

            if not flag:
                try:
                    # sometimes the library does not set the renamed value to True even if the file is actually renamed
                    if (not diff.a_blob) and (not diff.b_blob):
                        if re.match(r"^(.*)\nrename from(.*)\nrename to(.*)$", diff.diff, re.M):
                            flag = True
                except:
                    flag = False
        return flag

    def get_stats_for_file(self, commit_stats_files, file_name):
        """
        gets stats of a file

        :type commit_stats_files: Object
        :param commit_stats_files: the Object representing the commit stats

        :type file_name: str
        :param file_name: name of a file
        """
        stats_for_file = ()
        for f in commit_stats_files.keys():
            if f == file_name:
                stats = commit_stats_files.get(f)
                stats_for_file = (stats.get('insertions'), stats.get('deletions'), stats.get('lines'))
                break
        if not stats_for_file:
            stats_for_file = (0, 0, 0)
            self._logger.warning("GitQuerier: stats for file " + file_name + " not found!")
        return stats_for_file

    def get_references(self):
        """
        gets references
        """
        references = []
        for ref in self._repo.references:
            if all(c in string.printable for c in ref.name):
                ref_name = ref.name

                if type(ref) == RemoteReference:
                    if ref_name != "origin/HEAD":
                        references.append((ref_name, 'branch'))
                elif type(ref) == TagReference:
                    references.append((ref_name, 'tag'))
            else:
                self._logger.warning("Git2Db: reference: " + ref.name +
                                     " contains unprintable chars and won't be processed!")
        return references

    def get_commit_property(self, commit, prop):
        """
        gets a commit property

        :type commit: Object
        :param commit: the Object representing the commit

        :type prop: str
        :param prop: the name of a property
        """
        found = None
        try:
            if prop == "message":
                found = commit.message
            elif prop == "author.name":
                found = commit.author.name
            elif prop == "author.email":
                found = commit.author.email
            elif prop == "committer.name":
                found = commit.committer.name
            elif prop == "committer.email":
                found = commit.committer.email
            elif prop == "size":
                found = commit.size
            elif prop == "hexsha":
                found = commit.hexsha
            elif prop == "authored_date":
                found = commit.authored_date
            elif prop == "committed_date":
                found = commit.committed_date
        except:
            # ugly but effective. GitPython may fail in retrieving properties with large content.
            # Waiting some seconds seems to fix the problem
            try:
                time.sleep(5)
                found = self.get_commit_property(commit, prop)
            except:
                found = None
                self._logger.error("GitQuerier: something went wrong when trying to retrieve the attribute " +
                                   prop + " from the commit " + str(commit.hexsha))

        return found

    def get_patch_content(self, diff):
        """
        gets patch content from a diff

        :type diff: Object
        :param diff: the Object representing the diff
        """
        return diff.diff

    def is_new_file(self, diff):
        """
        checks the a diff contains a new file

        :type diff: Object
        :param diff: the Object representing the diff
        """
        return diff.new_file

    def get_rename_from(self, diff):
        """
        gets rename from file from a diff

        :type diff: Object
        :param diff: the Object representing the diff
        """
        if isinstance(diff, dict):
            file_previous = diff.get("rename_from")
        else:
            if diff.rename_from:
                file_previous = diff.rename_from
            else:
                file_previous = diff.diff.split('\n')[1].replace('rename from ', '')

        return file_previous

    def _get_commits(self, ref_name):
        # gets commits from a reference
        commits = []
        for commit in self._repo.iter_commits(rev=ref_name):
            commits.append(commit)
        return commits

    def _get_commits_before_date(self, commits, date):
        # gets commits before a given date
        before_date_object = self._date_util.get_timestamp(date, "%Y-%m-%d")

        selected_commits = []
        for commit in commits:
            committed_date_object = datetime.fromtimestamp(commit.committed_date)
            if committed_date_object <= before_date_object:
                selected_commits.append(commit)

        return selected_commits

    def _get_commits_after_sha(self, commits, sha):
        # gets commits after a commit with a given SHA
        selected_commits = []

        for commit in commits:
            if commit.hexsha == sha:
                break
            else:
                selected_commits.append(commit)

        return selected_commits

    def _order_chronologically_commits(self, commits):
        # order commits in chronological order
        commits.reverse()
        return commits

    def collect_all_commits(self, ref_name):
        """
        gets all commits from a reference

        :type ref_name: str
        :param ref_name: name of the reference
        """
        commits = self._get_commits(ref_name)
        ordered = self._order_chronologically_commits(commits)
        return ordered

    def collect_all_commits_before_date(self, ref_name, date):
        """
        gets all commits from a reference before a given date

        :type ref_name: str
        :param ref_name: name of the reference

        :type date: str
        :param date: a string representing a date YYYY-mm-dd
        """
        commits = self._get_commits(ref_name)
        selected_commits = self._get_commits_before_date(commits, date)
        ordered = self._order_chronologically_commits(selected_commits)
        return ordered

    def collect_all_commits_after_sha(self, ref_name, sha):
        """
        gets all commits from a reference after a given SHA

        :type ref_name: str
        :param ref_name: name of the reference

        :type sha: str
        :param sha: the SHA of a commit
        """
        commits = self._get_commits(ref_name)
        selected_commits = self._get_commits_after_sha(commits, sha)
        ordered = self._order_chronologically_commits(selected_commits)
        return ordered

    def collect_all_commits_after_sha_before_date(self, ref_name, sha, before_date):
        """
        gets all commits from a reference after a given SHA and before a given date

        :type ref_name: str
        :param ref_name: name of the reference

        :type sha: str
        :param sha: the SHA of a commit

        :type before_date: str
        :param before_date: import data before date (YYYY-mm-dd)
        """
        commits = self._get_commits(ref_name)
        selected_commits = self._get_commits_after_sha(commits, sha)
        selected_commits = self._get_commits_before_date(selected_commits, before_date)
        ordered = self._order_chronologically_commits(selected_commits)
        return ordered

    def get_line_details(self, patch_content, file_extension):
        """
        gets line details from a patch

        :type patch_content: str
        :param patch_content: content of a patch

        :type file_extension: str
        :param file_extension: extension of the file used to identify comments within the patch
        """
        details = []
        block_comment = False
        previous_block_comment = False

        lines = patch_content.split('\n')
        previous_original_line = 0
        previous_new_line = 0
        original_line = 0
        new_line = 0
        for line in lines:
            is_commented = False
            is_partially_commented = False
            # if the line contains diff info
            if re.match(r"^@@(\s|\+|\-|\d|,)+@@", line, re.M):
                # re-init parameters
                begin = self._get_file_modification_begin(line)
                original_line = begin[0]
                new_line = begin[1]

                if block_comment:
                    previous_block_comment = True
                else:
                    previous_block_comment = False
                block_comment = False
            # if the line does not contain diff info
            else:
                # collect content of the line
                # check if the line concerns an addition
                if re.match(r"^\+.*", line, re.M):

                    # check if the line is empty
                    if self._line_is_empty(line):
                        self._add_to_details(details, "addition", new_line, False, False, True, line)
                    else:
                        if file_extension in GitQuerier.ALLOWED_EXTENSIONS:
                            # calculate if the line is commented
                            result = self._line_is_commented("addition", previous_block_comment, previous_new_line,
                                                             new_line, block_comment, details, line, file_extension)
                            details = result[0]
                            previous_block_comment = result[1]
                            block_comment = result[2]
                            is_commented = result[3]
                            is_partially_commented = result[4]

                        self._add_to_details(details, "addition", new_line, is_commented,
                                             is_partially_commented, False, line)

                    previous_new_line = new_line
                    new_line += 1
                # check if the line concerns a deletion
                elif re.match(r"^\-.*", line, re.M):
                    # check if the line is empty
                    if self._line_is_empty(line):
                        self._add_to_details(details, "deletion", original_line, False, False, True, line)
                    else:
                        if file_extension in GitQuerier.ALLOWED_EXTENSIONS:
                            # calculate if the line is commented
                            result = self._line_is_commented("deletion", previous_block_comment,
                                                             previous_original_line, original_line, block_comment,
                                                             details, line, file_extension)
                            details = result[0]
                            previous_block_comment = result[1]
                            block_comment = result[2]
                            is_commented = result[3]
                            is_partially_commented = result[4]

                        self._add_to_details(details, "deletion", original_line, is_commented,
                                             is_partially_commented, False, line)

                    previous_original_line = original_line
                    original_line += 1
                else:
                    if line != '\\ No newline at end of file' and line != '':
                        original_line += 1
                        new_line += 1

        return details

    def _line_is_commented(self, type_change, previous_block_comment, previous_line_number, current_line_number,
                           block_comment, details, line, file_extension):
        # checks a line is commented
        is_commented = False
        is_partially_commented = False
        # if a comment has been added in the previous block, all the lines between the previous block and the current
        # block are marked as commented
        # Note that, it is not possible to check whether the lines between two blocks are empty or not. By default,
        # all these lines are set as not empty
        if previous_block_comment:
            for i in range(previous_line_number, current_line_number):
                self._add_to_details(details, type_change, i, True, False, False, None)
            previous_block_comment = False

        block_comment = self._line_is_in_block_comment(block_comment, line, file_extension)

        # check if the line is commented or it is inside a block comment
        if self._line_is_fully_commented(line, file_extension) or \
                block_comment or previous_block_comment or \
                self._line_contains_only_close_block_comment(line, file_extension) or \
                self._line_ends_with_close_block_comment(line, file_extension):
            is_commented = True
        elif self._line_is_partially_commented(line, file_extension) or \
                self._line_contains_open_block_comment(line, file_extension) or \
                self._line_contains_close_block_comment(line, file_extension):
            is_partially_commented = True

            block_comment = self._line_is_partially_in_block_comment(block_comment, line, file_extension)

        return (details, previous_block_comment, block_comment, is_commented, is_partially_commented)

    def _get_file_modification_begin(self, line):
        # gets the beginning of a file modification
        modified_lines = line.split("@@")[1].strip().split(" ")
        original_starting = modified_lines[0]
        original_line = int(original_starting.split(',')[0].replace('-', ''))
        new_starting = modified_lines[1]
        new_line = int(new_starting.split(',')[0].replace('+', ''))

        return original_line, new_line

    def _add_to_details(self, details, type, line, is_commented, is_partially_commented, is_empty, line_content):
        # stores line details
        details.append((type, line, is_commented, is_partially_commented, is_empty, line_content))
        return

    def _line_is_empty(self, line):
        # checks that a line is empty
        flag = False
        if re.match(r"^(\+|\-)(\s*)$", line, re.M):
            flag = True
        return flag

    def _line_starts_with_open_block_comment(self, line, ext):
        # checks that a line starts with a open block comment
        flag = False
        if ext in ("java", "js", "sql", "c", "cpp", "cc", "scala", "php"):
            if re.match(r"^(\+|\-)(\s*)/\*", line) and not re.match(r"^(\+|\-)(\s*)/\*(.*)(\*/)", line):
                flag = True
        elif ext == "py":
            if re.match(r'^(\+|\-)(\s*)"""', line) and not re.match(r'^(\+|\-)(\s*)"""(.*)(""")', line):
                flag = True
        elif ext in ("xml", "html"):
            if re.match(r'^(\+|\-)(\s*)(<\!\-\-)', line) and not re.match(r"^(\+|\-)(\s*)(<\!\-\-)(.*)(\-\->)", line):
                flag = True
        elif ext in ("rb"):
            if re.match(r'^(\+|\-)(\s*)(\=begin)', line) and not re.match(r"^(\+|\-)(\s*)(\=begin)(.*)(\=end)", line):
                flag = True
        elif ext in ("m"):
            if re.match(r'^(\+|\-)(\s*)(%\{)', line) and not re.match(r"^(\+|\-)(\s*)(%\{)(.*)(%\})", line):
                flag = True

        return flag

    def _line_contains_only_open_block_comment(self, line, ext):
        # checks that a line contains only a open block comment
        flag = False
        if ext in ("java", "js", "sql", "c", "cpp", "cc", "scala", "php"):
            if re.match(r"^(\+|\-)(\s*)(/\*)(\s*)$", line):
                flag = True
        elif ext == "py":
            if re.match(r'^(\+|\-)(\s*)(""")(\s*)$', line):
                flag = True
        elif ext in ("xml", "html"):
            if re.match(r"^(\+|\-)(\s*)(<\!\-\-)(\s*)$", line):
                flag = True
        elif ext in ("rb"):
            if re.match(r"^(\+|\-)(\s*)(\=begin)(\s*)$", line):
                flag = True
        elif ext in ("m"):
            if re.match(r"^(\+|\-)(\s*)(%\{)(\s*)$", line):
                flag = True

        return flag

    def _line_contains_open_block_comment(self, line, ext):
        # checks that a line contains a open block comment
        flag = False
        if ext in ("java", "js", "sql", "c", "cpp", "cc", "scala", "php"):
            if re.match(r"^(\+|\-)(.*)/\*", line) and not re.match(r"^(\+|\-)(.*)/\*(.*)(\*/)", line):
                flag = True
        elif ext == "py":
            if re.match(r'^(\+|\-)(.*)"""', line) and not re.match(r'^(\+|\-)(.*)"""(.*)(""")', line):
                flag = True
        elif ext in ("xml", "html"):
            if re.match(r'^(\+|\-)(.*)(<\!\-\-)', line) and not re.match(r"^(\+|\-)(.*)(<\!\-\-)(.*)(\-\->)", line):
                flag = True
        elif ext in ("rb"):
            if re.match(r'^(\+|\-)(.*)(\=begin)', line) and not re.match(r"^(\+|\-)(.*)(\=begin)(.*)(\=end)", line):
                flag = True
        elif ext in ("m"):
            if re.match(r'^(\+|\-)(.*)(%\{)', line) and not re.match(r"^(\+|\-)(.*)(%\{)(.*)(%\})", line):
                flag = True

        return flag

    def _line_ends_with_close_block_comment(self, line, ext):
        # checks that a line ends with a close block comment
        flag = False
        if ext in ("java", "js", "sql", "c", "cpp", "cc", "scala", "php"):
            if re.match(r"^(\+|\-)(.*)\*/(\s*)$", line) and not re.match(r"^(\+|\-)(\s*)(/\*)(.*)\*/(\s*)$", line):
                flag = True
        elif ext == "py":
            if re.match(r'^(\+|\-)(.*)"""(\s*)$', line) and not re.match(r'^(\+|\-)(\s*)(""")(.*)"""(\s*)$', line):
                flag = True
        elif ext in ("xml", "html"):
            if re.match(r"^(\+|\-)(.*)(\-\->(\s*)$)", line) and \
                    not re.match(r"^(\+|\-)(\s*)(<\!\-\-)(.*)(\-\->)(\s*)$", line):
                flag = True
        elif ext in ("rb"):
            if re.match(r'^(\+|\-)(.*)(\=end)(\s*)$', line) and \
                    not re.match(r"^(\+|\-)(\s*)(\=begin)(.*)(\=end)(\s*)$", line):
                flag = True
        elif ext in ("m"):
            if re.match(r'^(\+|\-)(.*)(%\})(\s*)$', line) and \
                    not re.match(r"^(\+|\-)(\s*)(%\{)(.*)(%\})(\s*)$", line):
                flag = True

        return flag

    def _line_starts_with_close_block_comment(self, line, ext):
        # checks that a line starts with a close block comment
        flag = False
        if ext in ("java", "js", "sql", "c", "cpp", "cc", "scala", "php"):
            if re.match(r"^(\+|\-)(\s*)\*/", line):
                flag = True
        elif ext == "py":
            if re.match(r'^(\+|\-)(\s*)"""', line) and not re.match(r'^(\+|\-)(\s*)"""(.*)(""")', line):
                flag = True
        elif ext in ("xml", "html"):
            if re.match(r'^(\+|\-)(\s*)(\-\->)', line):
                flag = True
        elif ext in ("rb"):
            if re.match(r'^(\+|\-)(\s*)(\=end)', line):
                flag = True
        elif ext in ("m"):
            if re.match(r'^(\+|\-)(\s*)(%\})', line):
                flag = True

        return flag

    def _line_contains_only_close_block_comment(self, line, ext):
        # checks that a line contains only a close block comment
        flag = False
        if ext in ("java", "js", "sql", "c", "cpp", "cc", "scala", "php"):
            if re.match(r"^(\+|\-)(\s*)\*/(\s*)$", line):
                flag = True
        elif ext == "py":
            if re.match(r'^(\+|\-)(\s*)"""(\s*)$', line) and not re.match(r'^(\+|\-)(\s*)(""")(.*)"""(\s*)$', line):
                flag = True
        elif ext in ("xml", "html"):
            if re.match(r"^(\+|\-)(\s*)(\-\->)(\s*)$", line):
                flag = True
        elif ext in ("rb"):
            if re.match(r'^(\+|\-)(\s*)(.*)(\=end)(\s*)$', line):
                flag = True
        elif ext in ("m"):
            if re.match(r'^(\+|\-)(\s*)(.*)(%\})(\s*)$', line):
                flag = True

        return flag

    def _line_contains_close_block_comment(self, line, ext):
        # checks that a line contains a close block comment
        flag = False
        if ext in ("java", "js", "sql", "c", "cpp", "cc", "scala", "php"):
            if re.match(r"^(\+|\-)(.*)\*/", line) and not re.match(r"^(\+|\-)(.*)/\*(.*)(\*/)", line):
                flag = True
        elif ext == "py":
            if re.match(r'^(\+|\-)(.*)"""', line) and not re.match(r'^(\+|\-)(.*)"""(.*)(""")', line):
                flag = True
        elif ext in ("xml", "html"):
            if re.match(r'^(\+|\-)(.*)(\-\->)', line) and not re.match(r"^(\+|\-)(.*)(<\!\-\-)(.*)(\-\->)", line):
                flag = True
        elif ext in ("rb"):
            if re.match(r'^(\+|\-)(.*)(\=end)', line) and not re.match(r"^(\+|\-)(.*)(\=begin)(.*)(\=end)", line):
                flag = True
        elif ext in ("m"):
            if re.match(r'^(\+|\-)(.*)(%\})', line) and not re.match(r"^(\+|\-)(.*)(%\{)(.*)(%\})", line):
                flag = True

        return flag

    def _line_is_partially_commented(self, line, ext):
        # checks that a line is partially commented
        flag = False
        if ext in ("java", "js", "c", "cpp", "cc", "scala"):
            if re.match(r"^(\+|\-)(.*)(/\*)(.*)\*/", line) or \
                    re.match(r"^(\+|\-)(.*)//", line):
                flag = True
        elif ext in ("py", "rb"):
            if re.match(r"^(\+|\-)(.*)\#", line):
                flag = True
        elif ext in ("xml", "html"):
            if re.match(r"^(\+|\-)(.*)(<\!\-\-)(.*)(\-\->)", line):
                flag = True
        elif ext == "sql":
            if re.match(r"^(\+|\-)(.*)(/\*)(.*)(\*/)", line) or \
                    re.match(r"^(\+|\-)(.*)(\-\-\s)", line):
                flag = True
        elif ext == "php":
            if re.match(r"^(\+|\-)(.*)(/\*)(.*)\*/", line) or \
                    re.match(r"^(\+|\-)(.*)//", line) or \
                    re.match(r"^(\+|\-)(.*)\#", line):
                flag = True
        elif ext == "m":
            if re.match(r'^(\+|\-)(.*)(%)', line) or \
                    re.match(r"^(\+|\-)(.*)(%\{)(.*)(%\})", line):
                flag = True
        else:
            self._logger.warning("GitQuerier: impossible to identify comments for extension: " + ext)

        return flag

    def _line_is_fully_commented(self, line, ext):
        # checks that a line is fully commented
        flag = False
        if ext in ("java", "js", "c", "cpp", "cc", "scala"):
            if re.match(r"^(\+|\-)(\s*)(/\*)(.*)\*/(\s*)$", line) or \
                    re.match(r"^(\+|\-)(\s*)//", line):
                flag = True
        elif ext in ("py", "rb"):
            if re.match(r"^(\+|\-)(\s*)\#", line):
                flag = True
        elif ext in ("xml", "html"):
            if re.match(r"^(\+|\-)(\s*)(<\!\-\-)(.*)(\-\->)(\s*)$", line):
                flag = True
        elif ext == "sql":
            if re.match(r"^(\+|\-)(\s*)(/\*)(.*)(\*/)(\s*)$", line) or \
                    re.match(r"^(\+|\-)(\s*)(\-\-\s)", line):
                flag = True
        elif ext == "php":
            if re.match(r"^(\+|\-)(\s*)(/\*)(.*)\*/(\s*)$", line) or \
                    re.match(r"^(\+|\-)(\s*)//", line) or \
                    re.match(r"^(\+|\-)(\s*)\#", line):
                flag = True
        elif ext == "m":
            if re.match(r'^(\+|\-)(\s*)(%)', line) or \
                    re.match(r"^(\+|\-)(\s*)(%\{)(.*)(%\})(\s*)$", line):
                flag = True
        else:
            self._logger.warning("GitQuerier: impossible to identify comments for extension: " + ext)

        return flag

    def _line_is_in_block_comment(self, block_comment, line, ext):
        # checks that a line is within a block comment
        if not block_comment:
            # check if the line starts with a block comment
            if self._line_starts_with_open_block_comment(line, ext) or \
                    self._line_contains_only_open_block_comment(line, ext):
                block_comment = True
        else:
            # check if the line ends with a block comment
            if self._line_ends_with_close_block_comment(line, ext) or \
                    self._line_contains_only_close_block_comment(line, ext) or \
                    self._line_starts_with_close_block_comment(line, ext):
                block_comment = False

        return block_comment

    def _line_is_partially_in_block_comment(self, block_comment, line, ext):
        # checks that a line is partially in a block comment
        if not block_comment:
            if self._line_contains_open_block_comment(line, ext):
                block_comment = True
        else:
            if self._line_contains_close_block_comment(line, ext):
                block_comment = False

        return block_comment
