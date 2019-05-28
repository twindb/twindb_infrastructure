import re
import socket
from time import sleep

from requests import RequestException

NAGIOS_EXIT_OK = 0
NAGIOS_EXIT_WARNING = 1
NAGIOS_EXIT_CRITICAL = 2
NAGIOS_EXIT_UNKNOWN = 3


class CheckResponse(object):
    def __init__(self, **kwargs):
        self._message = kwargs.get('message', 'Service unavailable')
        self._nagios_code = kwargs.get('nagios_code', NAGIOS_EXIT_UNKNOWN)

    @property
    def nagios_code(self):
        return self._nagios_code

    def __str__(self):
        return self._message


class CheckHttpResponse(CheckResponse):
    def __init__(self, **kwargs):
        super(CheckHttpResponse, self).__init__(**kwargs)
        self._http_code = kwargs.get('http_code', 503)

    @property
    def http_code(self):
        return self._http_code

    def __str__(self):
        template = "HTTP/1.1 {code} {short_message}\r\n" \
                   "Content-Type: text/plain; charset=UTF-8\r\n" \
                   "Connection: close\r\n" \
                   "Content-Length: {len}\r\n\r\n" \
                   "{msg}\r\n"
        return template.format(
            code=self._http_code,
            short_message="OK" if self._http_code == 200
            else "Service unavailable",
            len=len(self._message) + 2,
            msg=self._message
        )


class HttpChecker(object):
    __attributes = [
        'critical_load_time',
        'warning_load_time',
        'title',
        'title_regexp',
        'body_regexp'
    ]

    def __init__(self, **kwargs):
        self._body_regexp = None
        self._title_regexp = None
        self._title = None
        self._critical_load_time = None
        self._warning_load_time = None

        for attr in self.__attributes:
            setattr(
                self,
                '_%s' % attr,
                kwargs.get(attr, None)
            )

    def check(self, loader, resp_class):
        """

        :param loader:
        :type loader: Loader
        :param resp_class: What response type the method should return
        :type resp_class: class
        :return: Response
        :rtype: CheckResponse
        """
        try:
            # if load time more than critical threshold
            if self._critical_load_time \
                    and loader.load_time > self._critical_load_time:

                kwargs = {
                    'message': 'CRITICAL - %s: load time %f '
                               'seconds more than %f'
                               % (
                                   loader.url,
                                   loader.load_time,
                                   self._critical_load_time
                               ),
                    'nagios_code': NAGIOS_EXIT_CRITICAL
                }
                if resp_class == CheckHttpResponse:
                    kwargs['http_code'] = 503

                return resp_class(**kwargs)

            # if load time more than warning threshold
            if self._warning_load_time \
                    and loader.load_time > self._warning_load_time:

                kwargs = {
                    'message': 'WARNING - %s: load time %f '
                               'seconds more than %f'
                               % (
                                   loader.url,
                                   loader.load_time,
                                   self._warning_load_time
                               ),
                    'nagios_code': NAGIOS_EXIT_WARNING
                }
                if resp_class == CheckHttpResponse:
                    kwargs['http_code'] = 200

                return resp_class(**kwargs)

            # If title is different than expected
            if self._title and self._title != loader.title:
                kwargs = {
                    'message': "CRITICAL - %s: "
                               "Expected title %s. Actual title '%s'"
                               % (loader.url, self._title, loader.title),
                    'nagios_code': NAGIOS_EXIT_CRITICAL
                }
                if resp_class == CheckHttpResponse:
                    kwargs['http_code'] = 503

                return resp_class(**kwargs)

            # If title doesn't match expected regexp
            if self._title_regexp \
                    and re.match(self._title_regexp, loader.title) is None:

                kwargs = {
                    'message': "CRITICAL - %s: Title '%s' "
                               "is expected to match regexp '%s'"
                               % (loader.url, loader.title, self._title_regexp),
                    'nagios_code': NAGIOS_EXIT_CRITICAL
                }
                if resp_class == CheckHttpResponse:
                    kwargs['http_code'] = 503

                return resp_class(**kwargs)

            # If body doesn't match expected regexp
            if self._body_regexp \
                    and re.match(self._body_regexp, loader.body) is None:

                kwargs = {
                    'message': "CRITICAL - %s: Body '%s...' "
                               "is expected to match regexp '%s'"
                               % (
                                   loader.url,
                                   loader.body[0:16],
                                   self._body_regexp
                               ),
                    'nagios_code': NAGIOS_EXIT_CRITICAL
                }
                if resp_class == CheckHttpResponse:
                    kwargs['http_code'] = 503

                return resp_class(**kwargs)

            # If no checks fails respond with success
            loader.load()
            kwargs = {
                'message': "OK - %s is healthy"
                           % (
                               loader.url,
                           ),
                'nagios_code': NAGIOS_EXIT_OK
            }
            if resp_class == CheckHttpResponse:
                kwargs['http_code'] = 200

        except RequestException as err:
            kwargs = {
                'message': "CRITICAL - {url}: {err_msg}".format(
                    url=loader.url,
                    err_msg=err
                ),
                'nagios_code': NAGIOS_EXIT_CRITICAL
            }

            if resp_class == CheckHttpResponse:
                kwargs['http_code'] = 503

        return resp_class(**kwargs)

    def start_server(self, http_port, loader):
        try:
            s = socket.socket()

            while True:
                try:
                    s.bind(('', http_port))
                    break
                except socket.error as error:
                    # if socket in TIME_WAIT, sleep a bit and retry
                    if error.errno in [48, 98]:
                        sleep(5)
                    else:
                        raise
            s.listen(1)

            while True:
                c, addr = s.accept()
                response = self.check(
                    loader,
                    CheckHttpResponse
                )
                c.recv(4096)
                c.sendall(str(response))
                c.shutdown(socket.SHUT_RDWR)
                c.close()
                loader.reset()

        except KeyboardInterrupt:
            return
