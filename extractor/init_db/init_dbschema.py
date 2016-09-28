#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'valerio cosentino'

import sys
sys.path.insert(0, "..//..")

import mysql.connector
from mysql.connector import errorcode
from datetime import datetime
import config_db
import logging
import logging.handlers
import glob
import os

LOG_FOLDER = "logs"


class InitDbSchema():

    def __init__(self, db_name):
        self.db_name = config_db.DB_NAME
        self.create_log_folder(LOG_FOLDER)
        LOG_FILENAME = LOG_FOLDER + "/init_db_schema"
        self.delete_previous_logs(LOG_FOLDER)
        self.logger = logging.getLogger(LOG_FILENAME)
        fileHandler = logging.FileHandler(LOG_FILENAME + "-" + db_name + ".log", mode='w')
        formatter = logging.Formatter("%(asctime)s:%(levelname)s:%(message)s", "%Y-%m-%d %H:%M:%S")

        fileHandler.setFormatter(formatter)
        self.logger.setLevel(logging.INFO)
        self.logger.addHandler(fileHandler)

        self.cnx = mysql.connector.connect(**config_db.CONFIG)

    def create_log_folder(self, name):
        if not os.path.exists(name):
            os.makedirs(name)

    def delete_previous_logs(self, path):
        files = glob.glob(path + "/*")
        for f in files:
            try:
                os.remove(f)
            except:
                continue

    def init_database(self):
        self.create_database()
        self.set_database()
        self.set_settings()
        self.init_shared_tables()
        self.init_git_tables()
        self.init_issue_tracker_tables()
        self.init_forum_tables()
        self.init_instant_messaging_tables()
        self.init_functions()
        self.init_stored_procedures()

    # def reset_git_tables(self):
    #     self.set_database()
    #     self.set_settings()
    #     cursor = self.cnx.cursor()
    #
    #     delete_table_repositories = "DROP TABLE IF EXISTS repository;"
    #     delete_table_references = "DROP TABLE IF EXISTS reference;"
    #     delete_table_users = "DROP TABLE IF EXISTS user;"
    #     delete_table_commits = "DROP TABLE IF EXISTS commit;"
    #     delete_table_commit_parent = "DROP TABLE IF EXISTS commit_parent;"
    #     delete_table_commits2reference = "DROP TABLE IF EXISTS commit_in_reference;"
    #     delete_table_files = "DROP TABLE IF EXISTS file;"
    #     delete_table_file_renamed = "DROP TABLE IF EXISTS file_renamed;"
    #     delete_table_file_modifications = "DROP TABLE IF EXISTS file_modification;"
    #     delete_table_line_detail = "DROP TABLE IF EXISTS line_detail;"
    #
    #     cursor.execute(delete_table_repositories)
    #     cursor.execute(delete_table_references)
    #     cursor.execute(delete_table_users)
    #     cursor.execute(delete_table_commits)
    #     cursor.execute(delete_table_commit_parent)
    #     cursor.execute(delete_table_commits2reference)
    #     cursor.execute(delete_table_files)
    #     cursor.execute(delete_table_file_renamed)
    #     cursor.execute(delete_table_file_modifications)
    #     cursor.execute(delete_table_line_detail)
    #     cursor.close()
    #
    #     self.init_git_tables()
    #
    #     return
    #
    # def reset_issue_tracker_tables(self):
    #     self.set_database()
    #     self.set_settings()
    #     cursor = self.cnx.cursor()
    #
    #     delete_table_issue_tracker = "DROP TABLE IF EXISTS issue_tracker;"
    #     delete_table_issue = "DROP TABLE IF EXISTS issue;"
    #     delete_table_issue_assignee = "DROP TABLE IF EXISTS issue_assignee;"
    #     delete_table_issue_subscriber = "DROP TABLE IF EXISTS issue_subscriber;"
    #     delete_table_issue_event = "DROP TABLE IF EXISTS issue_event;"
    #     delete_table_issue_event_type = "DROP TABLE IF EXISTS issue_event_type;"
    #     delete_table_issue_labelled = "DROP TABLE IF EXISTS issue_labelled;"
    #     delete_table_issue_label = "DROP TABLE IF EXISTS label;"
    #     delete_table_issue_comment = "DROP TABLE IF EXISTS message;"
    #     delete_table_issue_comment_attachment = "DROP TABLE IF EXISTS attachment;"
    #     delete_issue_commit_dependency = "DROP TABLE IF EXISTS issue_commit_dependency;"
    #     delete_table_issue_dependency = "DROP TABLE IF EXISTS issue_dependency;"
    #
    #     cursor.execute(delete_table_issue_tracker)
    #     cursor.execute(delete_table_issue)
    #     cursor.execute(delete_table_issue_assignee)
    #     cursor.execute(delete_table_issue_subscriber)
    #     cursor.execute(delete_table_issue_event)
    #     cursor.execute(delete_table_issue_event_type)
    #     cursor.execute(delete_table_issue_labelled)
    #     cursor.execute(delete_table_issue_label)
    #     cursor.execute(delete_table_issue_comment)
    #     cursor.execute(delete_table_issue_comment_attachment)
    #     cursor.execute(delete_issue_commit_dependency)
    #     cursor.execute(delete_table_issue_dependency)
    #     cursor.close()
    #
    #     self.init_issue_tracker_tables()
    #
    #     return

    def set_database(self):
        cursor = self.cnx.cursor()
        use_database = "USE " + self.db_name
        cursor.execute(use_database)
        cursor.close()

    def set_settings(self):
        cursor = self.cnx.cursor()
        cursor.execute("set global innodb_file_format = BARRACUDA")
        cursor.execute("set global innodb_file_format_max = BARRACUDA")
        cursor.execute("set global innodb_large_prefix = ON")
        cursor.execute("set global character_set_server = utf8")
        cursor.close()

    def create_database(self):
        cursor = self.cnx.cursor()

        drop_database_if_exists = "DROP DATABASE IF EXISTS " + self.db_name
        cursor.execute(drop_database_if_exists)

        create_database = "CREATE DATABASE " + self.db_name
        cursor.execute(create_database)

        cursor.close()

    def init_functions(self):
        cursor = self.cnx.cursor()

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

    def init_stored_procedures(self):
        cursor = self.cnx.cursor()

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

    def init_shared_tables(self):
        cursor = self.cnx.cursor()

        create_table_project = "CREATE TABLE project( " \
                               "id int(20) AUTO_INCREMENT PRIMARY KEY, " \
                               "name varchar(255), " \
                               "INDEX n (name), " \
                               "CONSTRAINT name UNIQUE (name)" \
                               ") ENGINE=InnoDB DEFAULT CHARSET=utf8 ROW_FORMAT=DYNAMIC;"

        create_table_user = "CREATE TABLE user ( " \
                            "id int(20) AUTO_INCREMENT PRIMARY KEY, " \
                            "name varchar(256), " \
                            "email varchar(256), " \
                            "CONSTRAINT namem UNIQUE (name, email), " \
                            "INDEX ne (name, email) " \
                            ") ENGINE=InnoDB DEFAULT CHARSET=utf8 ROW_FORMAT=DYNAMIC;"

        create_table_label = "CREATE TABLE label ( " \
                             "id int(20) AUTO_INCREMENT PRIMARY KEY, " \
                             "name varchar(256), " \
                             "CONSTRAINT name UNIQUE (name), " \
                             "INDEX n (name) " \
                             ") ENGINE=InnoDB DEFAULT CHARSET=utf8 ROW_FORMAT=DYNAMIC;"

        create_table_message = "CREATE TABLE message ( " \
                               "id int(20) AUTO_INCREMENT PRIMARY KEY, " \
                               "own_id int(20), " \
                               "pos int(10), " \
                               "type int(20), " \
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
                                          "id int(20) AUTO_INCREMENT PRIMARY KEY, " \
                                          "source_message_id int(20), " \
                                          "target_message_id int(20), " \
                                          "CONSTRAINT ip UNIQUE (source_message_id, target_message_id) " \
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
                                                               "(NULL, 'file_upload');"

        create_table_attachment = "CREATE TABLE attachment ( " \
                                  "id int(20) PRIMARY KEY, " \
                                  "own_id int(20), " \
                                  "message_id int(20), " \
                                  "name varchar(256), " \
                                  "extension varchar(10), " \
                                  "bytes int(20), " \
                                  "url varchar(512), " \
                                  "CONSTRAINT ip UNIQUE (message_id, own_id) " \
                                  ") ENGINE=InnoDB DEFAULT CHARSET=utf8 ROW_FORMAT=DYNAMIC;"

        cursor.execute(create_table_project)
        cursor.execute(create_table_user)
        cursor.execute(create_table_label)
        cursor.execute(create_table_message)
        cursor.execute(create_table_message_dependency)
        cursor.execute(create_table_message_type)
        cursor.execute(insert_message_types)
        cursor.execute(create_table_attachment)

        cursor.close()

    def init_git_tables(self):
        cursor = self.cnx.cursor()

        create_table_repository = "CREATE TABLE repository( " \
                                  "id int(20) AUTO_INCREMENT PRIMARY KEY, " \
                                  "project_id int(20), " \
                                  "name varchar(255), " \
                                  "INDEX n (name), " \
                                  "CONSTRAINT name UNIQUE (project_id, name)" \
                                  ") ENGINE=InnoDB DEFAULT CHARSET=utf8 ROW_FORMAT=DYNAMIC;"

        create_table_reference = "CREATE TABLE reference( " \
                                 "id int(20) AUTO_INCREMENT PRIMARY KEY, " \
                                 "repo_id int(20), " \
                                 "name varchar(255), " \
                                 "type varchar(255), " \
                                 "INDEX n (name), " \
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
                              "CONSTRAINT s UNIQUE (sha) " \
                              ") ENGINE=InnoDB DEFAULT CHARSET=utf8 ROW_FORMAT=DYNAMIC;"

        create_table_commit_parent = "CREATE TABLE commit_parent(" \
                                     "repo_id int(20), " \
                                     "commit_id int(20), " \
                                     "commit_sha varchar(512), " \
                                     "parent_id int(20), " \
                                     "parent_sha varchar(512), " \
                                     "PRIMARY KEY copa (repo_id, commit_id, parent_id), " \
                                     "INDEX csha (commit_sha), " \
                                     "INDEX psha (parent_sha), " \
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
                            "INDEX rrn (repo_id, name), " \
                            "CONSTRAINT rerena UNIQUE (repo_id, name) " \
                            ") ENGINE=InnoDB DEFAULT CHARSET=utf8 ROW_FORMAT=DYNAMIC;"

        create_table_file_renamed = "CREATE TABLE file_renamed ( " \
                                    "repo_id int(20), " \
                                    "current_file_id int(20), " \
                                    "previous_file_id int(20), " \
                                    "PRIMARY KEY cpc (current_file_id, previous_file_id), " \
                                    "INDEX current (current_file_id), " \
                                    "INDEX previous (previous_file_id) " \
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
                                         "CONSTRAINT cf UNIQUE (commit_id, file_id), " \
                                         "INDEX c (commit_id), " \
                                         "INDEX f (file_id) " \
                                         ") ENGINE=InnoDB DEFAULT CHARSET=utf8 ROW_FORMAT=DYNAMIC;"

        create_table_line_detail = "CREATE TABLE line_detail( " \
                                   "file_modification_id int(20)," \
                                   "type varchar(25), " \
                                   "line_number numeric(20), " \
                                   "is_commented numeric(1), " \
                                   "is_partially_commented numeric(1), " \
                                   "is_empty numeric(1), " \
                                   "content longblob, " \
                                   "PRIMARY KEY fityli (file_modification_id, type, line_number), " \
                                   "INDEX fi (file_modification_id) " \
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
        return

    def init_issue_tracker_tables(self):
        cursor = self.cnx.cursor()

        create_table_issue_tracker = "CREATE TABLE issue_tracker ( " \
                                     "id int(20) AUTO_INCREMENT PRIMARY KEY, " \
                                     "repo_id int(20), " \
                                     "url varchar(512), " \
                                     "type varchar(512), " \
                                     "CONSTRAINT name UNIQUE (repo_id, url)" \
                                     ") ENGINE=InnoDB DEFAULT CHARSET=utf8 ROW_FORMAT=DYNAMIC;"

        create_table_issue = "CREATE TABLE issue ( " \
                             "id int(20) AUTO_INCREMENT PRIMARY KEY, " \
                             "own_id int(20), " \
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
                                        "CONSTRAINT name UNIQUE (name), " \
                                        "INDEX n (name) " \
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
                                        "type varchar(256), " \
                                        "PRIMARY KEY st (issue_source_id, issue_target_id) " \
                                        ") ENGINE=InnoDB DEFAULT CHARSET=utf8 ROW_FORMAT=DYNAMIC;"

        cursor.execute(create_table_issue_tracker)
        cursor.execute(create_table_issue)
        cursor.execute(create_table_issue_assignee)
        cursor.execute(create_table_issue_subscriber)
        cursor.execute(create_table_issue_event)
        cursor.execute(create_table_issue_event_type)
        cursor.execute(create_table_issue_labelled)
        cursor.execute(create_issue_commit_dependency)
        cursor.execute(create_table_issue_dependency)
        cursor.close()
        return

    def init_forum_tables(self):
        cursor = self.cnx.cursor()

        create_table_forum = "CREATE TABLE forum ( " \
                             "id int(20) AUTO_INCREMENT PRIMARY KEY, " \
                             "project_id int(20), " \
                             "url varchar(512), " \
                             "type varchar(512), " \
                             "CONSTRAINT name UNIQUE (project_id, url)" \
                             ") ENGINE=InnoDB DEFAULT CHARSET=utf8 ROW_FORMAT=DYNAMIC;"

        create_table_topic = "CREATE TABLE topic ( " \
                             "id int(20) PRIMARY KEY, " \
                             "own_id int(20), " \
                             "forum_id int(20), " \
                             "name varchar(256), " \
                             "votes int(10), " \
                             "views int(10), " \
                             "created_at timestamp DEFAULT '0000-00-00 00:00:00', " \
                             "last_changed_at timestamp DEFAULT '0000-00-00 00:00:00', " \
                             "CONSTRAINT name UNIQUE (forum_id, own_id)" \
                             ") ENGINE=InnoDB DEFAULT CHARSET=utf8 ROW_FORMAT=DYNAMIC;"

        cursor.execute(create_table_forum)
        cursor.execute(create_table_topic)

        cursor.close()

    def init_instant_messaging_tables(self):
        cursor = self.cnx.cursor()

        create_table_instant_messaging = "CREATE TABLE instant_messaging ( " \
                                         "id int(20) AUTO_INCREMENT PRIMARY KEY, " \
                                         "project_id int(20), " \
                                         "url varchar(512), " \
                                         "type varchar(512), " \
                                         "CONSTRAINT name UNIQUE (project_id, url)" \
                                         ") ENGINE=InnoDB DEFAULT CHARSET=utf8 ROW_FORMAT=DYNAMIC;"

        create_table_channel = "CREATE TABLE channel ( " \
                               "id int(20) PRIMARY KEY, " \
                               "own_id int(20), " \
                               "instant_messaging_id int(20), " \
                               "name varchar(256), " \
                               "description varchar(512), " \
                               "created_at timestamp DEFAULT '0000-00-00 00:00:00', " \
                               "CONSTRAINT name UNIQUE (instant_messaging_id, own_id)" \
                               ") ENGINE=InnoDB DEFAULT CHARSET=utf8 ROW_FORMAT=DYNAMIC;"

        cursor.execute(create_table_instant_messaging)
        cursor.execute(create_table_channel)
        cursor.close()
        return

    def execute(self):

        start_time = datetime.now()
        self.init_database()
        self.cnx.close()
        end_time = datetime.now()

        minutes_and_seconds = divmod((end_time-start_time).total_seconds(), 60)
        self.logger.info("InitDbSchema: process finished after " + str(minutes_and_seconds[0])
                         + " minutes and " + str(round(minutes_and_seconds[1], 1)) + " secs")
        return


def main():
    a = InitDbSchema(config_db.DB_NAME)
    a.execute()

if __name__ == "__main__":
    main()