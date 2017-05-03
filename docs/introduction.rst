Introduction
============

Software development projects are notoriously complex and difficult to deal with. Several support tools such as issue
trackers, instant messaging services and Version Control Systems (VCSs) have been introduced in the past decades
to ease development activities. While such tools efficiently track the evolution of a given aspect of the project (e.g., bug
reports), they provide just a partial view of the project and lack of advanced querying support and data integration
mechanisms between them to enable a complete project analysis. In this paper, we propose a conceptual schema
(CS) to model the activity around a software project and an approach that, given a set of heterogeneous data sources
(e.g., VCSs, issue trackers and forums), export their data to a relational database derived from the CS in order to (1)
promote a shared place to perform cross-cutting analysis on the project data, (2) enable users to write ad-hoc queries
using standard SQL syntax, and (3) support diverse kinds of data analysis. To ensure efficiency, our approach comes
with an incremental propagation mechanism that refreshes the database content with the latest modifications available
on the data sources.


Download and install
--------------------
After installing MySQL Server and Python 2.7.6, execute the setup.py script