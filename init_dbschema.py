__author__ = 'atlanmod'

import mysql.connector
from mysql.connector import errorcode
from datetime import datetime


class InitDbSchema():



    def __init__(self, db_name, logger):
        self.logger = logger
        self.DB_NAME = db_name

        CONFIG = {
            'user': 'root',
            'password': 'root',
            'host': 'localhost',
            'port': '3306',
            'raise_on_warnings': False,
            'charset': 'utf8',
            'buffered': True
        }

        self.cnx = mysql.connector.connect(**CONFIG)

    def init_database(self):
        self.init_tables()
        self.init_views()
        self.init_functions()
        self.init_stored_procedures()

    def init_views(self):
        cursor = self.cnx.cursor()

        num_files_deleted = """
        CREATE VIEW num_files_deleted AS
        SELECT COUNT(DISTINCT fm.file_id) AS value FROM file_modification fm WHERE fm.status = "deleted";
        """

        num_files_present = """
        CREATE VIEW num_files_present AS
        SELECT (COUNT(*) - value) AS value
        FROM file f JOIN num_files_deleted nfd;
        """

        num_branches = """
        CREATE VIEW num_branches AS
        SELECT COUNT(*)  as value
        FROM reference r;
        """

        number_file_modification_per_commit = """
        CREATE VIEW number_file_modification_per_commit AS
        SELECT COUNT(DISTINCT fm.file_id) as value
        FROM file_modification fm
        GROUP BY fm.commit_id;
        """

        avg_number_file_modification_per_commit = """
        CREATE VIEW avg_number_file_modification_per_commit AS
        SELECT AVG(value) AS value
        FROM number_file_modification_per_commit;
        """

        num_empty_lines_deleted_files = """
        CREATE VIEW num_empty_lines_deleted_files AS
        SELECT COUNT(*) AS value
        FROM line_detail ld, file_modification fm
        WHERE ld.file_modification_id = fm.id AND fm.status = "deleted" AND ld.is_empty = 1;
        """

        num_empty_lines_present_files = """
        CREATE VIEW num_empty_lines_present_files AS
        SELECT (COUNT(*) - value) AS value
        FROM line_detail ld, file_modification fm
        JOIN num_empty_lines_deleted_files neldf
        WHERE ld.file_modification_id = fm.id AND ld.is_empty = 1;
        """

        num_commented_lines_deleted_files = """
        CREATE VIEW num_commented_lines_deleted_files AS
        SELECT COUNT(*) AS value
        FROM line_detail ld, file_modification fm
        WHERE ld.file_modification_id = fm.id AND fm.status = "deleted" AND (ld.is_commented = 1 OR ld.is_partially_commented = 1);
        """

        num_commented_lines_present_files = """
        CREATE VIEW num_commented_lines_present_files AS
        SELECT (COUNT(*) - value) as value
        FROM line_detail ld, file_modification fm
        JOIN num_commented_lines_deleted_files ncldf
        WHERE ld.file_modification_id = fm.id AND (ld.is_commented = 1 OR ld.is_partially_commented = 1);
        """

        num_lines_deleted_files = """
        CREATE VIEW num_lines_deleted_files AS
        SELECT COUNT(*) AS value
        FROM line_detail ld, file_modification fm
        WHERE ld.file_modification_id = fm.id AND fm.status = "deleted";
        """

        num_lines_present_files = """
        CREATE VIEW num_lines_present_files AS
        SELECT (COUNT(*) - value) as value
        FROM line_detail ld, file_modification fm
        JOIN num_lines_deleted_files nldf
        WHERE ld.file_modification_id = fm.id;
        """

        num_distinct_commits = """
        CREATE VIEW num_distinct_commits AS
        SELECT COUNT(*) as value FROM commit c;
        """

        num_commits_in_references = """
        CREATE VIEW num_commits_in_references AS
        SELECT COUNT(*) as value FROM commit_in_reference cin;
        """

        num_developers = """
        CREATE VIEW num_developers AS
        SELECT COUNT(*) as value FROM developer d;
        """

        repo_metrics = """
        CREATE VIEW repo_metrics AS
        SELECT
            a.value as num_files_deleted,
            b.value as num_files_present,
            c.value as num_branches,
            d.value as avg_number_file_modification_per_commit,
            e.value as num_empty_lines_deleted_files,
            f.value as num_empty_lines_present_files,
            g.value as num_commented_lines_deleted_files,
            h.value as num_commented_lines_present_files,
            i.value as num_lines_deleted_files,
            l.value as num_lines_present_files,
            m.value as num_distinct_commits,
            n.value as num_commits_in_references,
            o.value as num_developers
        FROM num_files_deleted a
        JOIN num_files_present b
        JOIN num_branches c
        JOIN avg_number_file_modification_per_commit d
        JOIN num_empty_lines_deleted_files e
        JOIN num_empty_lines_present_files f
        JOIN num_commented_lines_deleted_files g
        JOIN num_commented_lines_present_files h
        JOIN num_lines_deleted_files i
        JOIN num_lines_present_files l
        JOIN num_distinct_commits m
        JOIN num_commits_in_references n
        JOIN num_developers o;
        """

        developer_weekly_activity_metrics = """
        CREATE VIEW developer_activity_metrics AS
        SELECT
        YEAR(c.authored_date) as year,
        WEEK(c.authored_date) as week,
        d.name as author,
        SUM(fm.additions) as insertions,
        SUM(fm.deletions) as deletions
        FROM
        developer d,
        commit c,
        file_modification fm
        WHERE
        c.author_id = d.id AND c.id = fm.commit_id
        GROUP BY
        WEEK(c.authored_date), YEAR(c.authored_date), d.id;
        """

        totalChanges = """
        CREATE VIEW totalChanges AS
        SELECT COUNT(DISTINCT fm.id) AS value FROM file_modification fm;
        """

        num_commented_lines_per_author = """
        CREATE VIEW num_commented_lines_per_author AS
        SELECT c.author_id, COUNT(*) as value
        FROM line_detail ld, file_modification fm, commit c
        WHERE ld.file_modification_id = fm.id AND c.id = fm.commit_id AND type = 'addition' AND (ld.is_commented = 1 OR ld.is_partially_commented = 1)
        GROUP BY c.author_id;
        """

        num_total_commented_lines = """
        CREATE VIEW num_total_commented_lines AS
        SELECT COUNT(*) as value
        FROM line_detail ld, file_modification fm, commit c
        WHERE ld.file_modification_id = fm.id AND c.id = fm.commit_id AND type = 'addition' AND (ld.is_commented = 1 OR ld.is_partially_commented = 1);
        """

        developer_project_activity_metrics = """
        CREATE VIEW developer_project_activity_metrics AS
        SELECT
        d.name as author,
        COUNT(DISTINCT c.id) as commits,
        SUM(fm.additions) as insertions,
        SUM(fm.deletions) as deletions,
        ROUND((COUNT(DISTINCT fm.id)/total.value)*100, 2) as perc_changes,
        nclpa.value AS num_commented_lines_per_author,
        ROUND((nclpa.value/ntcl.value)*100, 2) AS perc_commented_lines
        FROM
        developer d,
        commit c,
        file_modification fm
        JOIN
        totalChanges as total
        JOIN
        num_commented_lines_per_author as nclpa
        JOIN
        num_total_commented_lines as ntcl
        WHERE
            c.author_id = d.id AND c.id = fm.commit_id AND nclpa.author_id = d.id
        GROUP BY
            d.id;
        """

        cursor.execute(num_files_deleted)
        cursor.execute(num_files_present)
        cursor.execute(num_branches)
        cursor.execute(number_file_modification_per_commit)
        cursor.execute(avg_number_file_modification_per_commit)
        cursor.execute(num_empty_lines_deleted_files)
        cursor.execute(num_empty_lines_present_files)
        cursor.execute(num_commented_lines_deleted_files)
        cursor.execute(num_commented_lines_present_files)
        cursor.execute(num_lines_deleted_files)
        cursor.execute(num_lines_present_files)
        cursor.execute(num_distinct_commits)
        cursor.execute(num_commits_in_references)
        cursor.execute(num_developers)
        cursor.execute(repo_metrics)

        cursor.execute(developer_weekly_activity_metrics)

        cursor.execute(totalChanges)
        cursor.execute(num_commented_lines_per_author)
        cursor.execute(num_total_commented_lines)
        cursor.execute(developer_project_activity_metrics)

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
        WHILE _prev IS NOT NULL DO
            /* add the previous version file id to the _file_ids variable */
            SET _file_ids = CONCAT(_file_ids, ',' , _prev);

            SET _aux = _prev;
            SET _prev = NULL;

            SELECT previous_file_id INTO _prev
            FROM file_renamed
            WHERE current_file_id = _aux;

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

        cursor.execute(get_file_history)
        cursor.execute(levenshtein_distance)
        cursor.execute(soundex_match)
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
                CALL get_file_history_by_line(@_file_ids, _date);
            ELSE
                CALL get_file_history_compact(@_file_ids, _date);
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

    def init_tables(self):
        cursor = self.cnx.cursor()

        drop_database_if_exists = "DROP DATABASE IF EXISTS " + self.DB_NAME
        cursor.execute(drop_database_if_exists)

        create_database = "CREATE DATABASE " + self.DB_NAME
        cursor.execute(create_database)

        cursor.execute("set global innodb_file_format = BARRACUDA")
        cursor.execute("set global innodb_file_format_max = BARRACUDA")
        cursor.execute("set global innodb_large_prefix = ON")
        cursor.execute("set global character_set_server = utf8")

        create_table_repositories = "CREATE TABLE " + self.DB_NAME + ".repository( " \
                                "id int(20) AUTO_INCREMENT PRIMARY KEY, " \
                                "name varchar(255), " \
                                "INDEX n (name), " \
                                "CONSTRAINT name UNIQUE (name)" \
                                ") ENGINE=InnoDB DEFAULT CHARSET=utf8 ROW_FORMAT=DYNAMIC;"

        create_table_references = "CREATE TABLE " + self.DB_NAME + ".reference( " \
                                  "id int(20) AUTO_INCREMENT PRIMARY KEY, " \
                                  "repo_id int(20), " \
                                  "name varchar(255), " \
                                  "type varchar(255), " \
                                  "INDEX n (name), " \
                                  "CONSTRAINT name UNIQUE (name) " \
                                  ") ENGINE=InnoDB DEFAULT CHARSET=utf8 ROW_FORMAT=DYNAMIC;"

        create_table_developers = "CREATE TABLE " + self.DB_NAME + ".developer( " \
                                  "id int(20) AUTO_INCREMENT PRIMARY KEY, " \
                                  "name varchar(256), " \
                                  "email varchar(256), " \
                                  "INDEX ne (name, email), " \
                                  "CONSTRAINT naem UNIQUE (name, email) " \
                                  ") ENGINE=InnoDB DEFAULT CHARSET=utf8 ROW_FORMAT=DYNAMIC;"

        create_table_commits = "CREATE TABLE " + self.DB_NAME + ".commit(" \
                               "id int(20) AUTO_INCREMENT PRIMARY KEY, " \
                               "repo_id int(20), " \
                               "sha varchar(512), " \
                               "message varchar(512), " \
                               "author_id int(20), " \
                               "committer_id int(20), " \
                               "authored_date timestamp, " \
                               "committed_date timestamp, " \
                               "size int(20), " \
                               "INDEX sha (sha), " \
                               "CONSTRAINT s UNIQUE (sha) " \
                               ") ENGINE=InnoDB DEFAULT CHARSET=utf8 ROW_FORMAT=DYNAMIC;"

        create_table_commit_parent = "CREATE TABLE " + self.DB_NAME + ".commit_parent(" \
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

        create_table_commits2reference = "CREATE TABLE " + self.DB_NAME + ".commit_in_reference(" \
                                         "repo_id int(20), " \
                                         "commit_id int(20), " \
                                         "ref_id int(20), " \
                                         "PRIMARY KEY core (commit_id, ref_id) " \
                                         ") ENGINE=InnoDB DEFAULT CHARSET=utf8 ROW_FORMAT=DYNAMIC;"

        create_table_files = "CREATE TABLE " + self.DB_NAME + ".file( " \
                             "id int(20) AUTO_INCREMENT PRIMARY KEY, " \
                             "repo_id int(20), " \
                             "name varchar(255), " \
                             "ext varchar(255), " \
                             "ref_id int(20), " \
                             "INDEX rrn (repo_id, ref_id, name), " \
                             "CONSTRAINT rerena UNIQUE (repo_id, ref_id, name) " \
                             ") ENGINE=InnoDB DEFAULT CHARSET=utf8 ROW_FORMAT=DYNAMIC;"

        create_table_file_renamed = "CREATE TABLE " + self.DB_NAME + ".file_renamed ( " \
                                    "repo_id int(20), " \
                                    "current_file_id int(20), " \
                                    "previous_file_id int(20), " \
                                    "PRIMARY KEY rena (current_file_id, previous_file_id), " \
                                    "INDEX current (current_file_id), " \
                                    "INDEX previous (previous_file_id) " \
                                    ") ENGINE=InnoDB DEFAULT CHARSET=utf8 ROW_FORMAT=DYNAMIC;"

        create_table_file_modifications = "CREATE TABLE " + self.DB_NAME + ".file_modification( " \
                                          "id int(20) AUTO_INCREMENT PRIMARY KEY, " \
                                          "commit_id int(20), " \
                                          "file_id int(20), " \
                                          "status varchar(10), " \
                                          "additions numeric(10), " \
                                          "deletions numeric(10), " \
                                          "changes numeric(10), " \
                                          "patch longblob, " \
                                          "INDEX c (commit_id), " \
                                          "INDEX f (file_id) " \
                                          ") ENGINE=InnoDB DEFAULT CHARSET=utf8 ROW_FORMAT=DYNAMIC;"

        create_table_lines = "CREATE TABLE " + self.DB_NAME + ".line_detail( " \
                             "file_modification_id int(11)," \
                             "type varchar(25), " \
                             "line_number numeric(20), " \
                             "is_commented numeric(1), " \
                             "is_partially_commented numeric(1), " \
                             "is_empty numeric(1), " \
                             "content longblob, " \
                             "PRIMARY KEY fityli (file_modification_id, type, line_number), " \
                             "INDEX fi (file_modification_id) " \
                             ") ENGINE=InnoDB DEFAULT CHARSET=utf8 ROW_FORMAT=DYNAMIC;"

        use_database = "USE " + self.DB_NAME

        cursor.execute(create_table_repositories)
        cursor.execute(create_table_references)
        cursor.execute(create_table_developers)
        cursor.execute(create_table_commits)
        cursor.execute(create_table_commit_parent)
        cursor.execute(create_table_commits2reference)
        cursor.execute(create_table_files)
        cursor.execute(create_table_file_renamed)
        cursor.execute(create_table_file_modifications)
        cursor.execute(create_table_lines)
        cursor.execute(use_database)
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