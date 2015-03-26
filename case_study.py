__author__ = 'atlanmod'

from gitana import Gitana

repos = [
            #('twitter', 'zipkin_t', 'C:/Users/atlanmod/Desktop/zipkin'),
            #('atlanmod', 'gila_t', 'C:/Users/atlanmod/Desktop/gila'),
            #('atlanmod', 'EMFtoCSP_t', 'C:/Users/atlanmod/Desktop/EMFtoCSP'),
            #('atlanmod', 'collaboro_t', 'C:/Users/atlanmod/Desktop/collaboro'),
            #('octopress', 'octopress_t', 'C:/Users/atlanmod/Desktop/octopress'),
            ('reddit', 'reddit_t', 'C:/Users/atlanmod/Desktop/reddit'),
            ('angularjs', 'angularjs_t', 'C:/Users/atlanmod/Desktop/angular.js'),
            ('symfony', 'symfony_t', 'C:/Users/atlanmod/Desktop/symfony')
        ]

for repo in repos:
    schema = repo[0] + "_" + repo[1]
    g = Gitana(schema)
    g.init_dbschema(schema)
    g.git2db(schema, repo[2])
    print schema + " done!"
