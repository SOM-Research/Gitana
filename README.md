# Gitana: a SQL-based Project Activity Inspector
 
Gitana exports and digests the data of a Git repository, issue trackers and Q&A web-sites to a relational database 
in order to ease browsing and querying activities with standard SQL syntax and tools.

To ensure efficiency, an incremental propagation mechanism refreshes the
database content with the latest project activities.

### Technical details

Gitana is written in Python 2.7.6, it relies on 

- GitPython >=0.3.1-beta2 (https://pypi.python.org/pypi/GitPython)
- python-bugzilla >= 1.2.2 (https://pypi.python.org/pypi/python-bugzilla/1.2.2)
- Git-1.9.4 (https://github.com/msysgit/msysgit/releases)
- MySQL Server 5.6 (http://dev.mysql.com/downloads/installer/)
- mysql-connector-python (https://pypi.python.org/pypi/mysql-connector-python)

### How to use Gitana

In order to use Gitana, your machine needs to fulfill the technical details. Then, you can use the different scripts to instantiate and populate the DB

- the script extractor/init_db/init_dbschema.py initializes the DB schema in your MySQL instance
- the script extractor/git_tracker/git2db_main.py imports the data from a Git repository
- the script extractor/git_tracker/gitupdate.py updates the DB content with the latest modifications tracked in the Git repo
- the script extractor/issue_tracker_bugzilla/issue2db_main.py imports the data from the Bugzilla tracker
- the script extractor/issue_tracker_bugzilla/issueupdate.py updates the DB content with the lastest modifications in the Bugzilla tracker

### Gitana extensions

- Gitana can be used also to calculate the bus factor (https://github.com/SOM-Research/busfactor). However, at the moment, this can be done only using Gitana 0.2 (https://github.com/SOM-Research/Gitana/tree/0.2)
