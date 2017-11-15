Introduction
============

Software development projects are notoriously complex and difficult to deal with. Several support tools such as issue
trackers, instant messaging services and Version Control Systems (VCSs) have been introduced in the past decades
to ease development activities. While such tools efficiently track the evolution of a given aspect of the project (e.g., bug
reports), they provide just a partial view of the project and lack of advanced querying support and data integration
mechanisms between them to enable a complete project analysis. Gitana provides a conceptual schema
(CS) to model the activity around a software project and an approach that, given a set of heterogeneous data sources
(e.g., VCSs, issue trackers and forums), export their data to a relational database derived from the CS in order to:

(1) promote a shared place to perform cross-cutting analysis on the project data,

(2) enable users to write ad-hoc queries using standard SQL syntax, and

(3) support diverse kinds of data analysis.

To ensure efficiency, our approach comes with an incremental propagation mechanism that refreshes the database content
with the latest modifications available on the data sources.


Requirements
------------
Gitana is developed on Windows 7 and it relies on:

	`Git 2.9.3 <https://git-scm.com/downloads>`_
	
	`MySQL Server 5.6 <http://dev.mysql.com/downloads/installer/>`_
	
	`Python 2.7.6 <https://www.python.org/downloads/windows/>`_

Python and pip package manager can be set to be executed from Windows command line by adding to the Path environment variable
the paths where Python and its scripts are installed. By default, these paths are:

.. code-block:: bash
	
	C:\Python27
	C:\Python27\Scripts


Installation
------------
Installation of Gitana is achieved by executing the setup script.

.. code-block:: bash

    $> cd <...>/Gitana
    $> python setup.py build
    $> python setup.py install


Licensing
--------------------
Gitana is distributed under the MIT License (https://opensource.org/licenses/MIT)

How to use Gitana
-----------------
.. code-block:: python

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

        # import
        g.import_git_data("papyrus_db", "papyrus", "papyrus_repo",
                          "...\\Desktop\\org.eclipse.papyrus")
        g.import_bugzilla_issue_data("papyrus_db", "papyrus", "papyrus_repo",
                                     "bugzilla-papyrus",
                                     "https://bugs.eclipse.org/bugs/xmlrpc.cgi",
                                     "papyrus")
        g.import_eclipse_forum_data("papyrus_db", "papyrus", "papyrus-forum",
                                    "https://www.eclipse.org/forums/index.php/f/121/")
        g.import_stackoverflow_data("papyrus_db", "papyrus", "papyrus-so",
                                    ['YOUR-TOKEN-1', 'YOUR-TOKEN-2', ...])
        g.extract_dependency_relations("papyrus_db", "papyrus", "papyrus_repo",
                                       "...\\Desktop\\org.eclipse.papyrus")

        # export
        g.export_graph("papyrus_db", "./graph.json", "./graph.gexf")
        g.export_activity_report("papyrus_db",
        "./report.json", "./report.html")

        if __name__ == "__main__":
            main()

