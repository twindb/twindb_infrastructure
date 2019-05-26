from textwrap import dedent

import mock

from twindb_infrastructure.loader import Loader


@mock.patch('twindb_infrastructure.loader.requests')
def test_loader(mock_requests):
    mock_response = mock.Mock()
    mock_response.content = dedent(
        """
        <html>
        <title>foo</title>
        <body>bar</body>
        </html>
        """
    )
    mock_requests.get.return_value = mock_response
    loader = Loader('xxx')
    assert loader.title == 'foo'
    assert loader.body == 'bar'


@mock.patch('twindb_infrastructure.loader.requests')
def test_loader_no_redirects(mock_requests):
    loader = Loader('xxx')
    assert loader.title is None
    mock_requests.get.assert_called_once_with(
        'xxx', allow_redirects=False, timeout=10
    )


@mock.patch('twindb_infrastructure.loader.requests')
def test_loader_with_headers(mock_requests):
    loader = Loader('xxx', host='foo.bar', protocol='aaa')
    assert loader.title is None
    mock_requests.get.assert_called_once_with(
        'xxx', allow_redirects=False, timeout=10,
        headers={
            'Host': 'foo.bar',
            'X-Forwarded-Proto': 'aaa',
        }
    )
