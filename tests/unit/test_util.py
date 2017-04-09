import pytest

from twindb_infrastructure.config.config import ConfigException
from twindb_infrastructure.util import parse_config


def test_parse_config_raises_config_exception():
    with pytest.raises(ConfigException):
        parse_config('/foo/bar')
