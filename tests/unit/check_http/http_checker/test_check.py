import mock
import pytest
from requests import RequestException

from twindb_infrastructure.check_http import HttpChecker, CheckHttpResponse, \
    NAGIOS_EXIT_CRITICAL, NAGIOS_EXIT_OK
from twindb_infrastructure.loader import Loader


def test_check_critical():
    ch = HttpChecker(
        critical_load_time=1
    )
    mock_loader = mock.Mock()
    mock_loader.load_time = 2.0
    resp = ch.check(
        mock_loader,
        CheckHttpResponse
    )
    assert resp.nagios_code == NAGIOS_EXIT_CRITICAL
    assert resp.http_code == 503


@pytest.mark.parametrize(
    'actual_title, title_regexp, nagios_code, http_code',
    [
        (
            'foo', 'foo', NAGIOS_EXIT_OK, 200
        ),
        (
            'foo bar', 'foo$', NAGIOS_EXIT_CRITICAL, 503
        )
    ]
)
def test_check_title_regexp(actual_title, title_regexp, nagios_code, http_code):
    ch = HttpChecker(
        title_regexp=title_regexp
    )
    mock_loader = mock.Mock()
    mock_loader.title = actual_title
    resp = ch.check(
        mock_loader,
        CheckHttpResponse
    )
    assert resp.nagios_code == nagios_code
    assert resp.http_code == http_code


@mock.patch.object(Loader, '_get_tag')
def test_check_on_exception(mock_get_tag):
    ch = HttpChecker(
        title_regexp='foo'
    )
    mock_get_tag.side_effect = RequestException
    resp = ch.check(
        Loader('foo-url'),
        CheckHttpResponse
    )
    assert resp.nagios_code == NAGIOS_EXIT_CRITICAL
    assert resp.http_code == 503
