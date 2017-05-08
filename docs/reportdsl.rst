Report Exporter
===============

The information stored in the Gitana database can be used to create activity reports.
The export process is driven by a Domain Specific Language (DSL), which relies on a set of parameterizable SQL `queries`_ 
(as similarly done for the graph exporter) and allows to generate tunable HTML reports. Depending on the user’s needs, the report can focus on the project activity over different tools (e.g., repository and issue trackers) according
to a given time dimension such as the current week, month or year. 

A Report Exporter DSL instance requires the name of the project, a time span as well as the names of the tools and the related list of measures to be included in the activity report. 
This information is then used to generate a set of SQL queries, one for each measure, based on the predefined query templates available in Gitana.

The figure below shows an example of report exporter. As can be seen, the name of each measure is used to identify the predefined query to be parameterized (see
#messages measure). Then, the project name, time span and names of the tools (see forums attribute) are processed to derive the corresponding identifiers and
time information (see after date, and interval), which are then set in the SQL query as similarly presented for the Graph exporter. It is worth noting 
how the time dimension (e.g., current year) for a specific measure in the report is automatically calculated by relying on where and group by conditions. Finally,
the data returned by each query is used to generate charts, which are embedded in the HTML report.

.. image:: imgs/report-exporter-2.svg

The DSL
-------
The DSL is defined using the JSON format. Below, the DSL instance template with the current exportable measures is shown. 

.. code-block:: json

	{"report":
		{"project": "NAME-OF-THE-PROJECT",
		 "time_span": "this_week|this_month|this_year",
		 "repo_activity": 
						{"names": ["NAME-OF-THE-REPO-1", "NAME-OF-THE-REPO-2", "..."],
						 "measures": ["#commits", "#repo-users"]},
		 "issue_tracker_activity": 
						{"names": ["NAME-OF-THE-ISSUE-TRACKER-1", "NAME-OF-THE-ISSUE-TRACKER-2", "..."],
						 "measures": ["#issues-open", "#issues-closed", "#issue-tracker-users"]},
		 "forum_activity": 
						{"names": ["NAME-OF-THE-FORUM-1", "NAME-OF-THE-FORUM-2", "..."],
						"measures": ["#messages", "#forum-users", "#new-topics", "#active-topics"]}
		}
	}

.. _queries: https://github.com/SOM-Research/Gitana/blob/master/exporters/resources/queries.json