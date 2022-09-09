> NOTE: Gitana has been archived and is not maintained anymore. We have deactivated the issue tracker as we cannot offer support either. The development status of our tools is declared [here](https://som-research.uoc.edu/research-tools/). Feel free to contact us for further information.

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

## Requirements

Gitana is developed on Windows 7 and it relies on:
- Git 2.9.3 ([download](https://git-scm.com/downloads))
- MySQL Server 5.6 ([download](http://dev.mysql.com/downloads/installer/))
- Python 2.7.6 ([download](https://www.python.org/downloads/windows/))

Python and pip package manager can be set to be executed from Windows command line by adding to the Path environment variable
the paths where Python and its scripts are installed. By default, these paths are:
```
C:\Python27
C:\Python27\Scripts
```

##  Installation

Installation of Gitana is achieved by executing the setup script.
```
$> cd <...>/Gitana
$> python setup.py build
$> python setup.py install
```
   
## How to use Gitana

Gitana is developed and tested on Windows, thus the user mileage in other platforms may vary.
Nevertheless, Gitana has been successfully executed on Linux (i.e., all its exporters and Git, GitHub, StackOverflow, Bugzilla importers).

### Data gathering from an Eclipse project and report generation

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
    
    g.import_bugzilla_issue_data("papyrus_db", "papyrus", "papyrus_repo", "papyrus-bugzilla", 
                                 "https://bugs.eclipse.org/bugs/xmlrpc.cgi", "papyrus")
				 
    g.import_eclipse_forum_data("papyrus_db", "papyrus", "papyrus-forum", 
                                "https://www.eclipse.org/forums/index.php/f/121/")
				
    g.import_stackoverflow_data("papyrus_db", "papyrus", "papyrus-so", 
                                ['YOUR-TOKEN-1', 'YOUR-TOKEN-2', ...])
				
    g.extract_dependency_relations("papyrus_db", "papyrus", "papyrus_repo", 
                                   "...\\Desktop\\org.eclipse.papyrus")
	
    g.export_graph("papyrus_db", "./graph.json", "./graph.gexf")
    g.export_activity_report("papyrus_db", "./report.json", "./report.html")
	
if __name__ == "__main__":
    main()
```

### Data gathering from a GitHub project

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
	
GH_TOKENS = ['your-token-1',
             'your-token-2',
             '...']

def main():
    g = Gitana(CONFIG, None)
    g.delete_previous_logs()
    g.init_db("db_2048")
    g.create_project("db_2048", "2048")
    
    g.import_git_data("db_2048", "2048", "repo_2048", 
                      "C:\\Users\\atlanmod\\Desktop\\oss\\ants-work\\github-repos\\2048", 
		      import_type=2)
		      
    g.import_github_issue_data("db_2048", "2048", "repo_2048", "2048_it", 
                               "gabrielecirulli/2048", GH_TOKENS)

if __name__ == "__main__":
    main()
```

## Gitana application(s)

- Assessing the bus factor of git repositories (https://github.com/SOM-Research/busfactor).
- Gamification of OSS projects (http://som-research.uoc.edu/tools/papygamus/)

## Publications
- V. Cosentino, J. L. Cánovas Izquierdo, J. Cabot, Gitana: A SQL-Based Git Repository Inspector, in: ER conf., 2015, pp. 329–343.
- V. Cosentino, J. L. Cánovas Izquierdo, J. Cabot, Assessing the bus factor of git repositories, in: SANER conf., 2015, pp. 499–503.
- J. L. Cánovas Izquierdo, V. Cosentino, J. Cabot, An Empirical Study on the Maturity of the Eclipse Modeling Ecosystem, in: MODELS conf., 2017, p. in press.
- V. Cosentino, J. L. Cánovas Izquierdo, J. Cabot, Gitana: a Software Project Inspector. Science of Computer Programming, Vol. 153, pp. 30–33.
