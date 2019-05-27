"""twindb-monitoring CLI module."""
import click

from twindb_infrastructure.check_http import \
    HttpChecker, CheckHttpResponse, CheckResponse
from twindb_infrastructure.loader import Loader


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
@click.option(
    '--http-server',
    help='Run an HTTP server that reports the check result',
    is_flag=True,
    default=False
)
@click.option(
    '--http-port',
    help='Bind the HTTP server to this TCP port',
    type=click.INT,
    default=8080,
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
               http_server,
               http_port
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
    loader = Loader(
        url,
        timeout=timeout,
        host=host,
        protocol=protocol
    )
    checker = HttpChecker(
        critical_load_time=critical,
        warning_load_time=warning,
        title=title,
        title_regexp=title_regexp,
        body_regexp=body_regexp
    )

    if http_server:
        checker.start_server(http_port, loader)

    else:
        response = checker.check(
            loader,
            CheckHttpResponse if http else CheckResponse
        )
        print(response)
        exit(response.nagios_code)
