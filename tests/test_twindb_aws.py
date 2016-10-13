from click.testing import CliRunner
import mock
import pytest
from twindb_infrastructure import twindb_aws
from twindb_infrastructure.config.config import Config, ConfigException
from twindb_infrastructure.twindb_aws import parse_config


@mock.patch.object(Config, '__init__')
def test_parse_config(mock_config):
    mock_config.return_value = None
    parse_config('foo')


@mock.patch.object(Config, '__init__')
def test_parse_config_exception(mock_config):
    mock_config.return_value = None
    mock_config.side_effect = ConfigException
    with pytest.raises(ConfigException):
        parse_config('foo')


def test_main():
    runner = CliRunner()
    result = runner.invoke(twindb_aws.main)
    assert result.exit_code == 0
