# Gitana: a SQL-based Git Repository Inspector
 
Gitana exports and digests the data of a Git repository to a relational database 
in order to ease browsing and querying activities with standard SQL syntax and tools. 

To ensure efficiency, an incremental propagation mechanism refreshes the
database content with the latest Git repository modifications.

Gitana also provides a JSON exporter to facilitate 
the analysis of the repository data with other technologies.


### Technical details

Gitana is written in Python 2.7.6, it relies on 

- GitPython >=0.3.1-beta2 (https://pypi.python.org/pypi/GitPython)
- Git-1.9.4 (https://github.com/msysgit/msysgit/releases)
- MySQL Server 5.6 (http://dev.mysql.com/downloads/installer/)


### How to use Gitana

Launch the script gitana_gui.py (https://github.com/valeriocos/Gitana/blob/master/gitana_gui.py) and a GUI will allow you 
to:

- extract your Git repository to a database
- update your database with the latest Git repository modifications
- export your database to JSON

### Gitana extensions

- Bus factor for Git repositories (https://github.com/valeriocos/BusFactor)
