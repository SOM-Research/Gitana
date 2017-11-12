#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'valerio cosentino'

from util.db_util import DbUtil
from util.logging_util import LoggingUtil
from datetime import datetime


class DbSchema():
    """
    This class initializes the DB schema
    """

    def __init__(self, db_name, config, log_root_path):
        """
        :type db_name: str
        :param db_name: the name of the DB to initialize/connect to, it cannot be null and must follow the format
        allowed in MySQL (http://dev.mysql.com/doc/refman/5.7/en/identifiers.html).
        If a DB having a name equal already exists in Gitana, the existing DB will
        be dropped and a new one will be created


        :type config: dict
        :param config: the DB configuration file

        :type log_root_path: str
        :param log_root_path: the log path
        """
        self._db_name = db_name
        self._config = config
        self._log_root_path = log_root_path
        self._db_util = DbUtil()
        self._logging_util = LoggingUtil()

        log_path = self._log_root_path + "db-schema-" + db_name
        self._logger = self._logging_util.get_logger(log_path)
        self._fileHandler = self._logging_util.get_file_handler(self._logger, log_path, "info")
        self._cnx = self._db_util.get_connection(self._config)

    def __del__(self):
        if self._cnx:
            self._db_util.close_connection(self._cnx)
        if self._logger:
            # deletes the file handler of the logger
            self._logging_util.remove_file_handler_logger(self._logger, self._fileHandler)

    def add_git_tables(self):
        """
        initializes git tables if they do not exist
        """
        self.set_database(self._db_name)
        self._init_git_tables()

    def add_issue_tracker_tables(self):
        """
        initializes issue tracker tables if they do not exist
        """
        self.set_database(self._db_name)
        self._init_shared_tables_issue_tracker_communication_channels()
        self._init_issue_tracker_tables()

    def add_instant_messaging_tables(self):
        """
        initializes instant messaging tables if they do not exist
        """
        self.set_database(self._db_name)
        self._init_shared_tables_issue_tracker_communication_channels()
        self._init_instant_messaging_tables()

    def add_forum_tables(self):
        """
        initializes forum tables if they do not exist
        """
        self.set_database(self._db_name)
        self._init_shared_tables_issue_tracker_communication_channels()
        self._init_forum_tables()

    def init_database(self, init_git, init_issue_tracker, init_forum, init_instant_messaging):
        """
        initializes the database tables and functions

        :type init_git: bool
        :param init_git: if True, it initializes the tables containing git data

        :type init_issue_tracker: bool
        :param init_issue_tracker: if True, it initializes the tables containing issue tracker data

        :type init_forum: bool
        :param init_forum: if True, it initializes the tables containing forum data

        :type init_instant_messaging: bool
        :param init_instant_messaging: if True, it initializes the tables containing instant messaging data
        """
        try:
            self._logger.info("init database started")
            start_time = datetime.now()
            self._create_database()
            self.set_database(self._db_name)
            self._set_settings()

            self._init_common_tables()

            if init_issue_tracker or init_forum or init_instant_messaging:
                self._init_shared_tables_issue_tracker_communication_channels()

            if init_git:
                self._init_git_tables()

            if init_issue_tracker:
                self._init_issue_tracker_tables()

            if init_forum:
                self._init_forum_tables()

            if init_instant_messaging:
                self._init_instant_messaging_tables()

            self._init_functions()
            self._logger.info("database " + self._db_name + " created")

            end_time = datetime.now()

            minutes_and_seconds = self._logging_util.calculate_execution_time(end_time, start_time)
            self._logger.info("Init database finished after " + str(minutes_and_seconds[0]) +
                              " minutes and " + str(round(minutes_and_seconds[1], 1)) + " secs")
        except Exception:
            self._logger.error("init database failed", exc_info=True)

    def create_project(self, project_name):
        """
        inserts a project in the DB

        :type project_name: str
        :param project_name: the name of the project to create
        """
        self._cnx = self._db_util.get_connection(self._config)
        self._db_util.insert_project(self._cnx, self._db_name, project_name)
        self._db_util.close_connection(self._cnx)

    def create_repository(self, project_name, repo_name):
        """
        inserts a repository in the DB

        :type project_name: str
        :param project_name: the name of an existing project

        :type repo_name: str
        :param repo_name: the name of the repository to insert
        """
        self._cnx = self._db_util.get_connection(self._config)
        self.set_database(self._db_name)
        project_id = self._db_util.select_project_id(self._cnx, project_name, self._logger)
        try:
            self._db_util.insert_repo(self._cnx, project_id, repo_name, self._logger)
        except Exception:
            self._logger.error("repository " + repo_name + " not inserted", exc_info=True)
        self._db_util.close_connection(self._cnx)

    def list_projects(self):
        """
        lists all projects contained in the DB
        """
        self._cnx = self._db_util.get_connection(self._config)
        project_names = []
        self.set_database(self._db_name)
        cursor = self._cnx.cursor()
        query = "SELECT name FROM project"
        cursor.execute(query)

        row = cursor.fetchone()

        while row:
            project_names.append(row[0])
            row = cursor.fetchone()

        cursor.close()
        return project_names

    def set_database(self, db_name):
        """
        sets the DB used by the tool

        :type db_name: str
        :param db_name: the name of the DB
        """
        try:
            self._logger.info("set database " + db_name + " started")
            self._db_util.set_database(self._cnx, db_name)
            self._logger.info("set database " + db_name + " finished")
        except Exception:
            self._logger.error("set database failed", exc_info=True)

    def _set_settings(self):
        # sets the settings (max connections, charset, file format, ...) used by the DB
        self._db_util.set_settings(self._cnx)

    def _create_database(self):
        # creates the database
        cursor = self._cnx.cursor()

        drop_database_if_exists = "DROP DATABASE IF EXISTS " + self._db_name
        cursor.execute(drop_database_if_exists)

        create_database = "CREATE DATABASE " + self._db_name
        cursor.execute(create_database)

        cursor.close()

    def _init_functions(self):
        # initializes functions
        cursor = self._cnx.cursor()

        levenshtein_distance = """
        CREATE DEFINER=`root`@`localhost` FUNCTION `levenshtein_distance`
            (s1 VARCHAR(255) CHARACTER SET utf8, s2 VARCHAR(255) CHARACTER SET utf8) RETURNS int(11)
            DETERMINISTIC
        BEGIN
            DECLARE s1_len, s2_len, i, j, c, c_temp, cost INT;
            DECLARE s1_char CHAR CHARACTER SET utf8;
            -- max strlen=255 for this function
            DECLARE cv0, cv1 VARBINARY(256);

            SET s1_len = CHAR_LENGTH(s1),
                s2_len = CHAR_LENGTH(s2),
                cv1 = 0x00,
                j = 1,
                i = 1,
                c = 0;

            IF (s1 = s2) THEN
              RETURN (0);
            ELSEIF (s1_len = 0) THEN
              RETURN (s2_len);
            ELSEIF (s2_len = 0) THEN
              RETURN (s1_len);
            END IF;

            WHILE (j <= s2_len) DO
              SET cv1 = CONCAT(cv1, CHAR(j)),
                  j = j + 1;
            END WHILE;

            WHILE (i <= s1_len) DO
              SET s1_char = SUBSTRING(s1, i, 1),
                  c = i,
                  cv0 = CHAR(i),
                  j = 1;

              WHILE (j <= s2_len) DO
                SET c = c + 1,
                    cost = IF(s1_char = SUBSTRING(s2, j, 1), 0, 1);

                SET c_temp = ORD(SUBSTRING(cv1, j, 1)) + cost;
                IF (c > c_temp) THEN
                  SET c = c_temp;
                END IF;

                SET c_temp = ORD(SUBSTRING(cv1, j+1, 1)) + 1;
                IF (c > c_temp) THEN
                  SET c = c_temp;
                END IF;

                SET cv0 = CONCAT(cv0, CHAR(c)),
                    j = j + 1;
              END WHILE;

              SET cv1 = cv0,
                  i = i + 1;
            END WHILE;

            RETURN (c);
        END"""

        soundex_match = """
        CREATE DEFINER=`root`@`localhost` FUNCTION `soundex_match`
            (s1 VARCHAR(255) CHARACTER SET utf8, s2 VARCHAR(255) CHARACTER SET utf8) RETURNS int(1)
            DETERMINISTIC
        BEGIN
            DECLARE _result INT DEFAULT 0;
            IF SOUNDEX(s1) = SOUNDEX(s2) THEN
                SET _result = 1;
            END IF;
            RETURN _result;
        END"""

        cursor.execute(levenshtein_distance)
        cursor.execute(soundex_match)
        cursor.close()

    def _init_common_tables(self):
        # initializes common tables used by tables modeling git, issue tracker, forum and instant messaging data
        cursor = self._cnx.cursor()

        create_table_project = "CREATE TABLE IF NOT EXISTS project( " \
                               "id int(20) AUTO_INCREMENT PRIMARY KEY, " \
                               "name varchar(255), " \
                               "CONSTRAINT name UNIQUE (name)" \
                               ") ENGINE=InnoDB DEFAULT CHARSET=utf8 ROW_FORMAT=DYNAMIC;"

        create_table_user = "CREATE TABLE IF NOT EXISTS user ( " \
                            "id int(20) AUTO_INCREMENT PRIMARY KEY, " \
                            "name varchar(256), " \
                            "email varchar(256), " \
                            "CONSTRAINT namem UNIQUE (name, email) " \
                            ") ENGINE=InnoDB DEFAULT CHARSET=utf8 ROW_FORMAT=DYNAMIC;"

        create_table_user_alias = "CREATE TABLE IF NOT EXISTS user_alias ( " \
                                  "user_id int(20), " \
                                  "alias_id int(20), " \
                                  "CONSTRAINT a UNIQUE (user_id) " \
                                  ") ENGINE=InnoDB DEFAULT CHARSET=utf8 ROW_FORMAT=DYNAMIC;"

        cursor.execute(create_table_project)
        cursor.execute(create_table_user)
        cursor.execute(create_table_user_alias)

    def _init_shared_tables_issue_tracker_communication_channels(self):
        # initializes shared tables used by tables modeling issue tracker, forum and instant messaging data
        cursor = self._cnx.cursor()

        create_table_label = "CREATE TABLE IF NOT EXISTS label ( " \
                             "id int(20) AUTO_INCREMENT PRIMARY KEY, " \
                             "name varchar(256), " \
                             "CONSTRAINT name UNIQUE (name) " \
                             ") ENGINE=InnoDB DEFAULT CHARSET=utf8 ROW_FORMAT=DYNAMIC;"

        create_table_message = "CREATE TABLE IF NOT EXISTS message ( " \
                               "id int(20) AUTO_INCREMENT PRIMARY KEY, " \
                               "own_id varchar(20), " \
                               "pos int(10), " \
                               "type_id int(20), " \
                               "issue_id int(20), " \
                               "topic_id int(20), " \
                               "channel_id int(20), " \
                               "body longblob, " \
                               "votes int(20), " \
                               "author_id int(20), " \
                               "created_at timestamp NULL DEFAULT NULL," \
                               "CONSTRAINT ip UNIQUE (issue_id, topic_id, channel_id, own_id) " \
                               ") ENGINE=InnoDB DEFAULT CHARSET=utf8 ROW_FORMAT=DYNAMIC;"

        create_table_message_dependency = "CREATE TABLE IF NOT EXISTS message_dependency ( " \
                                          "source_message_id int(20), " \
                                          "target_message_id int(20), " \
                                          "PRIMARY KEY st (source_message_id, target_message_id) " \
                                          ") ENGINE=InnoDB DEFAULT CHARSET=utf8 ROW_FORMAT=DYNAMIC;"

        create_table_message_type = "CREATE TABLE IF NOT EXISTS message_type ( " \
                                    "id int(20) AUTO_INCREMENT PRIMARY KEY, " \
                                    "name varchar(255), " \
                                    "CONSTRAINT name UNIQUE (name) " \
                                    ") ENGINE=InnoDB DEFAULT CHARSET=utf8 ROW_FORMAT=DYNAMIC;"

        insert_message_types = "INSERT IGNORE INTO message_type VALUES (NULL, 'question'), " \
                               "(NULL, 'answer'), " \
                               "(NULL, 'comment'), " \
                               "(NULL, 'accepted_answer'), " \
                               "(NULL, 'reply'), " \
                               "(NULL, 'file_upload'), " \
                               "(NULL, 'info');"

        create_table_attachment = "CREATE TABLE IF NOT EXISTS attachment ( " \
                                  "id int(20) AUTO_INCREMENT PRIMARY KEY, " \
                                  "own_id varchar(20), " \
                                  "message_id int(20), " \
                                  "name varchar(256), " \
                                  "extension varchar(10), " \
                                  "bytes int(20), " \
                                  "url varchar(512), " \
                                  "CONSTRAINT ip UNIQUE (message_id, own_id) " \
                                  ") ENGINE=InnoDB DEFAULT CHARSET=utf8 ROW_FORMAT=DYNAMIC;"

        cursor.execute(create_table_label)
        cursor.execute(create_table_message)
        cursor.execute(create_table_message_dependency)
        cursor.execute(create_table_message_type)
        cursor.execute(insert_message_types)
        cursor.execute(create_table_attachment)

        cursor.close()

    def _init_git_tables(self):
        # initializes tables used to model git data
        cursor = self._cnx.cursor()

        create_table_repository = "CREATE TABLE IF NOT EXISTS repository( " \
                                  "id int(20) AUTO_INCREMENT PRIMARY KEY, " \
                                  "project_id int(20), " \
                                  "name varchar(255), " \
                                  "CONSTRAINT name UNIQUE (name)" \
                                  ") ENGINE=InnoDB DEFAULT CHARSET=utf8 ROW_FORMAT=DYNAMIC;"

        create_table_reference = "CREATE TABLE IF NOT EXISTS reference( " \
                                 "id int(20) AUTO_INCREMENT PRIMARY KEY, " \
                                 "repo_id int(20), " \
                                 "name varchar(255), " \
                                 "type varchar(255), " \
                                 "CONSTRAINT name UNIQUE (repo_id, name, type) " \
                                 ") ENGINE=InnoDB DEFAULT CHARSET=utf8 ROW_FORMAT=DYNAMIC;"

        create_table_commit = "CREATE TABLE IF NOT EXISTS commit(" \
                              "id int(20) AUTO_INCREMENT PRIMARY KEY, " \
                              "repo_id int(20), " \
                              "sha varchar(512), " \
                              "message varchar(512), " \
                              "author_id int(20), " \
                              "committer_id int(20), " \
                              "authored_date timestamp NULL DEFAULT NULL, " \
                              "committed_date timestamp NULL DEFAULT NULL, " \
                              "size int(20), " \
                              "INDEX sha (sha), " \
                              "INDEX auth (author_id), " \
                              "INDEX comm (committer_id), " \
                              "CONSTRAINT s UNIQUE (sha, repo_id) " \
                              ") ENGINE=InnoDB DEFAULT CHARSET=utf8 ROW_FORMAT=DYNAMIC;"

        create_table_commit_parent = "CREATE TABLE IF NOT EXISTS commit_parent(" \
                                     "repo_id int(20), " \
                                     "commit_id int(20), " \
                                     "commit_sha varchar(512), " \
                                     "parent_id int(20), " \
                                     "parent_sha varchar(512), " \
                                     "PRIMARY KEY copa (repo_id, commit_id, parent_id), " \
                                     "CONSTRAINT cshapsha UNIQUE (repo_id, commit_id, parent_sha) " \
                                     ") ENGINE=InnoDB DEFAULT CHARSET=utf8 ROW_FORMAT=DYNAMIC;"

        create_table_commits2reference = "CREATE TABLE IF NOT EXISTS commit_in_reference(" \
                                         "repo_id int(20), " \
                                         "commit_id int(20), " \
                                         "ref_id int(20), " \
                                         "PRIMARY KEY core (commit_id, ref_id) " \
                                         ") ENGINE=InnoDB DEFAULT CHARSET=utf8 ROW_FORMAT=DYNAMIC;"

        create_table_file = "CREATE TABLE IF NOT EXISTS file( " \
                            "id int(20) AUTO_INCREMENT PRIMARY KEY, " \
                            "repo_id int(20), " \
                            "name varchar(512), " \
                            "ext varchar(255), " \
                            "CONSTRAINT rerena UNIQUE (repo_id, name) " \
                            ") ENGINE=InnoDB DEFAULT CHARSET=utf8 ROW_FORMAT=DYNAMIC;"

        create_table_file_renamed = "CREATE TABLE IF NOT EXISTS file_renamed ( " \
                                    "repo_id int(20), " \
                                    "current_file_id int(20), " \
                                    "previous_file_id int(20), " \
                                    "file_modification_id int(20), " \
                                    "PRIMARY KEY cpc (current_file_id, previous_file_id, file_modification_id) " \
                                    ") ENGINE=InnoDB DEFAULT CHARSET=utf8 ROW_FORMAT=DYNAMIC;"

        create_table_file_modification = "CREATE TABLE IF NOT EXISTS file_modification ( " \
                                         "id int(20) AUTO_INCREMENT PRIMARY KEY, " \
                                         "commit_id int(20), " \
                                         "file_id int(20), " \
                                         "status varchar(10), " \
                                         "additions numeric(10), " \
                                         "deletions numeric(10), " \
                                         "changes numeric(10), " \
                                         "patch longblob, " \
                                         "CONSTRAINT cf UNIQUE (commit_id, file_id) " \
                                         ") ENGINE=InnoDB DEFAULT CHARSET=utf8 ROW_FORMAT=DYNAMIC;"

        create_table_line_detail = "CREATE TABLE IF NOT EXISTS line_detail( " \
                                   "file_modification_id int(20)," \
                                   "type varchar(25), " \
                                   "line_number numeric(20), " \
                                   "is_commented numeric(1), " \
                                   "is_partially_commented numeric(1), " \
                                   "is_empty numeric(1), " \
                                   "content longblob, " \
                                   "PRIMARY KEY fityli (file_modification_id, type, line_number) " \
                                   ") ENGINE=InnoDB DEFAULT CHARSET=utf8 ROW_FORMAT=DYNAMIC;"

        # adding it here because "file_dependency" depends on "file" table creation.
        # @todo: find a way to move the following table creation to separate section
        # make "extract_dependency_relations" API interface completely independent.
        create_table_file_dependency = "CREATE TABLE file_dependency ( " \
                                       "repo_id int(20), " \
                                       "ref_id int(20), " \
                                       "source_file_id int(20), " \
                                       "target_file_id int(20), " \
                                       "CONSTRAINT dep UNIQUE (repo_id, ref_id, source_file_id, target_file_id) " \
                                       ") ENGINE=InnoDB DEFAULT CHARSET=utf8 ROW_FORMAT=DYNAMIC;"

        cursor.execute(create_table_repository)
        cursor.execute(create_table_reference)
        cursor.execute(create_table_commit)
        cursor.execute(create_table_commit_parent)
        cursor.execute(create_table_commits2reference)
        cursor.execute(create_table_file)
        cursor.execute(create_table_file_renamed)
        cursor.execute(create_table_file_modification)
        cursor.execute(create_table_line_detail)
        cursor.execute(create_table_file_dependency)
        cursor.close()

    def _init_issue_tracker_tables(self):
        # initializes tables used to model issue tracker data
        cursor = self._cnx.cursor()

        create_table_issue_tracker = "CREATE TABLE IF NOT EXISTS issue_tracker ( " \
                                     "id int(20) AUTO_INCREMENT PRIMARY KEY, " \
                                     "repo_id int(20), " \
                                     "name varchar(512), " \
                                     "type varchar(512), " \
                                     "CONSTRAINT name UNIQUE (name)" \
                                     ") ENGINE=InnoDB DEFAULT CHARSET=utf8 ROW_FORMAT=DYNAMIC;"

        create_table_issue = "CREATE TABLE IF NOT EXISTS issue ( " \
                             "id int(20) AUTO_INCREMENT PRIMARY KEY, " \
                             "own_id varchar(20), " \
                             "issue_tracker_id int(20), " \
                             "summary varchar(512), " \
                             "component varchar(256), " \
                             "version varchar(256), " \
                             "hardware varchar(256), " \
                             "priority varchar(256), " \
                             "severity varchar(256), " \
                             "reference_id int(20), " \
                             "reporter_id int(20), " \
                             "created_at timestamp NULL DEFAULT NULL, " \
                             "last_change_at timestamp NULL DEFAULT NULL, " \
                             "CONSTRAINT ioi UNIQUE (issue_tracker_id, own_id), " \
                             "INDEX u (reporter_id), " \
                             "INDEX r (reference_id) " \
                             ") ENGINE=InnoDB DEFAULT CHARSET=utf8 ROW_FORMAT=DYNAMIC;"

        create_table_issue_assignee = "CREATE TABLE IF NOT EXISTS issue_assignee ( " \
                                      "issue_id int(20), " \
                                      "assignee_id int(20), " \
                                      "PRIMARY KEY il (issue_id, assignee_id) " \
                                      ") ENGINE=InnoDB DEFAULT CHARSET=utf8 ROW_FORMAT=DYNAMIC;"

        create_table_issue_subscriber = "CREATE TABLE IF NOT EXISTS issue_subscriber ( " \
                                        "issue_id int(20), " \
                                        "subscriber_id int(20), " \
                                        "PRIMARY KEY il (issue_id, subscriber_id) " \
                                        ") ENGINE=InnoDB DEFAULT CHARSET=utf8 ROW_FORMAT=DYNAMIC;"

        create_table_issue_event = "CREATE TABLE IF NOT EXISTS issue_event ( " \
                                   "id int(20) AUTO_INCREMENT PRIMARY KEY, " \
                                   "issue_id int(20), " \
                                   "event_type_id int(20), " \
                                   "detail varchar(256), " \
                                   "creator_id int(20), " \
                                   "created_at timestamp NULL DEFAULT NULL, " \
                                   "target_user_id int(20), " \
                                   "CONSTRAINT iecc UNIQUE (issue_id, event_type_id, creator_id, created_at, detail) " \
                                   ") ENGINE=InnoDB DEFAULT CHARSET=utf8 ROW_FORMAT=DYNAMIC;"

        create_table_issue_event_type = "CREATE TABLE IF NOT EXISTS issue_event_type ( " \
                                        "id int(20) AUTO_INCREMENT PRIMARY KEY, " \
                                        "name varchar(256), " \
                                        "CONSTRAINT name UNIQUE (name) " \
                                        ") ENGINE=InnoDB DEFAULT CHARSET=utf8 ROW_FORMAT=DYNAMIC;"

        create_table_issue_labelled = "CREATE TABLE IF NOT EXISTS issue_labelled ( " \
                                      "issue_id int(20), " \
                                      "label_id int(20), " \
                                      "PRIMARY KEY il (issue_id, label_id) " \
                                      ") ENGINE=InnoDB DEFAULT CHARSET=utf8 ROW_FORMAT=DYNAMIC;"

        create_issue_commit_dependency = "CREATE TABLE IF NOT EXISTS issue_commit_dependency ( " \
                                         "issue_id int(20), " \
                                         "commit_id int(20), " \
                                         "PRIMARY KEY ict (issue_id, commit_id) " \
                                         ") ENGINE=InnoDB DEFAULT CHARSET=utf8 ROW_FORMAT=DYNAMIC;"

        create_table_issue_dependency = "CREATE TABLE IF NOT EXISTS issue_dependency ( " \
                                        "issue_source_id int(20), " \
                                        "issue_target_id int(20), " \
                                        "type_id int(20), " \
                                        "PRIMARY KEY st (issue_source_id, issue_target_id, type_id) " \
                                        ") ENGINE=InnoDB DEFAULT CHARSET=utf8 ROW_FORMAT=DYNAMIC;"

        create_issue_dependency_type = "CREATE TABLE IF NOT EXISTS issue_dependency_type (" \
                                       "id int(20) AUTO_INCREMENT PRIMARY KEY, " \
                                       "name varchar(256), " \
                                       "CONSTRAINT name UNIQUE (name) " \
                                       ") ENGINE=InnoDB DEFAULT CHARSET=utf8 ROW_FORMAT=DYNAMIC;"

        insert_issue_dependency_type = "INSERT IGNORE INTO issue_dependency_type VALUES (NULL, 'block'), " \
                                       "(NULL, 'depends'), " \
                                       "(NULL, 'related'), " \
                                       "(NULL, 'duplicated');"

        cursor.execute(create_table_issue_tracker)
        cursor.execute(create_table_issue)
        cursor.execute(create_table_issue_assignee)
        cursor.execute(create_table_issue_subscriber)
        cursor.execute(create_table_issue_event)
        cursor.execute(create_table_issue_event_type)
        cursor.execute(create_table_issue_labelled)
        cursor.execute(create_issue_commit_dependency)
        cursor.execute(create_table_issue_dependency)
        cursor.execute(create_issue_dependency_type)
        cursor.execute(insert_issue_dependency_type)
        cursor.close()

    def _init_forum_tables(self):
        # initializes tables used to model forum data
        cursor = self._cnx.cursor()

        create_table_forum = "CREATE TABLE IF NOT EXISTS forum ( " \
                             "id int(20) AUTO_INCREMENT PRIMARY KEY, " \
                             "project_id int(20), " \
                             "name varchar(512), " \
                             "type varchar(512), " \
                             "CONSTRAINT name UNIQUE (name)" \
                             ") ENGINE=InnoDB DEFAULT CHARSET=utf8 ROW_FORMAT=DYNAMIC;"

        create_table_topic = "CREATE TABLE IF NOT EXISTS topic ( " \
                             "id int(20) AUTO_INCREMENT PRIMARY KEY, " \
                             "own_id varchar(20), " \
                             "forum_id int(20), " \
                             "name varchar(256), " \
                             "votes int(10), " \
                             "views int(10), " \
                             "created_at timestamp NULL DEFAULT NULL, " \
                             "last_change_at timestamp NULL DEFAULT NULL, " \
                             "CONSTRAINT name UNIQUE (forum_id, own_id)" \
                             ") ENGINE=InnoDB DEFAULT CHARSET=utf8 ROW_FORMAT=DYNAMIC;"

        create_table_topic_labelled = "CREATE TABLE IF NOT EXISTS topic_labelled ( " \
                                      "topic_id int(20), " \
                                      "label_id int(20), " \
                                      "PRIMARY KEY il (topic_id, label_id) " \
                                      ") ENGINE=InnoDB DEFAULT CHARSET=utf8 ROW_FORMAT=DYNAMIC;"

        cursor.execute(create_table_forum)
        cursor.execute(create_table_topic)
        cursor.execute(create_table_topic_labelled)

        cursor.close()

    def _init_instant_messaging_tables(self):
        # initializes tables used to model instant messaging data
        cursor = self._cnx.cursor()

        create_table_instant_messaging = "CREATE TABLE IF NOT EXISTS instant_messaging ( " \
                                         "id int(20) AUTO_INCREMENT PRIMARY KEY, " \
                                         "project_id int(20), " \
                                         "name varchar(512), " \
                                         "type varchar(512), " \
                                         "CONSTRAINT name UNIQUE (name)" \
                                         ") ENGINE=InnoDB DEFAULT CHARSET=utf8 ROW_FORMAT=DYNAMIC;"

        create_table_channel = "CREATE TABLE IF NOT EXISTS channel ( " \
                               "id int(20) AUTO_INCREMENT PRIMARY KEY, " \
                               "own_id varchar(20), " \
                               "instant_messaging_id int(20), " \
                               "name varchar(256), " \
                               "description varchar(512), " \
                               "created_at timestamp NULL DEFAULT NULL, " \
                               "last_change_at timestamp NULL DEFAULT NULL, " \
                               "CONSTRAINT name UNIQUE (instant_messaging_id, own_id)" \
                               ") ENGINE=InnoDB DEFAULT CHARSET=utf8 ROW_FORMAT=DYNAMIC;"

        cursor.execute(create_table_instant_messaging)
        cursor.execute(create_table_channel)
        cursor.close()
