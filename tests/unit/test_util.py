import pytest

from twindb_infrastructure.config.config import ConfigException
from twindb_infrastructure.util import parse_config, domainname


def test_parse_config_raises_config_exception():
    with pytest.raises(ConfigException):
        parse_config('/foo/bar')


@pytest.mark.parametrize('host, domain', [
    (
        'www.google.com',
        'google.com'
    ),
    (
        'www.google.com.',
        'google.com.'
    )
])
def test_domainname(host, domain):
    assert domainname(host) == domain
