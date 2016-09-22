__author__ = 'valerio cosentino'

import pip

DEPENDENCIES = ['networkx', 'mysql-connector', 'gitpython', 'python-bugzilla', 'pygithub']


def main():
    for d in DEPENDENCIES:
        install(d)


def install(package):
    pip.main(['install', package])


if __name__ == '__main__':
    main()
