"""twindb-monitoring CLI module."""
import re
import time
from warnings import filterwarnings

import click
from requests import RequestException

from twindb_infrastructure.loader import Loader

NAGIOS_EXIT_OK = 0
NAGIOS_EXIT_WARNING = 1
NAGIOS_EXIT_CRITICAL = 2
NAGIOS_EXIT_UNKNOWN = 3


@click.group()
@click.version_option()
def main():
    pass


@main.command()
@click.argument('url')
@click.option(
    '-w', '--warning',
    help='Response time to result in warning status (seconds)',
    type=click.FLOAT,
)
@click.option(
    '-c', '--critical',
    help='Response time to result in critical status (seconds)',
    type=click.FLOAT,
)
@click.option(
    '-t', '--timeout',
    help='Seconds before connection times out',
    default=10,
    show_default=True,
    type=click.INT,
)
@click.option(
    '--title',
    help='Expect the string to be a title',
)
@click.option(
    '--title-regexp',
    help='Expect the regexp to match the title',
)
@click.option(
    '--body-regexp',
    help='Expect the regexp to match the body',
)
@click.option(
    '--http',
    help='Print result as an HTTP response',
    is_flag=True,
    default=False
)
@click.option(
    '--host',
    help='Pass this value as Host: HTTP header',
)
@click.option(
    '--protocol',
    help='This value is used for X-Forwarded-Proto header',
    default='http',
    show_default=True,
)
def check_http(url,
               warning,
               critical,
               timeout,
               title,
               title_regexp,
               body_regexp,
               http,
               host,
               protocol,
               ):
    """
    Make an HTTP(s) GET request and check response against given criteria.

    The exit code matches Nagios convention:

    \b
        - 0 - OK
        - 1 - Warning
        - 2 - Critical
        - 3 - Unknown
    """
    filterwarnings("ignore")
    start_time = time.time()
    try:
        loader = Loader(
            url,
            timeout=timeout,
            host=host,
            protocol=protocol
        )
        assert loader.title, '%s returns empty HTML title' % url
        finish_time = time.time()
        load_time = finish_time - start_time

        if critical is not None:
            if load_time > critical:
                print_response(
                    'CRITICAL - %s: load time %f seconds more than %f'
                    % (url, load_time, critical),
                    http=http, http_code=503
                )
                exit(NAGIOS_EXIT_CRITICAL)

        if warning is not None:
            if load_time > warning:
                print_response(
                    'WARNING - %s: load time %f seconds more than %f'
                    % (url, load_time, critical),
                    http=http, http_code=200
                )
                exit(NAGIOS_EXIT_WARNING)

        if title and loader.title != title:
            print_response(
                "CRITICAL - %s: Expected title %s. Actual title '%s'"
                % (url, title, loader.title),
                http=http, http_code=503
            )
            exit(NAGIOS_EXIT_CRITICAL)

        if title_regexp and re.match(title_regexp, loader.title) is None:
            print_response(
                "CRITICAL - %s: Title '%s' is expected to match regexp '%s'"
                % (url, loader.title, title_regexp),
                http=http, http_code=503
            )
            exit(NAGIOS_EXIT_CRITICAL)

        if body_regexp and re.match(body_regexp, loader.body) is None:
            print_response(
                "CRITICAL - %s: Body '%s' is expected to match regexp '%s'"
                % (url, loader.body, body_regexp),
                http=http, http_code=503
            )
            exit(NAGIOS_EXIT_CRITICAL)

    except (RequestException, AssertionError) as err:
        print_response(
            "UNKNOWN - %s" % err,
            http=http, http_code=503
        )
        exit(NAGIOS_EXIT_UNKNOWN)

    print_response('OK', http=http, http_code=200)
    exit(NAGIOS_EXIT_OK)


def print_response(msg, http=False, http_code=None):
    """
    Print response after the check.

    :param msg: Message to output to the client.
    :param http: If True the response is meant to be for an HTTP client.
    :type http: bool
    :param http_code: If it's an HTTP response use this code as a HTTP code.
    :type http_code: int
    """
    if http:
        print(
            "HTTP/1.1 {code} {short_message}".format(
                code=http_code,
                short_message="OK"
                if http_code == 200 else "Service Unavailable",
            )
        )
        print("Content-Type: text/plain; charset=UTF-8")
        print("Connection: close")
        print(
            "Content-Length: {len}".format(
                len=len(msg) + 1
            )
        )
        print("")
        print(msg)
    else:
        print(msg)
