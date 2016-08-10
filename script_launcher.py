__author__ = 'valerio cosentino'

import gitana as Gitana

SCHEMA = "valcos_jbrex"
IMPORT_TYPE = 1 # 1 = light, 2 = medium, 3 = full
REPO_PATH = "C:/Users/atlanmod/Desktop/jbrex"
BEFORE_DATE = "2016-10-05"
IMPORT_LAST_COMMIT = 0 # 0 do not re-import the last commit, 1 re-import the last commit
LINE_DETAILS = True # True = line details, False = file details
FILTER = "in" # in = filter in, out = filter out

#output
OUTPUT_JSON = "C:/Users/atlanmod/Desktop/gitana-env/Gitana/json/output.json"
OUTPUT_FILTERED_JSON = "C:/Users/atlanmod/Desktop/gitana-env/Gitana/json/filtered.output.json"
OUTPUT_ALIASES_JSON = "C:/Users/atlanmod/Desktop/gitana-env/Gitana/json/filtered.aliased.output.json"

#file settings
FORBIDDEN_RESOURCES_PATH = "C:/Users/atlanmod/Desktop/gitana-env/Gitana/settings/xxx.frs"
FORBIDDEN_EXTENSION_PATH = "C:/Users/atlanmod/Desktop/gitana-env/Gitana/settings/xxx.fex"
USER_ALIASES_PATH = "C:/Users/atlanmod/Desktop/gitana-env/Gitana/settings/xxx.nal"


def db2json():
    g = Gitana(SCHEMA)
    g.db2json(SCHEMA, OUTPUT_JSON, LINE_DETAILS)
    g.filtering(OUTPUT_JSON, OUTPUT_FILTERED_JSON, FORBIDDEN_RESOURCES_PATH, FORBIDDEN_EXTENSION_PATH, FILTER)
    g.aliasing(OUTPUT_JSON, OUTPUT_ALIASES_JSON, USER_ALIASES_PATH)


def updatedb():
    g = Gitana(SCHEMA)
    g.updatedb(SCHEMA, REPO_PATH, BEFORE_DATE, IMPORT_LAST_COMMIT)


def git2db():
    g = Gitana(SCHEMA)
    g.init_dbschema(SCHEMA)
    g.git2db(SCHEMA, REPO_PATH, BEFORE_DATE, IMPORT_TYPE)


def main():
    git2db()
    updatedb()
    db2json()

if __name__ == "__main__":
    main()
