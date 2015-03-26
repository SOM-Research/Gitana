
__author__ = 'atlanmod'

import logging
import logging.handlers
from init_dbschema import InitDbSchema
from git2db import Git2Db
from db2json import Db2Json
from updatedb import UpdateDb
from aliaser import Aliaser
from filter import Filter


class Gitana():

    LOG_FILENAME = "gitana_log"

    def __init__(self, schema):
        self.logger = logging.getLogger(schema)
        fileHandler = logging.FileHandler(Gitana.LOG_FILENAME + "_" + schema, mode='w')
        formatter = logging.Formatter("%(asctime)s:%(levelname)s:%(message)s", "%Y-%m-%d %H:%M:%S")
        fileHandler.setFormatter(formatter)

        self.logger.setLevel(logging.INFO)
        self.logger.addHandler(fileHandler)

    def init_dbschema(self, db_name):
        i = InitDbSchema(db_name, self.logger)
        i.execute()
        return

    def git2db(self, db_name, git_path):
        extractor = Git2Db(db_name, git_path, None, self.logger)
        extractor.extract()
        return

    def git2db_before_date(self, db_name, git_path, before):
        extractor = Git2Db(db_name, git_path, before, self.logger)
        extractor.extract()
        return

    def db2json(self, db_name, json_path, line_details):
        exporter = Db2Json(db_name, json_path, line_details, self.logger)
        exporter.export()
        return

    def aliasing(self, source_json_path, target_aliasing_path, name_aliases_path):
        aliaser = Aliaser(source_json_path, target_aliasing_path, name_aliases_path, self.logger)
        aliaser.execute()
        return

    def filtering(self, source_json_path, target_filtered_path, filtered_resources_path, filtered_extensions_path, filtering_type):
        filter = Filter(source_json_path, target_filtered_path, filtered_resources_path, filtered_extensions_path, filtering_type, self.logger)
        filter.filter()
        return

    def updatedb(self, db_name, git_path):
        updater = UpdateDb(db_name, git_path, None, logging)
        updater.update()
        return

    def updatedb_before_date(self, db_name, git_path, before):
        updater = UpdateDb(db_name, git_path, before, logging)
        updater.update()
        return