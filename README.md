# Gitana: a SQL-based Project Activity Inspector
 
Gitana exports and digests the data of a Git repository, issue trackers and Q&A web-sites to a relational database 
in order to ease browsing and querying activities with standard SQL syntax and tools.

To ensure efficiency, an incremental propagation mechanism refreshes the
database content with the latest project activities.

## Technical details

Gitana is developed on Windows 7 and it relies on:
- Python 2.7.6
- MySQL Server 5.6 (http://dev.mysql.com/downloads/installer/) 

## Installation

After installing MySQL Server and Python 2.7.6, follow the instructions below to download the packages used by Gitana:
- set pip to be used from the command prompt (CMD)
- in the CMD
 - cd to the directory where requirements.txt is located
 - run the following command:
   ```
   pip install -r requirements.txt
   ```

## How to use Gitana (master version)

### import Gitana
```python
from gitana import Gitana
```

### instantiate Gitana
```python
CONFIG = {
            'user': 'root',
            'password': 'root',
            'host': 'localhost',
            'port': '3306',
            'raise_on_warnings': False,
            'buffered': True
        }

g = Gitana(CONFIG, "LOGS-PATH")
# if LOGS-PATH is None, a log folder will be created in the same directory where Gitana is executed
```

### initialize Gitana DB
```python
g.init_db("NAME-OF-YOUR-DB")

# NAME-OF-YOUR-DB cannot be null, and must follow the format allowed in MySQL (http://dev.mysql.com/doc/refman/5.7/en/identifiers.html)
# if a DB with the input name already exists in Gitana, the existing DB will be dropped and a new one will be created
```

### create a project in Gitana
```python
g.create_project("NAME-OF-YOUR-DB", "NAME-OF-THE-PROJECT")

# NAME-OF-YOUR-DB should point to a DB already existing in Gitana 
# NAME-OF-THE-PROJECT should not be null
```

### import git data
```python
g.import_git_data("NAME-OF-YOUR-DB", "NAME-OF-THE-PROJECT", "NAME-OF-THE-GIT-REPO", "GIT-REPO-PATH", 
                  "BEFORE-DATE", "RECOVERY-PROCESS", "LIST-OF-REFERENCES", "NUM-OF-PROCESSES")
                  
# NAME-OF-YOUR-DB and NAME-OF-THE-PROJECT should point to a DB and project already existing in Gitana 
# NAME-OF-THE-GIT-REPO, GIT-REPO-PATH cannot be null
# BEFORE-DATE can be None or "%Y-%m-%d". It allows to import references and commits created before a given date
# RECOVER-IMPORT can be True or False. It allows to restart the import from the last commit inserted
# LIST-OF-REFERENCES can be None or ["x1", .., "xn"]. It allows to import the data of a set of repo references (tag or branches)
# NUM-OF-PROCESSES can be None or a int number. It is the number of parallel processes used to analyse the Git repo. if None, the number of processes is 10
```

### update git data 
- it updates the references already stored in Gitana, and optionally import new references)
```python
g.update_git_data("NAME-OF-YOUR-DB", "NAME-OF-THE-PROJECT", "NAME-OF-THE-GIT-REPO", "GIT-REPO-PATH", 
                  "BEFORE-DATE", "RECOVERY-PROCESS", "IMPORT-NEW-REFERENCES", "NUM-OF-PROCESSES")
                  
# NAME-OF-YOUR-DB and NAME-OF-THE-PROJECT should point to a DB and project already existing in Gitana 
# NAME-OF-THE-GIT-REPO, GIT-REPO-PATH cannot be null
# BEFORE-DATE can be None or "%Y-%m-%d". It allows to import references and commits created before a given date
# RECOVER-IMPORT can be True or False. It allows to restart the import from the last commit inserted
# IMPORT-NEW-REFERENCES can be True or False. It allows to import new references in the Git repo not included in Gitana. If False, only the references included in the DB will be updated with the missing commits
# NUM-OF-PROCESSES can be None or a int number. It is the number of parallel processes used to analyse the Git repo. if None, the number of processes is 10
```

### import bugzilla data
```python
g.import_bugzilla_tracker_data("NAME-OF-YOUR-DB", "NAME-OF-THE-PROJECT", "NAME-OF-THE-GIT-REPO", 
                               "BUGZILLA-URL", "PRODUCT-NAME-IN-BUGZILLA", 
                               "BEFORE-DATE", "RECOVER-IMPORT", "NUM-OF-PROCESSES")
  
# NAME-OF-YOUR-DB, NAME-OF-THE-PROJECT, NAME-OF-THE-GIT-REPO should point to a DB, project and repo already existing in Gitana 
# BUGZILLA-URL cannot be null. It points to the URL REST API (e.g., "https://bugs.eclipse.org/bugs/xmlrpc.cgi")
# PRODUCT-NAME cannot be null. It will collect the issues for the input product (e.g., "MDT.MoDisco")
# BEFORE-DATE can be None or "%Y-%m-%d". It allows to import issues created before a given date
# RECOVER-IMPORT can be True or False. It allows to restart the import from the last issue inserted
# NUM-OF-PROCESSES can be None or a int number. It is the number of parallel processes used to collect issue tracker information. if None, the number of processes is 10
```
    
### update bugzilla data 
- it updates only the issues already stored in Gitana. It does not import new ones
```python 
g.update_bugzilla_tracker_data("NAME-OF-YOUR-DB", "NAME-OF-THE-PROJECT", "NAME-OF-THE-GIT-REPO",
                               "BUGZILLA-URL", "PRODUCT-NAME-IN-BUGZILLA", "NUM-OF-PROCESSES")

# NAME-OF-YOUR-DB, NAME-OF-THE-PROJECT, NAME-OF-THE-GIT-REPO should point to a DB, project and repo already existing in Gitana 
# BUGZILLA-URL cannot be null. It points to the URL REST API (e.g., "https://bugs.eclipse.org/bugs/xmlrpc.cgi")
# PRODUCT-NAME cannot be null. It will update the issues already in Gitana for the input product (e.g., "MDT.MoDisco")
# NUM-OF-PROCESSES can be None or a int number. It is the number of parallel processes used to collect issue tracker information. if None, the number of processes is 10
```

### import Eclipse forum data
```python 
g.import_eclipse_forum_data("NAME-OF-YOUR-DB", "NAME-OF-THE-PROJECT", "ECLIPSE-FORUM-URL",
                               "BEFORE-DATE", "RECOVER-IMPORT", "NUM-OF-PROCESSES")

# NAME-OF-YOUR-DB, NAME-OF-THE-PROJECT should point to a DB and project already existing in Gitana 
# ECLIPSE-FORUM-URL cannot be null. It points to the URL of the Eclipse forum (e.g., "https://www.eclipse.org/forums/index.php/f/241/")
# BEFORE-DATE can be None or "%Y-%m-%d". It allows to import topics created before a given date
# RECOVER-IMPORT can be True or False. It allows to restart the import from the last topic inserted
# NUM-OF-PROCESSES can be None or a int number. It is the number of parallel browsers used to collect forum information. if None, the number of processes is 2
```

### update Eclipse forum data 
- it updates only the topics already stored in Gitana. It does not import new ones
```python 
g.update_eclipse_forum_data("NAME-OF-YOUR-DB", "NAME-OF-THE-PROJECT", "ECLIPSE-FORUM-URL", "NUM-OF-PROCESSES")

# NAME-OF-YOUR-DB, NAME-OF-THE-PROJECT should point to a DB and project already existing in Gitana 
# ECLIPSE-FORUM-URL cannot be null. It points to the URL of the Eclipse forum (e.g., "https://www.eclipse.org/forums/index.php/f/241/")
# NUM-OF-PROCESSES can be None or a int number. It is the number of parallel browsers used to collect forum information. if None, the number of processes is 2
```

### Example(s)

```python 
from gitana import Gitana

CONFIG = {
            'user': 'root',
            'password': 'root',
            'host': 'localhost',
            'port': '3306',
            'raise_on_warnings': False,
            'buffered': True
        }

def main():
    g = Gitana(CONFIG, None)
    g.init_db("papyrus_db")

    g.create_project("papyrus_db", "papyrus")
    g.import_git_data("papyrus_db", "papyrus", "papyrus_repo", "...\\Desktop\\org.eclipse.papyrus", None, 1, None, 20)
    g.import_bugzilla_tracker_data("papyrus_db", "papyrus", "papyrus_repo", "https://bugs.eclipse.org/bugs/xmlrpc.cgi", "papyrus", None, False, 20)
    g.import_eclipse_forum_data("papyrus_db", "papyrus", "https://www.eclipse.org/forums/index.php/f/121/", None, False, 5)
    
if __name__ == "__main__":
    main()
```

## How to use the Gitana Exporter (master version)

Gitana provides also a gexf exporter with predefined metrics to analyse data using graph analysis tools (e.g., Gephi). The metrics are stored in a JSON file (https://github.com/SOM-Research/Gitana/blob/master/exporter/resources/queries.json) and must be parameterized by the users. Currently, the metrics available are:

- **users-on-issues**. It generates a graph where each node is a user and its size is proportional to the number of issues the user commented. There exists an edge between two users if they have commented on the same issue (thickness proportional to the number of issues both have contributed to).

- **users-on-files**. It generates a graph where each node is a user and its size is proportional to the number of files the user contributed to. There exists an edge between two users if they have worked on the same file (thickness proportional to the number of files both have contributed to).

- **users-on-files-for-references**. This metric is similar to the previous one, but can defined for a sub-set of references (branches or tags)

### JSON structure

Each metric in the JSON file contains a fixed part (lowercase attributes) and a variable part (uppercase attributes), that must be tuned by the user. For instance, in the example below, the user should modify the values of the attributes PROJECTID, REPOID, NODECOLOR, EDGECOLOR. Such values will be then used to build the SQL queries to retrieve nodes and edges from the Gitana DB.

```json
{"name": "users-on-files",
 "PROJECTID": "1",
 "REPOID": "1",
 "NODECOLOR": "blue",
 "EDGECOLOR": "gray",
 "nodes": "sql-query-for-nodes",
 "edges": "sql-query-for-edges"
 }
 ```
Currently the available colors are the following: 
 ```
 "white", "gray", "black", "blue", "cyan", "green", "yellow", "red", "brown", "orange", "pink", "purple", "violet" 
 ```

### import Gitana Exporter
```python 
from exporter.gexf_exporter import GexfExporter
```

### instantiate Gitana Exporter
```python
CONFIG = {
            'user': 'root',
            'password': 'root',
            'host': 'localhost',
            'port': '3306',
            'raise_on_warnings': False,
            'buffered': True
        }

gexf = GexfExporter(CONFIG, "NAME-OF-YOUR-DB", "LOGS-PATH")
# NAME-OF-YOUR-DB should point to a DB already existing in Gitana 
# if LOGS-PATH is None, a log folder will be created in the same directory where Gitana Exporter is executed
```

### export Gitana data
```python
gexf.export("OUTPUT-FILE-PATH", "GRAPH-TYPE", "GRAPH-MODE", "METRIC-NAME")
                  
# OUTPUT-FILE-PATH point to a location where to store the gexf output file
# GRAPH-TYPE can be "undirected" or "directed". If None, the default type is "undirected"
# GRAPH-MODE can be "static" or "dynamic". If None, the default mode is "dynamic"
# METRIC-NAME is the name of the metric to execute. It can be: "users-on-issues", "users-on-files", "users-on-files-for-references"
```

### Example(s)

```python 
from exporter.gexf_exporter import GexfExporter

CONFIG = {
            'user': 'root',
            'password': 'root',
            'host': 'localhost',
            'port': '3306',
            'raise_on_warnings': False,
            'buffered': True
        }


def main():
    gexf = GexfExporter(CONFIG, "papyrus_db", None)
    gexf.export("./export.gexf", "undirected", "dynamic", "users-on-issues")


if __name__ == "__main__":
    main()
```

## Gitana extension(s)

Gitana can be used also to calculate the bus factor (https://github.com/SOM-Research/busfactor). However, at the moment, this can be done only using Gitana 0.2 (https://github.com/SOM-Research/Gitana/tree/0.2)
