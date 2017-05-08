Examples
========

Below you can find some examples to import and export data using Gitana. Additional examples can be found in the `test`_  folder

.. _test: https://github.com/SOM-Research/Gitana/tree/master/test

Importer
--------

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
		g = Gitana(CONFIG, None)
		g.delete_previous_logs()
		g.init_db("_papyrus_db")
		g.create_project("_papyrus_db", "papyrus")
		print "import git data"
		g.import_git_data("_papyrus_db", "papyrus", "papyrus_repo", "C:\\Users\\atlanmod\\Desktop\\eclipse-git-projects\\papyrus", None, 1, ["0.7.0"], 10)
		print "import bugzilla data"
		g.import_bugzilla_tracker_data("_papyrus_db", "papyrus", "papyrus_repo", "bugzilla-papyrus", "https://bugs.eclipse.org/bugs/xmlrpc.cgi", "papyrus", None, 10)
		print "import eclipse forum data"
		g.import_eclipse_forum_data("_papyrus_db", "papyrus", "papyrus-eclipse", "https://www.eclipse.org/forums/index.php/f/121/", None, 4)
		print "import stackoverflow data"
		g.import_stackoverflow_data("_papyrus_db", "papyrus", "papyrus-stackoverflow", "papyrus", None, ['YOUR-STACKOVERFLOW-TOKEN'])

	if __name__ == "__main__":
		main()
		
Graph Exporter
--------------

.. code-block:: json

	{"graph":
		{"name": "users-on-issues",
		 "params": {"project": "papyrus",
					"repo": "papyrus_repo",
					"issuetracker": "bugzilla-papyrus",
					"nodecolor": "random",
					"edgecolor": "black",
					"type": "undirected"}
		 }
	}

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
		g = Gitana(CONFIG, None)
		g.export_to_graph("_papyrus_db", "./graph.json", "./graph.gexf")

	if __name__ == "__main__":
		main()
		

Report Exporter
---------------

.. code-block:: json

	{"report":
		{"project": "papyrus",
		 "time_span": "this_year",
		 "repo_activity": {"names": ["papyrus_repo"],
						   "measures": ["#commits", "#repo-users"]},
		 "issue_tracker_activity": {"names": ["bugzilla-papyrus"],
									"measures": ["#issues-open", "#issues-closed", "#issue-tracker-users"]},
		 "forum_activity": {"names": ["papyrus-eclipse", "papyrus-stackoverflow"],
							"measures": ["#messages", "#forum-users", "#new-topics", "#active-topics"]}
		 }
	}

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
		g = Gitana(CONFIG, None)
		g.export_to_report("_papyrus_db", "./report.json", "./report.html")

	if __name__ == "__main__":
		main()