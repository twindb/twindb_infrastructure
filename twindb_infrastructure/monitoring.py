"""twindb-monitoring CLI module."""
import re
import time

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
def check_http(url,
               warning,
               critical,
               timeout,
               title,
               title_regexp,
               body_regexp
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
    start_time = time.time()
    try:
        loader = Loader(url, timeout=timeout)
        assert loader.title
        finish_time = time.time()
        load_time = finish_time - start_time

        if critical is not None:
            if load_time > critical:
                print(
                    'CRITICAL - %s: load time %f seconds more than %f'
                    % (url, load_time, critical)
                )
                exit(NAGIOS_EXIT_CRITICAL)

        if warning is not None:
            if load_time > warning:
                print(
                    'WARNING - %s: load time %f seconds more than %f'
                    % (url, load_time, critical)
                )
                exit(NAGIOS_EXIT_WARNING)

        if title and loader.title != title:
            print(
                "CRITICAL - %s: Expected title %s. Actual title '%s'"
                % (url, title, loader.title)
            )
            exit(NAGIOS_EXIT_CRITICAL)

        if title_regexp and re.match(title_regexp, loader.title) is None:
            print(
                "CRITICAL - %s: Title '%s' is expected to match regexp '%s'"
                % (url, loader.title, title_regexp)
            )
            exit(NAGIOS_EXIT_CRITICAL)

        if body_regexp and re.match(body_regexp, loader.body) is None:
            print(
                "CRITICAL - %s: Body '%s' is expected to match regexp '%s'"
                % (url, loader.body, body_regexp)
            )
            exit(NAGIOS_EXIT_CRITICAL)

    except RequestException as err:
        print(
            "UNKNOWN - %s" % err
        )
        exit(NAGIOS_EXIT_UNKNOWN)

    print('OK')
    exit(NAGIOS_EXIT_OK)
