# Gitana: a SQL-based Project Activity Inspector
 
Gitana imports and digests the data of Git repositories, issue trackers, Q&A web-sites and Instant messaging services to a relational database
in order to ease browsing and querying activities with standard SQL syntax and tools. To ensure efficiency, an incremental propagation mechanism refreshes the
database content with the latest project activities.

Gitana also provides support to generate project activity reports and perform complex network analysis.

## Documentation

More information can be found on the [Gitana documentation site.](http://gitanadocs.getforge.io/)

## Who is behind this project?

* [Valerio Cosentino](http://valeriocos.github.io "Valerio Cosentino")
* [Javier Canovas](http://github.com/jlcanovas/ "Javier Canovas")
* [Jordi Cabot](http://github.com/jcabot/ "Jordi Cabot")

## Licensing

Gitana is distributed under the MIT License (https://opensource.org/licenses/MIT)

## Technical details

Gitana is developed on Windows 7 and it relies on:
- Python 2.7.6
- MySQL Server 5.6 (http://dev.mysql.com/downloads/installer/) 

## Installation

After installing MySQL Server and Python 2.7.6, execute the setup script.
```
$> cd Gitana
$> python setup.py build
$> python setup.py install
```
   
## How to use Gitana

### import Gitana
```python
from gitana.gitana import Gitana
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
g.init_db("DB-NAME")

# DB-NAME cannot be null, and must follow the format allowed in MySQL (http://dev.mysql.com/doc/refman/5.7/en/identifiers.html)
# if a DB having a name equal to DB-NAME already exists in Gitana, the existing DB will be dropped and a new one will be created
```

### create a project in Gitana
```python
g.create_project("DB-NAME", "PROJECT-NAME")

# DB-NAME should point to a DB already existing in Gitana
# PROJECT-NAME should not be null
```

### import Git data
```python
g.import_git_data("DB-NAME", "PROJECT-NAME", "GIT-REPO-NAME", "GIT-REPO-PATH",
                  "IMPORT-TYPE", "LIST-OF-REFERENCES", "BEFORE-DATE", "NUM-OF-PROCESSES")
                  
# DB-NAME and PROJECT-NAME should point to a DB and project already existing in Gitana
# GIT-REPO-NAME, GIT-REPO-PATH cannot be null
# IMPORT-TYPE can be 1, 2 or 3. It allows to define the granularity of the import process. 1 does not import patches, 2 imports patches but not at line level, 3 imports patches with line detail. Defaults to type 1.
# LIST-OF-REFERENCES can be None or ["ref-name-1", .., "ref-name-n"]. It allows to import the data of a set of repo references (tag or branches)
# BEFORE-DATE can be None or "%Y-%m-%d". It allows to import references and commits created before a given date
# NUM-OF-PROCESSES can be None or a int number. It is the number of parallel processes used to analyse the Git repo. if None, the number of processes is 5
```

### update Git data
- it updates the references already stored in Gitana.
```python
g.update_git_data("DB-NAME", "PROJECT-NAME", "GIT-REPO-NAME", "GIT-REPO-PATH",
                  "BEFORE-DATE", "NUM-OF-PROCESSES")
                  
# DB-NAME and PROJECT-NAME should point to a DB and project already existing in Gitana
# GIT-REPO-NAME, GIT-REPO-PATH cannot be null
# BEFORE-DATE can be None or "%Y-%m-%d". It allows to import references and commits created before a given date
# NUM-OF-PROCESSES can be None or a int number. It is the number of parallel processes used to analyse the Git repo. if None, the number of processes is 3
```

### import Bugzilla data
```python
g.import_bugzilla_tracker_data("DB-NAME", "PROJECT-NAME", "GIT-REPO-NAME",
                               "ISSUE-TRACKER-NAME", "BUGZILLA-URL", "PRODUCT-NAME-IN-BUGZILLA",
                               "BEFORE-DATE", "NUM-OF-PROCESSES")
  
# DB-NAME, PROJECT-NAME, GIT-REPO-NAME should point to a DB, project and repo already existing in Gitana
# ISSUE-TRACKER-NAME cannot be null. It is the name used to identify the issue tracker in the DB
# BUGZILLA-URL cannot be null. It points to the URL REST API (e.g., "https://bugs.eclipse.org/bugs/xmlrpc.cgi")
# PRODUCT-NAME cannot be null. It will collect the issues for the input product (e.g., "MDT.MoDisco")
# BEFORE-DATE can be None or "%Y-%m-%d". It allows to import issues created before a given date
# NUM-OF-PROCESSES can be None or a int number. It is the number of parallel processes used to collect issue tracker information. if None, the number of processes is 3
```
    
### update Bugzilla data
- it updates only the issues already stored in Gitana. It does not import new ones
```python 
g.update_bugzilla_tracker_data("DB-NAME", "PROJECT-NAME", "GIT-REPO-NAME",
                               "ISSUE-TRACKER-NAME", "PRODUCT-NAME-IN-BUGZILLA", "NUM-OF-PROCESSES")

# DB-NAME, PROJECT-NAME, GIT-REPO-NAME should point to a DB, project and repo already existing in Gitana
# ISSUE-TRACKER-NAME cannot be null. It points to the issue tracker stored in the DB
# PRODUCT-NAME cannot be null. It will update the issues already in Gitana for the input product (e.g., "MDT.MoDisco")
# NUM-OF-PROCESSES can be None or a int number. It is the number of parallel processes used to collect issue tracker information. if None, the number of processes is 5
```

### import Eclipse forum data
```python 
g.import_eclipse_forum_data("DB-NAME", "PROJECT-NAME", "FORUM-NAME", "ECLIPSE-FORUM-URL",
                               "BEFORE-DATE", "NUM-OF-PROCESSES")

# DB-NAME, PROJECT-NAME should point to a DB and project already existing in Gitana
# FORUM-NAME cannot be null. It is the name used to identify the forum in the DB
# ECLIPSE-FORUM-URL cannot be null. It points to the URL of the Eclipse forum (e.g., "https://www.eclipse.org/forums/index.php/f/241/")
# BEFORE-DATE can be None or "%Y-%m-%d". It allows to import topics created before a given date
# NUM-OF-PROCESSES can be None or a int number. It is the number of parallel browsers used to collect forum information. if None, the number of processes is 2
```

### update Eclipse forum data 
- it updates only the topics already stored in Gitana. It does not import new ones
```python 
g.update_eclipse_forum_data("DB-NAME", "PROJECT-NAME", "FORUM-NAME", "NUM-OF-PROCESSES")

# DB-NAME, PROJECT-NAME should point to a DB and project already existing in Gitana
# FORUM-NAME cannot be null. It points to the forum stored in the DB
# NUM-OF-PROCESSES can be None or a int number. It is the number of parallel browsers used to collect forum information. if None, the number of processes is 2
```

### import Stackoverflow data
```python
g.import_stackoverflow_data("DB-NAME", "PROJECT-NAME", "FORUM-NAME", "QUERY-STRING", "LIST-OF-TOKENS", "BEFORE-DATE")

# DB-NAME, PROJECT-NAME should point to a DB and project already existing in Gitana
# FORUM-NAME cannot be null. It is the name used to identify the forum in the DB
# QUERY-STRING cannot be null. It is used to retrieved the Questions in Stackoverflow labelled with "QUERY-STRING"
# "LIST-OF-TOKENS" cannot be null. Each token is passed to a process to speed up the collection of StackOverflow information.
# BEFORE-DATE can be None or "%Y-%m-%d". It allows to import topics created before a given date
```

### update Stackoverflow data
```python
g.update_stackoverflow_data("DB-NAME", "PROJECT-NAME", "FORUM-NAME", ""LIST-OF-TOKENS"")

# DB-NAME, PROJECT-NAME should point to a DB and project already existing in Gitana
# FORUM-NAME cannot be null. It is the name used to identify the forum in the DB
# QUERY-STRING cannot be null. It is used to retrieved the Questions in Stackoverflow labelled with "QUERY-STRING"
# "LIST-OF-TOKENS" cannot be null. Each token is passed to a process to speed up the collection of StackOverflow information.
```

### import Slack data
```python
g.import_slack_data("DB-NAME", "PROJECT-NAME", "INSTANT-MESSAGING-NAME", ""LIST-OF-TOKENS"", "BEFORE-DATE", "LIST-OF-CHANNELS")

# DB-NAME, PROJECT-NAME should point to a DB and project already existing in Gitana
# INSTANT-MESSAGING-NAME cannot be null. It is the name used to identify the instant messaging service in the DB
# "LIST-OF-TOKENS" cannot be null. Each token is passed to a process to speed up the collection of Slack information.
# BEFORE-DATE can be None or "%Y-%m-%d". It allows to import channels created before a given date
# LIST-OF-CHANNELS. can be None or ["channel-name-1", .., "channel-name-n"]. It allows to import the data of a set of channels
```

### update Slack data
```python
g.update_slack_data("DB-NAME", "PROJECT-NAME", "INSTANT-MESSAGING-NAME", ""LIST-OF-TOKENS"")
# DB-NAME, PROJECT-NAME should point to a DB and project already existing in Gitana
# INSTANT-MESSAGING-NAME cannot be null. It is the name used to identify the instant messaging service in the DB
# "LIST-OF-TOKENS" cannot be null. Each token is passed to a process to speed up the collection of Slack information.
```

### import GitHub issue data
```python
g.import_github_issue_data("DB-NAME", "PROJECT-NAME", "GIT-REPO-NAME",
                             "ISSUE-TRACKER-NAME", "GITHUB-REPO-FULLNAME",
                             ""LIST-OF-TOKENS"", "BEFORE-DATE")

# DB-NAME, PROJECT-NAME, GIT-REPO-NAME should point to a DB, project and repo already existing in Gitana
# ISSUE-TRACKER-NAME cannot be null. It is the name used to identify the issue tracker in the DB
# GITHUB-REPO-FULLNAME cannot be null. It points to the GitHub repository to import
# "LIST-OF-TOKENS" cannot be null. Each token is passed to a process to speed up the collection of GitHub information.
# BEFORE-DATE can be None or "%Y-%m-%d". It allows to import issues created before a given date
```

### update GitHub issue data
```python
g.update_github_issue_data("DB-NAME", "PROJECT-NAME", "GIT-REPO-NAME",
                             "ISSUE-TRACKER-NAME", "GITHUB-REPO-FULLNAME",
                             ""LIST-OF-TOKENS"")
  
# DB-NAME, PROJECT-NAME, GIT-REPO-NAME should point to a DB, project and repo already existing in Gitana
# ISSUE-TRACKER-NAME cannot be null. It is the name used to identify the issue tracker in the DB
# GITHUB-REPO-FULLNAME cannot be null. It points to the GitHub repository to import
# "LIST-OF-TOKENS" cannot be null. Each token is passed to a process to speed up the collection of GitHub information.
```

### export Gitana data to GEXF graph
```python
g.export_graph("DB-NAME", "SETTINGS-PATH", "OUTPUT-PATH")
  
# DB-NAME should point to a DB already existing in Gitana
# SETTINGS-PATH cannot be null. It points to the Graph Exporter DSL instance.
# OUTPUT-PATH cannot be null. It points to the path of the GEXF output file 
```
Further information about the Graph Exporter DSL can be found in the [documentation](http://gitanadocs.getforge.io/graphdsl.html)

### export Gitana data to HTML report
```python
g.export_activity_report("DB-NAME", "SETTINGS-PATH", "OUTPUT-PATH")
  
# DB-NAME should point to a DB already existing in Gitana
# SETTINGS-PATH cannot be null. It points to the Report Exporter DSL instance.
# OUTPUT-PATH cannot be null. It points to the path of the HTML output file 
```
Further information about the Report Exporter DSL can be found in the [documentation](http://gitanadocs.getforge.io/reportdsl.html)

## Simple Demo

```python 
from gitana.gitana import Gitana

CONFIG = {
            'user': 'root',
            'password': 'root',
            'host': 'localhost',
            'port': '3306',
            'raise_on_warnings': False,
            'buffered': True
        }

def main():
    g = Gitana(CONFIG)
    g.init_db("papyrus_db")

    g.create_project("papyrus_db", "papyrus")
    g.import_git_data("papyrus_db", "papyrus", "papyrus_repo", "...\\Desktop\\org.eclipse.papyrus")
    g.import_bugzilla_issue_data("papyrus_db", "papyrus", "papyrus_repo", "papyrus-bugzilla", "https://bugs.eclipse.org/bugs/xmlrpc.cgi", "papyrus")
    g.import_eclipse_forum_data("papyrus_db", "papyrus", "papyrus-forum", "https://www.eclipse.org/forums/index.php/f/121/")
    g.import_stackoverflow_data("papyrus_db", "papyrus", "papyrus-so", ['YOUR-TOKEN-1', 'YOUR-TOKEN-2', ...])
	
    g.export_graph("papyrus_db", "./graph.json", "./graph.gexf")
    g.export_activity_report("papyrus_db", "./report.json", "./report.html")
	
if __name__ == "__main__":
    main()
```

## Gitana extension(s)

Gitana can be used also to calculate the bus factor (https://github.com/SOM-Research/busfactor). However, at the moment, this can be done only using Gitana 0.2 (https://github.com/SOM-Research/Gitana/tree/0.2)
