#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'valerio cosentino'

from exporter import resources
import os

BOOTSTRAP_COLUMNS = 12
CHARTS_PER_LINE = 2


class HtmlGenerator():

    def __init__(self, logger):
        self.logger = logger

    def group(self, lst, n):
        grouped = [lst[i:i+n] for i in range(0, len(lst), n)]
        last_group = grouped[-1]

        while len(last_group) < n:
            last_group.append(None)

        return grouped

    def add_head(self, project_name, html_string):
        html_string += """<head>
                    <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
                    <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.7/css/bootstrap.min.css">
                    <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.7/css/bootstrap-theme.min.css">
                    <title>Activity Report - """ + project_name + """</title>
            </head>"""
        return html_string

    def add_css(self, html_string):
        html_string += """<style>
                .jumbotron {
                    position: relative;
                    background: #000 url(\'""" + os.path.dirname(resources.__file__).replace("\\", "/") + "/jumbotron.png" + """\') center center;
                    width: 100%;
                    height: 100%;
                    background-size: cover;
                    overflow: hidden;
                    color: white;
                }
                footer {
                    margin-top: 30px;
                    padding-top: 30px;
                    bottom: 0;
                    padding-bottom: 30px;
                    background-color: #337180;
                    width: 100%;
                    height: 146px;
                    color: white;
                }
                a:link {
                    color: white;
                    text-decoration: underline;
                }
                a:visited {
                    color: white;
                    text-decoration: underline;
                }
                a:hover {
                    color: white;
                    text-decoration: underline;
                }
                a:active {
                    color: white;
                    text-decoration: underline;
                }
                .activity {
                    color: white;
                    background-color: #a8a8a8;
                    max-height: 85px;
                }
                .activity h2 {
                    vertical-align:middle;
                    margin-top:7px;
                    margin-bottom:15px;
                }

            </style>
            """

        return html_string

    def add_jumbotron(self, project_name, html_string):
        html_string += """
                <div class="jumbotron">
                  <div class="container">
                    <h1>""" + project_name + """</h1>
                  </div>
                </div>
                """

        return html_string

    def add_footer(self, html_string):
        html_string += """
                        <footer>
                          <div class="row">
                            <div class="col-md-12">
                              <p class="text-center"><small>Report generated with <a href="https://github.com/SOM-Research/Gitana">Gitana</a>.</small></p>
                            </div>
                          </div>
                        </footer>
                        """

        return html_string

    def add_activity_name(self, activity_name, html_string):
        html_string += """<div class="col-sm-12 img-rounded activity">
                                <h2><span class="label label-warning">""" + activity_name + """</span></h2>
                          </div>
                        """
        return html_string

    def add_tool_name(self, tool_name, html_string):
        html_string += """<div class="col-sm-12">
                                <h3><span class="label label-warning">""" + tool_name + """</span></h3>
                          </div>
                        """
        return html_string

    def create(self, project_name, activity2charts):
        html_string = """<!DOCTYPE html><html>"""
        html_string = self.add_head(project_name, html_string)
        html_string = self.add_css(html_string)
        html_string += """<body>"""
        html_string = self.add_jumbotron(project_name, html_string)
        html_string += """<div class="container">
                        """
        for a in activity2charts:
            html_string += """<div class="row">
                            """
            html_string = self.add_activity_name(a.title(), html_string)
            tool2charts = activity2charts.get(a)
            tool_names = tool2charts.keys()

            for tool_name in tool_names:
                html_string += """<div class="row">
                                """
                html_string = self.add_tool_name(tool_name, html_string)
                html_string += """<div class="container box-charts">
                            """
                grouped_charts = self.group(tool2charts.get(tool_name), CHARTS_PER_LINE)
                for grouped_chart in grouped_charts:
                    html_string += """<div class="container">
                                    """

                    for chart in grouped_chart:
                        if not chart:
                            html_string += """<div class="col-sm-""" + str(BOOTSTRAP_COLUMNS/CHARTS_PER_LINE) + """\"></div>"""
                        else:
                            html_string += """<div class="col-sm-""" + str(BOOTSTRAP_COLUMNS/CHARTS_PER_LINE) + """\">
                                                <div>""" + chart.decode('utf-8') + """</div>
                                              </div>"""

                    html_string += """</div>
                                    """

                html_string += """</div>
                                </div>
                                """
            html_string += """</div>
                            """
        html_string += """</div>
                            """
        html_string = self.add_footer(html_string)
        html_string += """</body>
                            </html>"""
        return html_string

