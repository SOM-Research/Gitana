#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'valerio cosentino'

import time


class TokenUtil():
    GITHUB_TYPE = "github"
    STACKOVERFLOW_TYPE = "stackoverflow"
    WAITING_TIME = 1800

    def __init__(self, logger, type):
        self._logger = logger
        self._type = type

    def _github_requests_left(self, token):
        left = None
        try:
            left = token.rate_limiting[0]
        except:
            self._logger.error("TokenUtil, requests left not retrieved for GitHub token")

        return left

    def _stackoverflow_requests_left(self, token):
        left = None
        try:
            left = token.requests_left
        except:
            self._logger.error("TokenUtil, requests left not retrieved for Stackoverflow token")

        return left

    def _get_requests_left(self, token):
        left = None
        if self._type == TokenUtil.GITHUB_TYPE:
            left = self._github_requests_left(token)
        elif self._type == TokenUtil.STACKOVERFLOW_TYPE:
            left = self._stackoverflow_requests_left(token)

        return left

    def _is_usuable(self, token):
        left = self._get_requests_left(token)
        if left:
            check = left > 0
        else:
            check = False

        return check

    def wait_is_usable(self, token):
        while True:
            if self._is_usuable(token) > 0:
                break
            time.sleep(5)
            self._logger.warning("Token expired, standy for " + str(TokenUtil.WAITING_TIME) + " seconds")
