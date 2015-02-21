__author__ = 'atlanmod'

from git import *
import re
from datetime import datetime


class GitQuerier():

    #python, java, html, xml, sql, javascript, c, c++, scala, php, ruby, matlab
    ALLOWED_EXTENSION = ['py', 'java', 'html', 'xml', 'sql', 'js', 'c', 'cpp', 'cc', 'scala', 'php', 'rb', 'm']

    def __init__(self, git_repo_path, logger):
        self.logger = logger
        self.repo = Repo(git_repo_path)
        self.no_treated_extensions = set()

    def get_diffs(self, commit):
        return commit.parents[0].diff(commit, create_patch=True)

    def commit_has_no_parents(self, commit):
        flag = False;
        if not commit.parents:
            flag = True

        return flag

    #not used, retrieve all the files currently present in a given branch
    def get_files_in_ref(self, ref):
        files = []
        git = self.repo.git
        content = git.execute(["git", "rev-list"])
        for line in content.split("\n"):
            files.append(line)
        return files

    def get_diffs_no_parent_commit(self, commit):
        diffs = []
        content = self.repo.git.execute(["git", "show", commit.hexsha])
        lines = content.split('\n')
        flag = False
        file_a = None
        for line in lines:
            if re.match("^diff \-\-git", line):
                line_content = re.sub("^diff \-\-git ", "", line)
                #if in the first commit there are more than one files, the calculated diff is added to the diffs list,
                #and the process can start analysing the next diffs
                if file_a:
                    diffs.append((file_a, content))
                    flag = False
                file_a = line_content.split(' ')[0].replace("a/", "")
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
            self.logger.warning("GitQuerier: diff with first commit not found")
        return diffs

    def get_status(self, stats, diff):
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
                    #self.logger.warning("GitQuerier: addition and deletion = 0 - diff: " + str(diff))
                    self.logger.warning("GitQuerier: addition and deletion = 0")
                else:
                    status = "modified"
            except:
                status = "modified"

        return status

    def is_renamed(self, diff):
        flag = False
        if diff.renamed:
            flag = True
        #sometimes the library does not set the renamed value to True even if the file is actually renamed
        elif (not diff.a_blob) and (not diff.b_blob):
            if re.match(r"^(.*)\nrename from(.*)\nrename to(.*)$", diff.diff, re.M):
               flag = True
        return flag

    def get_stats_for_file(self, commit, file_name):
        stats_for_file = ()
        for f in commit.stats.files.keys():
            if f == file_name:
                stats = commit.stats.files.get(f)
                stats_for_file = (stats.get('insertions'), stats.get('deletions'), stats.get('lines'))
        if not stats_for_file:
            stats_for_file = (0, 0, 0)
            self.logger.warning("GitQuerier: stats for file " + file_name + " not found!")
        return stats_for_file

    def get_references(self):
        references = []
        for ref in self.repo.references:
            if type(ref) == RemoteReference:
                if ref.name != "origin/HEAD":
                    references.append((ref.name, 'branch'))
            elif type(ref) == TagReference:
                references.append((ref.name, 'tag'))
            else:
                self.logger.warning("Git2Db: " + str(type(ref)) + " not handled in the extractor")

        return references

    def get_commits(self, ref_name):
        commits = []
        for commit in self.repo.iter_commits(rev=ref_name):
            commits.append(commit)
        return commits

    def get_commits_before_date(self, commits, date):
        before_date_object = datetime.strptime(date, "%Y-%m-%d")

        selected_commits = []
        for commit in commits:
            committed_date_object = datetime.fromtimestamp(commit.committed_date)
            if committed_date_object <= before_date_object:
                selected_commits.append(commit)

        return selected_commits

    def get_commits_after_sha(self, commits, sha):
        selected_commits = []

        for commit in commits:
            if commit.hexsha == sha:
                break
            else:
                selected_commits.append(commit)

        return selected_commits

    def order_chronologically_commits(self, commits):
        commits.reverse()
        return commits

    def collect_all_commits(self, ref_name):
        commits = self.get_commits(ref_name)
        ordered = self.order_chronologically_commits(commits)
        return ordered

    def collect_all_commits_before_date(self, ref_name, date):
        commits = self.get_commits(ref_name)
        selected_commits = self.get_commits_before_date(commits, date)
        ordered = self.order_chronologically_commits(selected_commits)
        return ordered

    def collect_all_commits_after_sha(self, ref_name, sha):
        commits = self.get_commits(ref_name)
        selected_commits = self.get_commits_after_sha(commits, sha)
        ordered = self.order_chronologically_commits(selected_commits)
        return ordered

    def collect_all_commits_after_sha_before_date(self, ref_name, sha, before_date):
        commits = self.get_commits(ref_name)
        selected_commits = self.get_commits_after_sha(commits, sha)
        selected_commits = self.get_commits_before_date(selected_commits, before_date)
        ordered = self.order_chronologically_commits(selected_commits)
        return ordered


    #TOO SLOW, CURRENTLY ALL THE DIFF IS STORED IN THE ATTRIBUTE CHANGES
    def get_line_content(self, patch_content, line_number):
        content = ""
        content_list = []
        lines = patch_content.split('\n')
        original_line = 0
        new_line = 0
        original_end = 0
        new_end = 0


        last_content_added = ""

        for line in lines:
            #if the line contains diff info
            if re.match(r"^@@(\s|\+|\-|\d|,)+@@", line, re.M):
                #re-init parameters
                begin = self.get_file_modification_begin(line)
                original_line = begin[0]
                new_line = begin[1]
                end = self.get_file_modification_end(line)
                deletion_end = end[0]
                addition_end = end[1]
            #if the line does not contain diff info
            else:
                if deletion_end > line_number:
                    if len(content_list) == 2:
                        break
                    if original_line > line_number and new_line > line_number:
                        break
                else:
                    if new_line > line_number:
                        break

                #collect content of the line
                #check if the line concerns an addition
                if re.match(r"^\+.*", line, re.M):
                    if new_line == line_number:
                        content_list.append({'type': 'addition', 'text': line[1:]})
                        last_content_added = 'addition'
                    new_line += 1
                #check if the line concerns a deletion
                elif re.match(r"^\-.*", line, re.M):
                    if original_line == line_number:
                        content_list.append({'type': 'deletion', 'text': line[1:]})
                        last_content_added = 'deletion'
                    original_line += 1
                else:
                    if line != '\\ No newline at end of file' and line != '':
                        original_line += 1
                        new_line += 1
        if content_list:
            content = content_list[-1]
        return content

    def get_line_details(self, patch_content, file_extension):
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
            is_empty = False
            is_documentation = False
            #if the line contains diff info
            if re.match(r"^@@(\s|\+|\-|\d|,)+@@", line, re.M):
                #re-init parameters
                begin = self.get_file_modification_begin(line)
                original_line = begin[0]
                new_line = begin[1]

                if block_comment:
                    previous_block_comment = True
                else:
                    previous_block_comment = False
                block_comment = False
            #if the line does not contain diff info
            else:
                #collect content of the line
                #check if the line concerns an addition
                if re.match(r"^\+.*", line, re.M):

                    #check if the line is empty
                    if self.line_is_empty(line):
                        self.add_to_details(details, "addition", new_line, False, False, True, line)
                    else:
                        if file_extension in GitQuerier.ALLOWED_EXTENSION:
                            #calculate if the line is commented
                            result = self.line_is_commented("addition", previous_block_comment, previous_new_line, new_line, block_comment, details, line, file_extension)
                            details = result[0]
                            previous_block_comment = result[1]
                            block_comment = result[2]
                            is_commented = result[3]
                            is_partially_commented = result[4]
                        #else:
                            #self.no_treated_extensions.add(file_extension)
                            #check if the comment contains code or documentation (natural language)
                            #if is_commented:
                            #    guess = guess_lexer(line)
                        self.add_to_details(details, "addition", new_line, is_commented, is_partially_commented, False, line)

                    previous_new_line = new_line
                    new_line += 1
                #check if the line concerns a deletion
                elif re.match(r"^\-.*", line, re.M):
                    #check if the line is empty
                    if self.line_is_empty(line):
                        self.add_to_details(details, "deletion", original_line, False, False, True, line)
                    else:
                        if file_extension in GitQuerier.ALLOWED_EXTENSION:
                            #calculate if the line is commented
                            result = self.line_is_commented("deletion", previous_block_comment, previous_original_line, original_line, block_comment, details, line, file_extension)
                            details = result[0]
                            previous_block_comment = result[1]
                            block_comment = result[2]
                            is_commented = result[3]
                            is_partially_commented = result[4]

                        self.add_to_details(details, "deletion", original_line, is_commented, is_partially_commented, False, line)

                    previous_original_line = original_line
                    original_line += 1
                else:
                    if line != '\\ No newline at end of file' and line != '':
                        original_line += 1
                        new_line += 1

        return details

    def add_no_treated_extensions_to_log(self):
        for ext in list(self.no_treated_extensions):
            self.logger.warning("GitQuerier: extension " + str(ext) + " is not treated!")
        return

    def line_is_commented(self, type_change, previous_block_comment, previous_line_number, current_line_number, block_comment, details, line, file_extension):
        is_commented = False
        is_partially_commented = False
        #if a comment has been added in the previous block, all the lines between the previous block and the current block are marked as commented
        #Note that, it is not possible to check whether the lines between two blocks are empty or not. By default, all these lines are set as not empty
        if previous_block_comment:
            for i in range(previous_line_number, current_line_number):
                self.add_to_details(details, type_change, i, True, False, False, None)
            previous_block_comment = False

        block_comment = self.line_is_in_block_comment(block_comment, line, file_extension)

        #check if the line is commented or it is inside a block comment
        if self.line_is_fully_commented(line, file_extension) or \
                block_comment or previous_block_comment or \
                self.line_contains_only_close_block_comment(line, file_extension) or \
                self.line_ends_with_close_block_comment(line, file_extension):
            is_commented = True
        elif self.line_is_partially_commented(line, file_extension) or \
                self.line_contains_open_block_comment(line, file_extension) or \
                self.line_contains_close_block_comment(line, file_extension):
            is_partially_commented = True

            block_comment = self.line_is_partially_in_block_comment(block_comment, line, file_extension)

        return (details, previous_block_comment, block_comment, is_commented, is_partially_commented)

    def get_file_modification_begin(self, line):
        modified_lines = line.split("@@")[1].strip().split(" ")
        original_starting = modified_lines[0]
        original_line = int(original_starting.split(',')[0].replace('-', ''))
        new_starting = modified_lines[1]
        new_line = int(new_starting.split(',')[0].replace('+', ''))

        return original_line, new_line

    def get_file_modification_end(self, line):
        modified_lines = line.split("@@")[1].strip().split(" ")
        original_ending = modified_lines[0]
        original_line = int(original_ending.split(',')[1])
        new_ending = modified_lines[1]
        try:
            new_line = int(new_ending.split(',')[1])
        except:
            new_line = 0

        return original_line, new_line

    def add_to_details(self, details, type, line, is_commented, is_partially_commented, is_empty, line_content):
        details.append((type, line, is_commented, is_partially_commented, is_empty, line_content))
        return

    def line_is_empty(self, line):
        flag = False
        if re.match(r"^(\+|\-)(\s*)$", line, re.M):
            flag = True
        return flag

    def line_starts_with_open_block_comment(self, line, ext):
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

    def line_contains_only_open_block_comment(self, line, ext):
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

    def line_contains_open_block_comment(self, line, ext):
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

    def line_ends_with_close_block_comment(self, line, ext):
        flag = False
        if ext in ("java", "js", "sql", "c", "cpp", "cc", "scala", "php"):
            if re.match(r"^(\+|\-)(.*)\*/(\s*)$", line) and not re.match(r"^(\+|\-)(\s*)(/\*)(.*)\*/(\s*)$", line):
                flag = True
        elif ext == "py":
            if re.match(r'^(\+|\-)(.*)"""(\s*)$', line) and not re.match(r'^(\+|\-)(\s*)(""")(.*)"""(\s*)$', line):
                flag = True
        elif ext in ("xml", "html"):
            if re.match(r"^(\+|\-)(.*)(\-\->(\s*)$)", line) and not re.match(r"^(\+|\-)(\s*)(<\!\-\-)(.*)(\-\->)(\s*)$", line):
                flag = True
        elif ext in ("rb"):
            if re.match(r'^(\+|\-)(.*)(\=end)(\s*)$', line) and not re.match(r"^(\+|\-)(\s*)(\=begin)(.*)(\=end)(\s*)$", line):
                flag = True
        elif ext in ("m"):
            if re.match(r'^(\+|\-)(.*)(%\})(\s*)$', line) and not re.match(r"^(\+|\-)(\s*)(%\{)(.*)(%\})(\s*)$", line):
                flag = True

        return flag

    def line_starts_with_close_block_comment(self, line, ext):
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

    def line_contains_only_close_block_comment(self, line, ext):
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

    def line_contains_close_block_comment(self, line, ext):
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

    def line_is_partially_commented(self, line, ext):
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
            self.logger.warning("GitQuerier: impossible to identify comments for extension: " + ext)

        return flag

    def line_is_fully_commented(self, line, ext):
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
            self.logger.warning("GitQuerier: impossible to identify comments for extension: " + ext)

        return flag

    def line_is_in_block_comment(self, block_comment, line, ext):
        if not block_comment:
            #check if the line starts with a block comment
            if self.line_starts_with_open_block_comment(line, ext) or self.line_contains_only_open_block_comment(line, ext):
                block_comment = True
        else:
            #check if the line ends with a block comment
            if self.line_ends_with_close_block_comment(line, ext) or \
                    self.line_contains_only_close_block_comment(line, ext) or \
                    self.line_starts_with_close_block_comment(line, ext):
                block_comment = False

        return block_comment

    def line_is_partially_in_block_comment(self, block_comment, line, ext):
        if not block_comment:
            if self.line_contains_open_block_comment(line, ext):
                block_comment = True
        else:
            if self.line_contains_close_block_comment(line, ext):
                block_comment = False

        return block_comment