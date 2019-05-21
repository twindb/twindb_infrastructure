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
