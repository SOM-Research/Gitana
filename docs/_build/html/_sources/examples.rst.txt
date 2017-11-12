Examples
========

Below you can find some examples to import and export data using Gitana.
Additional examples can be found in the `test`_  folder

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

        g.init_db("papyrus_db")
        g.create_project("papyrus_db", "papyrus")

        g.import_git_data("papyrus_db", "papyrus", "papyrus_repo",
                          "...\\Desktop\\org.eclipse.papyrus",
                          references=["0.7.0"])
        g.import_bugzilla_issue_data("papyrus_db", "papyrus", "papyrus_repo",
                                     "bugzilla-papyrus",
                                     "https://bugs.eclipse.org/bugs/xmlrpc.cgi", "papyrus")
        g.import_eclipse_forum_data("papyrus_db", "papyrus", "papyrus-forum",
                                    "https://www.eclipse.org/forums/index.php/f/121/")
        g.import_stackoverflow_data("papyrus_db", "papyrus", "papyrus-so",
                                    ['YOUR-TOKEN-1', 'YOUR-TOKEN-2', ...])
        g.extract_dependency_relations("papyrus_db", "papyrus", "papyrus_repo",
                                       "...\\Desktop\\org.eclipse.papyrus")

    if __name__ == "__main__":
        main()

Graph Exporter
--------------

.. code-block:: json

    {"graph":
        {"name": "users-on-issues",
         "params": {
         "project": "papyrus",
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
        g.export_graph("papyrus_db", "./graph.json", "./graph.gexf")

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
                                    "measures": ["#issues-open",
                                                 "#issues-closed",
                                                 "#issue-tracker-users"]},
         "forum_activity": {"names": ["papyrus-eclipse", "papyrus-stackoverflow"],
                            "measures": ["#messages",
                                         "#forum-users",
                                         "#new-topics",
                                         "#active-topics"]}
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
        g.export_activity_report("papyrus_db",
                                 "./report.json", "./report.html")

    if __name__ == "__main__":
        main()