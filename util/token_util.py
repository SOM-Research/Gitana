#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'valerio cosentino'

import time


class TokenUtil():

    def get_requests_left(self, token):
        try:
            left = token.requests_left
        except:
            left = None

        if not left:
            try:
                left = token.rate_limiting[0]
            except:
                left = None

        if left:
            check = left > 0
        else:
            check = False

        return check

    def is_usuable(self, token):
        try:
            check = self.get_requests_left(token)
        except:
            check = True

        return check

    def wait_is_usable(self, token):
        while True:
            if self.is_usuable(token) > 0:
                break
            time.sleep(5)
