#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'valerio cosentino'

import sys
sys.path.insert(0, "..//..")


class DbSchema():

    def __init__(self, cnx, logger):
        self.logger = logger
        self.cnx = cnx

    def init_database(self, db_name):
        try:
            self.create_database(db_name)
            self.set_database(db_name)
            self.set_settings()
            self.init_shared_tables()
            self.init_git_tables()
            self.init_issue_tracker_tables()
            self.init_forum_tables()
            self.init_instant_messaging_tables()
            self.init_functions()
            self.init_stored_procedures()
            self.logger.info("database " + db_name + " created")
        except Exception:
            self.logger.error("Dbschema failed", exc_info=True)

    def create_project(self, db_name, project_name):
        self.set_database(db_name)
        cursor = self.cnx.cursor()
        query = "INSERT IGNORE INTO project " \
                "VALUES (%s, %s)"
        arguments = [None, project_name]
        cursor.execute(query, arguments)
        self.cnx.commit()

        cursor.close()

    def get_project_id(self, project_name, db_name):
        found = None
        self.set_database(db_name)
        cursor = self.cnx.cursor()
        query = "SELECT id FROM project WHERE name = %s"
        arguments = [project_name]
        cursor.execute(query, arguments)

        row = cursor.fetchone()
        cursor.close()

        if row:
            found = row[0]

        return found

    def list_projects(self, db_name):
        project_names = []
        self.set_database(db_name)
        cursor = self.cnx.cursor()
        query = "SELECT name FROM project"
        cursor.execute(query)

        row = cursor.fetchone()

        while row:
            project_names.append(row[0])
            row = cursor.fetchone()

        cursor.close()
        return project_names

    def set_database(self, db_name):
        try:
            cursor = self.cnx.cursor()
            use_database = "USE " + db_name
            cursor.execute(use_database)
            cursor.close()
        except Exception:
            self.logger.error("Dbschema failed", exc_info=True)

    def set_settings(self):
        cursor = self.cnx.cursor()
        cursor.execute("set global innodb_file_format = BARRACUDA")
        cursor.execute("set global innodb_file_format_max = BARRACUDA")
        cursor.execute("set global innodb_large_prefix = ON")
        cursor.execute("set global character_set_server = utf8")
        cursor.close()

    def create_database(self, db_name):
        cursor = self.cnx.cursor()

        drop_database_if_exists = "DROP DATABASE IF EXISTS " + db_name
        cursor.execute(drop_database_if_exists)

        create_database = "CREATE DATABASE " + db_name
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
                                  "id int(20) AUTO_INCREMENT PRIMARY KEY, " \
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
                             "id int(20) AUTO_INCREMENT PRIMARY KEY, " \
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
                               "id int(20) AUTO_INCREMENT PRIMARY KEY, " \
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