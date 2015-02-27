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

In order to use Gitana, your machine needs to fulfill the technical details. Then, you can launch the script gitana_gui.py (https://github.com/valeriocos/Gitana/blob/master/gitana_gui.py) and a GUI will allow you 
to complete the following steps:

- import your Git repository to a database (**Import Git to DB**)
- update your database with the latest Git repository modifications (**Update DB**)
- export your database to JSON (**Export DB to JSON**)

### Settings

- **Import Git to DB**. You can import to the database just a slice of your Git repository by selecting the "before date" field. Thus, your database will contain the Git information from the very first commit until the commit(s) pushed before the date set in the "before date" field.

- **Update DB**. You can update the database information until a given date, thus all the commits pushed before the date set in the "before date" field will be included in the database.

- **Export DB to JSON**. You can export the database information to the JSON format to perform analysis on your repository beyond SQL. The output of this step is a file that contains a JSON entry per file (currently present and deleted) in the repository. The JSON entry is composed of:
 - *overall information*: name and extension of the file, directories is contained, line count, status (deleted or present), last modification.
 
 - *commits information*: all the commits where the file has been modified. Each commit contains committer and author information as well as the sha and the commit message.
 
 -  *file changes*: all the changes on the file. Each file change contains the number of additions and deletions, the commit that modified it and the corresponding patch.
 
 -  *line changes*: all the line changes on the file. Each line change contains the modified number of line, the related commit and the patch for that specific line.

 - **Parametrizations of the export step:**
 - **Filtering.** It allows to filter in/out single files, directories, entire references (branches or tags). In addition, the files can be filter in/out also according to their file extensions. Example of filterings are available at https://github.com/valeriocos/Gitana/blob/master/settings/gila.frs and https://github.com/valeriocos/Gitana/blob/master/settings/gila.fex
 
 - **Aliasing.** It allows to assign aliases to developers in order, for instance, to merge different user names corresponding to the same physical person or to group developers according to the development (sub)team they belong to.
 
 - **Detail Level.** It allows to export fine-grained information (line changes) or just the modifications at file level (file changes)
 
 



### Gitana extensions

- Bus factor for Git repositories (https://github.com/valeriocos/BusFactor)
