#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'valerio cosentino'

from gitana import Gitana

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
    g.init_db("papyrus_db_test")

    g.create_project("papyrus_db_test", "papyrus")
    g.import_stackoverflow_data("papyrus_db_test", "papyrus", "papyrus", None, False, ['IFco1Gh5EJ*U)ZY5)16ZKQ(('])

if __name__ == "__main__":
    main()