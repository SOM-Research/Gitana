#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'valerio cosentino'

import time


class TokenUtil():

    def is_usuable(self, token):
        try:
            check = token.requests_left > 0
        except:
            check = True

        return check

    def wait_is_usable(self, token):
        while True:
            if self.is_usuable(token) > 0:
                break
            time.sleep(5)
