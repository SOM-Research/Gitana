#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'valerio cosentino'

import time


class TokenUtil():
    """
    This class provides token utilities
    """

    GITHUB_TYPE = "github"
    STACKOVERFLOW_TYPE = "stackoverflow"
    WAITING_TIME = 4000

    def __init__(self, logger, type):
        """
        :type logger: Object
        :param logger: logger

        :type type: str
        :param type: token type (github, stackoverflow, etc.)
        """
        self._logger = logger
        self._type = type

    def _github_requests_left(self, token):
        # gets github token requests left
        left = None
        try:
            left = token.rate_limiting[0]
        except:
            self._logger.error("TokenUtil, requests left not retrieved for GitHub token")

        return left

    def _stackoverflow_requests_left(self, token):
        # gets stackoverflow token requests left
        left = None
        try:
            if token.throttle_stop:
                left = 0
            else:
                try:
                    left = token.requests_left
                except:
                    left = 100
        except:
            self._logger.error("TokenUtil, requests left not retrieved for Stackoverflow token")

        return left

    def _get_requests_left(self, token):
        # gets token requests left
        left = None
        if self._type == TokenUtil.GITHUB_TYPE:
            left = self._github_requests_left(token)
        elif self._type == TokenUtil.STACKOVERFLOW_TYPE:
            left = self._stackoverflow_requests_left(token)

        return left

    def _is_usuable(self, token):
        # checks that a token has requests left
        left = self._get_requests_left(token)
        if left:
            check = left > 50
        else:
            check = False

        return check

    def wait_is_usable(self, token):
        """
        wait until a token has requests available

        :type token: str
        :param token: data source API token
        """
        if not self._is_usuable(token):
            self._logger.warning("Token expired, stand by for " + str(TokenUtil.WAITING_TIME) + " seconds")
            time.sleep(TokenUtil.WAITING_TIME)
