import pytest

from twindb_infrastructure.check_http import CheckHttpResponse


@pytest.mark.parametrize('http_code, expected_response', [
    (
        503,
        "HTTP/1.1 503 Service unavailable\r\n"
        "Content-Type: text/plain; charset=UTF-8\r\n"
        "Connection: close\r\n"
        "Content-Length: 5\r\n\r\n"
        "foo\r\n"
    ),
    (
        200,
        "HTTP/1.1 200 OK\r\n"
        "Content-Type: text/plain; charset=UTF-8\r\n"
        "Connection: close\r\n"
        "Content-Length: 5\r\n\r\n"
        "foo\r\n"
    )
])
def test_str(http_code, expected_response):
    resp = CheckHttpResponse(
        message='foo',
        http_code=http_code,
        nagios_code=4
    )
    assert str(resp) == expected_response
