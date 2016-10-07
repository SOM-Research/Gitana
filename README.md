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
#if LOGS-PATH is None, a log folder will be created in the same directory where Gitana is executed
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

## Example(s)

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

## Gitana extension(s)

- Gitana can be used also to calculate the bus factor (https://github.com/SOM-Research/busfactor). However, at the moment, this can be done only using Gitana 0.2 (https://github.com/SOM-Research/Gitana/tree/0.2)
