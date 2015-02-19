# Gitana: a SQL-based Git Repository Inspector
 
Gitana exports and digests the data of a Git repository to a relational database 
in order to ease browsing and querying activities with standard SQL syntax and tools. 

To ensure efficiency, an incremental propagation mechanism refreshes the
database content with the latest Git repository modifications.

Gitana also provides a JSON exporter to facilitate 
the analysis of the repository data with other technologies.


### Technical details

Gitana is written in Python 2.7.6 and relies on the version 0.3.1 of GitPython (https://pypi.python.org/pypi/GitPython), a library
to interact with Git repositories. The database integrated to Gitana has been implemented in MySQL

### How to use Gitana

Launch the script gui.py (https://github.com/valeriocos/Gitana/blob/master/gui.py) and a GUI interface will allow you 
to:

- extract your Git repository to a database
- update your database with the latest Git repository modifications
- export your database to JSON
