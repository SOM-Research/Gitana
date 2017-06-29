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

    def __init__(self, config, log_root_path):
        """
        :type config: dict
        :param config: the DB configuration file

        :type log_root_path: str
        :param log_root_path: the log path
        """
        self._config = config
        self._log_root_path = log_root_path
        self._db_util = DbUtil()
        self._logging_util = LoggingUtil()
        self._logger = None
        self._fileHandler = None

    def __del__(self):
        #deletes the file handler of the logger
        if self._logger:
            self._logging_util.remove_file_handler_logger(self._logger, self._fileHandler)

    def init_database(self, db_name):
        """
        initializes the database tables, functions and stored procedures

        :type db_name: str
        :param db_name: the name of the DB to initialize
        """
        try:
            log_path = self._log_root_path + "init-db-" + db_name
            self._logger = self._logging_util.get_logger(log_path)
            self._fileHandler = self._logging_util.get_file_handler(self._logger, log_path, "info")

            self._logger.info("init database started")
            start_time = datetime.now()
            self._cnx = self._db_util.get_connection(self._config)
            self._create_database(db_name)
            self.set_database(db_name)
            self._set_settings()
            self._init_shared_tables()
            self._init_git_tables()
            self._init_issue_tracker_tables()
            self._init_forum_tables()
            self._init_instant_messaging_tables()
            self._init_functions()
            self._init_stored_procedures()
            self._logger.info("database " + db_name + " created")
            self._db_util.close_connection(self._cnx)
            end_time = datetime.now()

            minutes_and_seconds = self._logging_util.calculate_execution_time(end_time, start_time)
            self._logger.info("Init database finished after " + str(minutes_and_seconds[0])
                         + " minutes and " + str(round(minutes_and_seconds[1], 1)) + " secs")
        except Exception:
            self._logger.error("init database failed", exc_info=True)

    def create_project(self, db_name, project_name):
        """
        inserts a project in the DB

        :type db_name: str
        :param db_name: the name of an existing DB

        :type project_name: str
        :param project_name: the name of the project to create
        """
        self._cnx = self._db_util.get_connection(self._config)
        self._db_util.insert_project(self._cnx, db_name, project_name)
        self._db_util.close_connection(self._cnx)

    def create_repository(self, db_name, project_name, repo_name):
        """
        inserts a repository in the DB

        :type db_name: str
        :param db_name: the name of an existing DB

        :type project_name: str
        :param project_name: the name of an existing project

        :type repo_name: str
        :param repo_name: the name of the repository to insert
        """
        self._cnx = self._db_util.get_connection(self._config)
        self.set_database(db_name)
        project_id = self._db_util.select_project_id(self._cnx, project_name, self._logger)
        self._db_util.insert_repo(self._cnx, project_id, repo_name, self._logger)
        self._db_util.close_connection(self._cnx)

    def list_projects(self, db_name):
        """
        lists all projects contained in the DB

        :type db_name: str
        :param db_name: the name of the DB
        """
        self._cnx = self._db_util.get_connection(self._config)
        project_names = []
        self.set_database(db_name)
        cursor = self._cnx.cursor()
        query = "SELECT name FROM project"
        cursor.execute(query)

        row = cursor.fetchone()

        while row:
            project_names.append(row[0])
            row = cursor.fetchone()

        cursor.close()
        self._db_util.close_connection(self._cnx)
        return project_names

    def set_database(self, db_name):
        """
        sets the DB used by the tool

        :type db_name: str
        :param db_name: the name of the DB
        """
        try:
            if not self._logger:
                log_path = self._log_root_path + "set-db-" + db_name
                self._logger = self._logging_util.get_logger(log_path)
                self._fileHandler = self._logging_util.get_file_handler(self._logger, log_path, "info")

            self._logger.info("set database " + db_name + " started")
            self._db_util.set_database(self._cnx, db_name)
            self._logger.info("set database " + db_name + " finished")
        except Exception:
            self._logger.error("set database failed", exc_info=True)

    def _set_settings(self):
        #sets the settings (max connections, charset, file format, ...) used by the DB
        self._db_util.set_settings(self._cnx)

    def _create_database(self, db_name):
        #creates the database
        cursor = self._cnx.cursor()

        drop_database_if_exists = "DROP DATABASE IF EXISTS " + db_name
        cursor.execute(drop_database_if_exists)

        create_database = "CREATE DATABASE " + db_name
        cursor.execute(create_database)

        cursor.close()

    def _init_functions(self):
        #initializes functions
        cursor = self._cnx.cursor()

        get_file_history = """
        CREATE DEFINER=`root`@`localhost` FUNCTION `get_file_history`(_file_id INT) RETURNS text CHARSET utf8
        BEGIN
        DECLARE _file_ids TEXT DEFAULT _file_id;
        DECLARE _prev INT;
        DECLARE _aux INT;

        SELECT previous_file_id INTO _prev
        FROM file_renamed
        WHERE current_file_id = _file_id;

        /* execute the loop until a previous version is found */
        myloop: WHILE _prev IS NOT NULL DO
                    /* add the previous version file id to the _file_ids variable */
                    SET _file_ids = CONCAT(_file_ids, ',' , _prev);

                    SET _aux = _prev;
                    SET _prev = NULL;

                    SELECT previous_file_id INTO _prev
                    FROM file_renamed
                    WHERE current_file_id = _aux;

                    IF _file_ids REGEXP CONCAT('^', _prev, ',|,', _prev, '$|,', _prev, ',') = 1  THEN
                        LEAVE myloop;
                    END IF;
        END WHILE;
        RETURN _file_ids;
        END"""

        levenshtein_distance = """
        CREATE DEFINER=`root`@`localhost` FUNCTION `levenshtein_distance`(s1 VARCHAR(255) CHARACTER SET utf8, s2 VARCHAR(255) CHARACTER SET utf8) RETURNS int(11)
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
        CREATE DEFINER=`root`@`localhost` FUNCTION `soundex_match`(s1 VARCHAR(255) CHARACTER SET utf8, s2 VARCHAR(255) CHARACTER SET utf8) RETURNS int(1)
            DETERMINISTIC
        BEGIN
            DECLARE _result INT DEFAULT 0;
            IF SOUNDEX(s1) = SOUNDEX(s2) THEN
                SET _result = 1;
            END IF;
            RETURN _result;
        END"""

        extract_issue_id = """
        CREATE DEFINER=`root`@`localhost` FUNCTION `extract_issue_id`(message VARCHAR(512)) RETURNS char(20) CHARSET utf8
        BEGIN
            DECLARE i, len SMALLINT DEFAULT 1;
            DECLARE digested VARCHAR(512) DEFAULT '';
            DECLARE c CHAR(1);
            DECLARE first_occ INT(2);
            DECLARE flag INT DEFAULT 0;
            DECLARE ret_string CHAR(20) DEFAULT '';

            SET digested = REPLACE(LOWER(message), ' ', '_');
            SET first_occ = LOCATE('bug', digested);
            SET digested = SUBSTRING(digested, first_occ, first_occ + 200);
            SET len = CHAR_LENGTH(digested);

            myloop: WHILE i <= len DO
                        SET c = MID(digested, i, 1);
                        IF c REGEXP '[0-9]' = 1 THEN
                           SET ret_string = CONCAT(ret_string, c);

                            IF flag = 0 THEN
                                SET flag = 1;
                            END IF;
                        ELSE
                            IF flag = 1 THEN
                                LEAVE myloop;
                            END IF;
                        END IF;

                        SET i = i + 1;
                    END WHILE;

            IF CHAR_LENGTH(ret_string) < 5 THEN
                SET ret_string = NULL;
            END IF;

            RETURN ret_string;
        END
        """

        cursor.execute(get_file_history)
        cursor.execute(levenshtein_distance)
        cursor.execute(soundex_match)
        cursor.execute(extract_issue_id)
        cursor.close()

    def _init_stored_procedures(self):
        #initializes stored procedures
        cursor = self._cnx.cursor()

        get_file_version = """
        CREATE DEFINER=`root`@`localhost` PROCEDURE `get_file_version`(IN _file_id INTEGER, _date TEXT, by_line BOOL)
        BEGIN
            DECLARE invar INTEGER;
            DECLARE _file_ids TEXT;

            /* retrieve the previous version of the file */
            SET @invar = _file_id;
            PREPARE stmt FROM 'SELECT get_file_history(id) INTO @_file_ids FROM file WHERE id = ?';
            EXECUTE stmt using @invar;

            /* returns either the content per line or the compacted version */
            IF by_line THEN
                CALL get_file_version_by_line(@_file_ids, _date);
            ELSE
                CALL get_file_version_compact(@_file_ids, _date);
            END IF;
        END"""

        get_file_version_by_line = """
        CREATE DEFINER=`root`@`localhost` PROCEDURE `get_file_version_by_line`(IN _file_ids TEXT, IN _date TEXT)
        BEGIN
            DECLARE _query TEXT DEFAULT
                          CONCAT('SELECT SUBSTRING(add_cont, 2) as line_content
                                FROM (
                                SELECT ld.line_number, max(c.committed_date) AS last_committed_date
                                FROM file_modification fm
                                JOIN line_detail ld
                                ON fm.id = ld.file_modification_id
                                JOIN commit c
                                ON fm.commit_id = c.id
                                WHERE fm.file_id IN (', _file_ids, ') AND committed_date <= \\'', _date , '\\'
                                group by ld.line_number) as last_mod
                                left join
                                (
                                SELECT ld.line_number AS line, ld.content AS add_cont, c.committed_date as date
                                FROM file_modification fm
                                JOIN line_detail ld
                                ON fm.id = ld.file_modification_id
                                JOIN commit c
                                ON fm.commit_id = c.id
                                WHERE fm.file_id IN (', _file_ids, ') AND ld.type = "addition" AND committed_date <= \\'', _date, '\\'
                                ) AS _add
                                ON last_mod.line_number = _add.line AND last_mod.last_committed_date = _add.date
                                WHERE add_cont IS NOT NULL
                                ORDER BY last_mod.line_number;');
             DECLARE sql_query TEXT;
             SET @sql_query = _query;
             PREPARE stmt FROM @sql_query;
             EXECUTE stmt;
             DEALLOCATE PREPARE stmt;

        END"""

        get_file_version_compact = """
        CREATE DEFINER=`root`@`localhost` PROCEDURE `get_file_version_compact`(IN _file_ids TEXT, IN _date TEXT)
        BEGIN
            DECLARE _query TEXT DEFAULT
                          CONCAT('CREATE TEMPORARY TABLE _tmp AS
                                SELECT SUBSTRING(add_cont, 2) as line_content
                                FROM (
                                SELECT ld.line_number, max(c.committed_date) AS last_committed_date
                                FROM file_modification fm
                                JOIN line_detail ld
                                ON fm.id = ld.file_modification_id
                                JOIN commit c
                                ON fm.commit_id = c.id
                                WHERE fm.file_id IN (', _file_ids, ') AND committed_date <= \\'', _date , '\\'
                                group by ld.line_number) as last_mod
                                left join
                                (
                                SELECT ld.line_number AS line, ld.content AS add_cont, c.committed_date as date
                                FROM file_modification fm
                                JOIN line_detail ld
                                ON fm.id = ld.file_modification_id
                                JOIN commit c
                                ON fm.commit_id = c.id
                                WHERE fm.file_id IN (', _file_ids, ') AND ld.type = "addition" AND committed_date <= \\'', _date, '\\'
                                ) AS _add
                                ON last_mod.line_number = _add.line AND last_mod.last_committed_date = _add.date
                                WHERE add_cont IS NOT NULL
                                ORDER BY last_mod.line_number;');
            DECLARE sql_query TEXT;
            DECLARE content LONGBLOB;
            DECLARE _txt BLOB;
            DECLARE done INT DEFAULT FALSE;
            DECLARE cur CURSOR FOR SELECT * FROM _tmp;
            DECLARE CONTINUE HANDLER FOR NOT FOUND SET done = 1;

            /* drop _tmp table if exists */
            DROP TABLE IF EXISTS _tmp;

            /* create _tmp table */
            SET @sql_query = _query;
            PREPARE stmt FROM @sql_query;
            EXECUTE stmt;
            DEALLOCATE PREPARE stmt;

            /* iterate over the lines and fill the variable content */
            OPEN cur;
            FETCH cur INTO _txt;

            SET content = _txt;

            read_loop: LOOP
                FETCH cur into _txt;
                IF done THEN
                    LEAVE read_loop;
                END IF;
                /* concat the line content to the variable content */
                SET content = CONCAT(content, '\\n', COALESCE(_txt, ''));
            END LOOP;

            CLOSE cur;

            /* drop _tmp table if exists */
            DROP TABLE IF EXISTS _tmp;
            /* return the conent variable */
            SELECT content;

        END
        """

        cursor.execute(get_file_version)
        cursor.execute(get_file_version_by_line)
        cursor.execute(get_file_version_compact)

        cursor.close()

    def _init_shared_tables(self):
        #initializes shared tables used by tables modeling git, issue tracker, forum and instant messaging data
        cursor = self._cnx.cursor()

        create_table_project = "CREATE TABLE project( " \
                               "id int(20) AUTO_INCREMENT PRIMARY KEY, " \
                               "name varchar(255), " \
                               "CONSTRAINT name UNIQUE (name)" \
                               ") ENGINE=InnoDB DEFAULT CHARSET=utf8 ROW_FORMAT=DYNAMIC;"

        create_table_user = "CREATE TABLE user ( " \
                            "id int(20) AUTO_INCREMENT PRIMARY KEY, " \
                            "name varchar(256), " \
                            "email varchar(256), " \
                            "CONSTRAINT namem UNIQUE (name, email) " \
                            ") ENGINE=InnoDB DEFAULT CHARSET=utf8 ROW_FORMAT=DYNAMIC;"

        create_table_user_alias = "CREATE TABLE user_alias ( " \
                                  "user_id int(20), " \
                                  "alias_id int(20), " \
                                  "CONSTRAINT a UNIQUE (alias_id) " \
                                  ") ENGINE=InnoDB DEFAULT CHARSET=utf8 ROW_FORMAT=DYNAMIC;"

        create_table_label = "CREATE TABLE label ( " \
                             "id int(20) AUTO_INCREMENT PRIMARY KEY, " \
                             "name varchar(256), " \
                             "CONSTRAINT name UNIQUE (name) " \
                             ") ENGINE=InnoDB DEFAULT CHARSET=utf8 ROW_FORMAT=DYNAMIC;"

        create_table_message = "CREATE TABLE message ( " \
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
                               "created_at timestamp DEFAULT '0000-00-00 00:00:00'," \
                               "CONSTRAINT ip UNIQUE (issue_id, topic_id, channel_id, own_id) " \
                               ") ENGINE=InnoDB DEFAULT CHARSET=utf8 ROW_FORMAT=DYNAMIC;"

        create_table_message_dependency = "CREATE TABLE message_dependency ( " \
                                          "source_message_id int(20), " \
                                          "target_message_id int(20), " \
                                          "PRIMARY KEY st (source_message_id, target_message_id) " \
                                          ") ENGINE=InnoDB DEFAULT CHARSET=utf8 ROW_FORMAT=DYNAMIC;"

        create_table_message_type = "CREATE TABLE message_type ( " \
                                    "id int(20) AUTO_INCREMENT PRIMARY KEY, " \
                                    "name varchar(255), " \
                                    "CONSTRAINT name UNIQUE (name) " \
                                    ") ENGINE=InnoDB DEFAULT CHARSET=utf8 ROW_FORMAT=DYNAMIC;"

        insert_message_types = "INSERT INTO message_type VALUES (NULL, 'question'), " \
                                                               "(NULL, 'answer'), " \
                                                               "(NULL, 'comment'), " \
                                                               "(NULL, 'accepted_answer'), " \
                                                               "(NULL, 'reply'), " \
                                                               "(NULL, 'file_upload'), " \
                                                               "(NULL, 'info');"

        create_table_attachment = "CREATE TABLE attachment ( " \
                                  "id int(20) AUTO_INCREMENT PRIMARY KEY, " \
                                  "own_id varchar(20), " \
                                  "message_id int(20), " \
                                  "name varchar(256), " \
                                  "extension varchar(10), " \
                                  "bytes int(20), " \
                                  "url varchar(512), " \
                                  "CONSTRAINT ip UNIQUE (message_id, own_id) " \
                                  ") ENGINE=InnoDB DEFAULT CHARSET=utf8 ROW_FORMAT=DYNAMIC;"

        cursor.execute(create_table_project)
        cursor.execute(create_table_user)
        cursor.execute(create_table_user_alias)
        cursor.execute(create_table_label)
        cursor.execute(create_table_message)
        cursor.execute(create_table_message_dependency)
        cursor.execute(create_table_message_type)
        cursor.execute(insert_message_types)
        cursor.execute(create_table_attachment)

        cursor.close()

    def _init_git_tables(self):
        #initializes tables used to model git data
        cursor = self._cnx.cursor()

        create_table_repository = "CREATE TABLE repository( " \
                                  "id int(20) AUTO_INCREMENT PRIMARY KEY, " \
                                  "project_id int(20), " \
                                  "name varchar(255), " \
                                  "CONSTRAINT name UNIQUE (name)" \
                                  ") ENGINE=InnoDB DEFAULT CHARSET=utf8 ROW_FORMAT=DYNAMIC;"

        create_table_reference = "CREATE TABLE reference( " \
                                 "id int(20) AUTO_INCREMENT PRIMARY KEY, " \
                                 "repo_id int(20), " \
                                 "name varchar(255), " \
                                 "type varchar(255), " \
                                 "CONSTRAINT name UNIQUE (repo_id, name, type) " \
                                 ") ENGINE=InnoDB DEFAULT CHARSET=utf8 ROW_FORMAT=DYNAMIC;"

        create_table_commit = "CREATE TABLE commit(" \
                              "id int(20) AUTO_INCREMENT PRIMARY KEY, " \
                              "repo_id int(20), " \
                              "sha varchar(512), " \
                              "message varchar(512), " \
                              "author_id int(20), " \
                              "committer_id int(20), " \
                              "authored_date timestamp DEFAULT '0000-00-00 00:00:00', " \
                              "committed_date timestamp DEFAULT '0000-00-00 00:00:00', " \
                              "size int(20), " \
                              "INDEX sha (sha), " \
                              "INDEX auth (author_id), " \
                              "INDEX comm (committer_id), " \
                              "CONSTRAINT s UNIQUE (sha, repo_id) " \
                              ") ENGINE=InnoDB DEFAULT CHARSET=utf8 ROW_FORMAT=DYNAMIC;"

        create_table_commit_parent = "CREATE TABLE commit_parent(" \
                                     "repo_id int(20), " \
                                     "commit_id int(20), " \
                                     "commit_sha varchar(512), " \
                                     "parent_id int(20), " \
                                     "parent_sha varchar(512), " \
                                     "PRIMARY KEY copa (repo_id, commit_id, parent_id), " \
                                     "CONSTRAINT cshapsha UNIQUE (repo_id, commit_id, parent_sha) " \
                                     ") ENGINE=InnoDB DEFAULT CHARSET=utf8 ROW_FORMAT=DYNAMIC;"

        create_table_commits2reference = "CREATE TABLE commit_in_reference(" \
                                         "repo_id int(20), " \
                                         "commit_id int(20), " \
                                         "ref_id int(20), " \
                                         "PRIMARY KEY core (commit_id, ref_id) " \
                                         ") ENGINE=InnoDB DEFAULT CHARSET=utf8 ROW_FORMAT=DYNAMIC;"

        create_table_file = "CREATE TABLE file( " \
                            "id int(20) AUTO_INCREMENT PRIMARY KEY, " \
                            "repo_id int(20), " \
                            "name varchar(512), " \
                            "ext varchar(255), " \
                            "CONSTRAINT rerena UNIQUE (repo_id, name) " \
                            ") ENGINE=InnoDB DEFAULT CHARSET=utf8 ROW_FORMAT=DYNAMIC;"

        create_table_file_renamed = "CREATE TABLE file_renamed ( " \
                                    "repo_id int(20), " \
                                    "current_file_id int(20), " \
                                    "previous_file_id int(20), " \
                                    "PRIMARY KEY cpc (current_file_id, previous_file_id) " \
                                    ") ENGINE=InnoDB DEFAULT CHARSET=utf8 ROW_FORMAT=DYNAMIC;"

        create_table_file_modification = "CREATE TABLE file_modification ( " \
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

        create_table_line_detail = "CREATE TABLE line_detail( " \
                                   "file_modification_id int(20)," \
                                   "type varchar(25), " \
                                   "line_number numeric(20), " \
                                   "is_commented numeric(1), " \
                                   "is_partially_commented numeric(1), " \
                                   "is_empty numeric(1), " \
                                   "content longblob, " \
                                   "PRIMARY KEY fityli (file_modification_id, type, line_number) " \
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
        cursor.close()

    def _init_issue_tracker_tables(self):
        #initializes tables used to model issue tracker data
        cursor = self._cnx.cursor()

        create_table_issue_tracker = "CREATE TABLE issue_tracker ( " \
                                     "id int(20) AUTO_INCREMENT PRIMARY KEY, " \
                                     "repo_id int(20), " \
                                     "name varchar(512), " \
                                     "type varchar(512), " \
                                     "CONSTRAINT name UNIQUE (name)" \
                                     ") ENGINE=InnoDB DEFAULT CHARSET=utf8 ROW_FORMAT=DYNAMIC;"

        create_table_issue = "CREATE TABLE issue ( " \
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
                             "created_at timestamp DEFAULT '0000-00-00 00:00:00', " \
                             "last_change_at timestamp DEFAULT '0000-00-00 00:00:00', " \
                             "CONSTRAINT ioi UNIQUE (issue_tracker_id, own_id), " \
                             "INDEX u (reporter_id), " \
                             "INDEX r (reference_id) " \
                             ") ENGINE=InnoDB DEFAULT CHARSET=utf8 ROW_FORMAT=DYNAMIC;"

        create_table_issue_assignee = "CREATE TABLE issue_assignee ( " \
                                      "issue_id int(20), " \
                                      "assignee_id int(20), " \
                                      "PRIMARY KEY il (issue_id, assignee_id) " \
                                      ") ENGINE=InnoDB DEFAULT CHARSET=utf8 ROW_FORMAT=DYNAMIC;"

        create_table_issue_subscriber = "CREATE TABLE issue_subscriber ( " \
                                        "issue_id int(20), " \
                                        "subscriber_id int(20), " \
                                        "PRIMARY KEY il (issue_id, subscriber_id) " \
                                        ") ENGINE=InnoDB DEFAULT CHARSET=utf8 ROW_FORMAT=DYNAMIC;"

        create_table_issue_event = "CREATE TABLE issue_event ( " \
                                   "id int(20) AUTO_INCREMENT PRIMARY KEY, " \
                                   "issue_id int(20), " \
                                   "event_type_id int(20), " \
                                   "detail varchar(256), " \
                                   "creator_id int(20), " \
                                   "created_at timestamp DEFAULT '0000-00-00 00:00:00', " \
                                   "target_user_id int(20), " \
                                   "CONSTRAINT iecc UNIQUE (issue_id, event_type_id, creator_id, created_at, detail) " \
                                   ") ENGINE=InnoDB DEFAULT CHARSET=utf8 ROW_FORMAT=DYNAMIC;"

        create_table_issue_event_type = "CREATE TABLE issue_event_type ( " \
                                        "id int(20) AUTO_INCREMENT PRIMARY KEY, " \
                                        "name varchar(256), " \
                                        "CONSTRAINT name UNIQUE (name) " \
                                        ") ENGINE=InnoDB DEFAULT CHARSET=utf8 ROW_FORMAT=DYNAMIC;"

        create_table_issue_labelled = "CREATE TABLE issue_labelled ( " \
                                      "issue_id int(20), " \
                                      "label_id int(20), " \
                                      "PRIMARY KEY il (issue_id, label_id) " \
                                      ") ENGINE=InnoDB DEFAULT CHARSET=utf8 ROW_FORMAT=DYNAMIC;"

        create_issue_commit_dependency = "CREATE TABLE issue_commit_dependency ( " \
                                         "issue_id int(20), " \
                                         "commit_id int(20), " \
                                         "PRIMARY KEY ict (issue_id, commit_id) " \
                                         ") ENGINE=InnoDB DEFAULT CHARSET=utf8 ROW_FORMAT=DYNAMIC;"

        create_table_issue_dependency = "CREATE TABLE issue_dependency ( " \
                                        "issue_source_id int(20), " \
                                        "issue_target_id int(20), " \
                                        "type_id int(20), " \
                                        "PRIMARY KEY st (issue_source_id, issue_target_id, type_id) " \
                                        ") ENGINE=InnoDB DEFAULT CHARSET=utf8 ROW_FORMAT=DYNAMIC;"

        create_issue_dependency_type = "CREATE TABLE issue_dependency_type (" \
                                       "id int(20) AUTO_INCREMENT PRIMARY KEY, " \
                                       "name varchar(256), " \
                                       "CONSTRAINT name UNIQUE (name) " \
                                       ") ENGINE=InnoDB DEFAULT CHARSET=utf8 ROW_FORMAT=DYNAMIC;"

        insert_issue_dependency_type = "INSERT INTO issue_dependency_type VALUES (NULL, 'block'), " \
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
        #initializes tables used to model forum data
        cursor = self._cnx.cursor()

        create_table_forum = "CREATE TABLE forum ( " \
                             "id int(20) AUTO_INCREMENT PRIMARY KEY, " \
                             "project_id int(20), " \
                             "name varchar(512), " \
                             "type varchar(512), " \
                             "CONSTRAINT name UNIQUE (name)" \
                             ") ENGINE=InnoDB DEFAULT CHARSET=utf8 ROW_FORMAT=DYNAMIC;"

        create_table_topic = "CREATE TABLE topic ( " \
                             "id int(20) AUTO_INCREMENT PRIMARY KEY, " \
                             "own_id varchar(20), " \
                             "forum_id int(20), " \
                             "name varchar(256), " \
                             "votes int(10), " \
                             "views int(10), " \
                             "created_at timestamp DEFAULT '0000-00-00 00:00:00', " \
                             "last_change_at timestamp DEFAULT '0000-00-00 00:00:00', " \
                             "CONSTRAINT name UNIQUE (forum_id, own_id)" \
                             ") ENGINE=InnoDB DEFAULT CHARSET=utf8 ROW_FORMAT=DYNAMIC;"

        cursor.execute(create_table_forum)
        cursor.execute(create_table_topic)

        cursor.close()

    def _init_instant_messaging_tables(self):
        #initializes tables used to model instant messaging data
        cursor = self._cnx.cursor()

        create_table_instant_messaging = "CREATE TABLE instant_messaging ( " \
                                         "id int(20) AUTO_INCREMENT PRIMARY KEY, " \
                                         "project_id int(20), " \
                                         "name varchar(512), " \
                                         "type varchar(512), " \
                                         "CONSTRAINT name UNIQUE (name)" \
                                         ") ENGINE=InnoDB DEFAULT CHARSET=utf8 ROW_FORMAT=DYNAMIC;"

        create_table_channel = "CREATE TABLE channel ( " \
                               "id int(20) AUTO_INCREMENT PRIMARY KEY, " \
                               "own_id varchar(20), " \
                               "instant_messaging_id int(20), " \
                               "name varchar(256), " \
                               "description varchar(512), " \
                               "created_at timestamp DEFAULT '0000-00-00 00:00:00', " \
                               "last_change_at timestamp DEFAULT '0000-00-00 00:00:00', " \
                               "CONSTRAINT name UNIQUE (instant_messaging_id, own_id)" \
                               ") ENGINE=InnoDB DEFAULT CHARSET=utf8 ROW_FORMAT=DYNAMIC;"

        cursor.execute(create_table_instant_messaging)
        cursor.execute(create_table_channel)
        cursor.close()