import pytest

from twindb_infrastructure.check_http import CheckHttpResponse


@pytest.mark.parametrize('http_code, expected_response', [
    (
        503,
        """HTTP/1.1 503 Service unavailable
Content-Type: text/plain; charset=UTF-8
Connection: close
Content-Length: 4

foo
"""
    ),
    (
        200,
        """HTTP/1.1 200 OK
Content-Type: text/plain; charset=UTF-8
Connection: close
Content-Length: 4

foo
"""
    )
])
def test_str(http_code, expected_response):
    resp = CheckHttpResponse(
        message='foo',
        http_code=http_code,
        nagios_code=4
    )
    assert str(resp) == expected_response
