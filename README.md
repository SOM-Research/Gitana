# Gitana: a SQL-based Project Activity Inspector
 
Gitana exports and digests the data of a Git repository, issue trackers and Q&A web-sites to a relational database 
in order to ease browsing and querying activities with standard SQL syntax and tools.

To ensure efficiency, an incremental propagation mechanism refreshes the
database content with the latest project activities.

### Technical details

Gitana is developed on Windows 7 and it relies on:
- Python 2.7.6
- MySQL Server 5.6 (http://dev.mysql.com/downloads/installer/) 

### Installation

After installing MySQL Server and Python 2.7.6, follow the instructions below to download the packages used by Gitana:
- set pip to be used from the command prompt (CMD)
- in the CMD
 - cd to the directory where requirements.txt is located
 - run the following command:
   ```
   pip install -r requirements.txt
   ```

### How to use Gitana (version 1.0)

Set the following parameters in the extractor/init_db/config_db.py:

- **DB_NAME:** the name of the database to be created in your MySQL instance
- **REPO_NAME:** the name of the repository to analyse
- **GIT_REPO_PATH:** the path to the Git repository to analyse
- **CONFIG:** the credentials to access your MySQL instance

Then, you can use the different scripts to instantiate and populate the DB

- **extractor/init_db/init_dbschema.py** initializes the DB schema in your MySQL instance
- **extractor/git_tracker/git2db_main.py** imports the data from a Git repository

 - you can set the name of the **REFERENCES** to import and the number of **PROCESSES** (default 30) launched to extract the data from the Git repository

- **extractor/git_tracker/gitupdate.py** updates the DB content with the latest modifications tracked in the Git repo
- **extractor/issue_tracker_bugzilla/issue2db_main.py** imports the data from the Bugzilla tracker
 - you can set the **URL** to the Bugzilla repository, the number of **PROCESSES** (default 30) launched to extract the data from it and the target **PRODUCT** 
- **extractor/issue_tracker_bugzilla/issueupdate.py** updates the DB content with the lastest modifications in the Bugzilla tracker
 - Note that this script will update only the issues already stored in Gitana. This operation is automatically performed by issue2db_main.py
- **exporter/gexf_exporter.py** exports the data stored in the DB to a GEXF file, that can be analysed with Gephi.
  Currently, the export generates a graph where nodes represent users and their sizes are the number of issue comments written by the user. An edge exists between two nodes if the two corresponding users have commented on the same issue.

### Gitana extensions

- Gitana can be used also to calculate the bus factor (https://github.com/SOM-Research/busfactor). However, at the moment, this can be done only using Gitana 0.2 (https://github.com/SOM-Research/Gitana/tree/0.2)
