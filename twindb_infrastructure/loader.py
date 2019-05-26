"""Module with Loader() class"""
from HTMLParser import HTMLParser

import requests


class Loader(HTMLParser):
    def __init__(self, url, timeout=10, host=None, protocol=None):
        HTMLParser.__init__(self)
        self._url = url
        self._timeout = timeout
        self.__response = None
        self._body = None
        self._title = None
        self.__current_tag = None
        self._host = host
        self._protocol = protocol

    @property
    def body(self):
        return self._get_tag('body')

    @property
    def title(self):
        return self._get_tag('title')

    def handle_starttag(self, tag, attrs):
        self.__current_tag = tag

    def handle_endtag(self, tag):
        self.__current_tag = None

    def handle_data(self, data):
        setattr(self, '_%s' % self.__current_tag, data)

    @property
    def _response(self):
        if self.__response is None:
            kwargs = {
                'timeout': self._timeout,
                'allow_redirects': False,
            }
            headers = {}
            if self._host:
                headers['Host'] = self._host
            if self._protocol:
                headers['X-Forwarded-Proto'] = self._protocol
            if headers:
                kwargs['headers'] = headers

            resp = requests.get(self._url, **kwargs)
            resp.raise_for_status()
            self.__response = resp.content

        return self.__response

    def _get_tag(self, tag):
        if getattr(self, '_%s' % tag) is None:
            self.feed(self._response)

        return getattr(self, '_%s' % tag)
