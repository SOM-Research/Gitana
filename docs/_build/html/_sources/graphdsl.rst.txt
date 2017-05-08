Graph Exporter
==============
The information stored in the Gitana database can be exported to support complex networks analysis using graphs. 
The export process is driven by a Domain Specific Language (DSL) able to generate different kind of graphs from a set of parameterizable SQL
`queries`_ to be executed against the Gitana database. 
The DSL is used to hide the database implementation details to the user, thus promoting independence with the database technology employed.

The Graph exporter is in charge of generating a GEXF graph from an instance of the Graph Exporter DSL. Each DSL instance requires the name
of the graph to export, some optional parameters that depend on the chosen graph, such as the name of the target project and tools (e.g., repository, issue tracker, etc.) to include in the export, and some mandatory ones like the type
of graph to export (e.g., directed or undirected) and the color of edges/nodes. These parameters are used to generate and execute the SQL queries responsible
for creating the nodes and edges of the graph based on the predefined query templates available in Gitana

The figure below shows how the parametrization is achieved for the SQL query related to the nodes of the graph users-on-issues. As can be seen, the name of the graph
is used to identify the predefined queries for nodes and edges, while the names of the parameters in the Graph Exporter DSL are used as markers in the SQL
query template. Depending on the type of the parameter (i.e., required or optional), its value is either directly replaced in the SQL query (see node-color
parameter) or first processed in order to retrieve its identifier (see project, repo and issue-tracker parameters). The data returned by both queries for nodes and
edges is processed and exported to a GEXF file.

.. image:: imgs/graph-exporter-2.svg

The DSL
-------
The DSL is defined using the JSON format. Below, the DSL instance templates for the currently exportable graphs are shown.   

.. code-block:: json

	{"graph":
		{"name": "users-on-issues",
		 "params": {"project": "NAME-OF-THE-PROJECT",
					"repo": "NAME-OF-THE-REPO",
					"issuetracker": "NAME-OF-THE-ISSUE-TRACKER",
					"nodecolor": "black|gray|white|blue|cyan|yellow|red|brown|orange|pink|purple|violet|random",
					"edgecolor": "black|gray|white|blue|cyan|yellow|red|brown|orange|pink|purple|violet|random",
					"type": "undirected|directed"}
		 }
	}

	{"graph":
		{"name": "users-on-files",
		 "params": {"project": "NAME-OF-THE-PROJECT",
					"repo": "NAME-OF-THE-REPO",
					"nodecolor": "black|gray|white|blue|cyan|yellow|red|brown|orange|pink|purple|violet|random",
					"edgecolor": "black|gray|white|blue|cyan|yellow|red|brown|orange|pink|purple|violet|random",
					"type": "undirected|directed"}
		 }
	}

	{"graph":
		{"name": "users-on-files-for-references",
		 "params": {"project": "NAME-OF-THE-PROJECT",
					"repo": "NAME-OF-THE-REPO",
					"references": "COMMA-SEPARATED-LIST-OF-REFERENCE-NAMES",
					"nodecolor": "black|gray|white|blue|cyan|yellow|red|brown|orange|pink|purple|violet|random",
					"edgecolor": "black|gray|white|blue|cyan|yellow|red|brown|orange|pink|purple|violet|random",
					"type": "undirected|directed"}
		 }
	}

.. _queries: https://github.com/SOM-Research/Gitana/blob/master/exporters/resources/queries.json


