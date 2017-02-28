from boto3.exceptions import ResourceNotExistsError, UnknownAPIVersionError
from botocore.exceptions import ClientError
from click.testing import CliRunner
import mock
import pytest
from twindb_infrastructure import twindb_aws
from twindb_infrastructure.config.config import Config, ConfigException
from twindb_infrastructure.providers.aws import start_instance, terminate_instance, stop_instance
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


@pytest.mark.parametrize('response, expected_code', [
    (
        [{
            'ResponseMetadata': {
                'HTTPStatusCode': 200
            }
        }],
        True
    ),
    (
        [{
            'ResponseMetadata': {
                'HTTPStatusCode': 404
            }
        }],
        False
    )
])
@mock.patch('twindb_infrastructure.providers.aws.boto3')
def test_start_instance(mock_boto3, response, expected_code):
    mock_ec2 = mock.Mock()
    mock_boto3.resource.return_value = mock_ec2
    mock_instance = mock.Mock()
    mock_ec2.instances.filter.return_value = mock_instance
    mock_instance.start.return_value = response
    assert start_instance('foo-bar') == expected_code
    mock_boto3.resource.assert_called_once_with('ec2')
    mock_ec2.instances.filter.assert_called_once_with(InstanceIds=['foo-bar'])
    mock_instance.start.assert_called_once()


@pytest.mark.parametrize('response, expected_code', [
    (
        [{
            'ResponseMetadata': {
                'HTTPStatusCode': 200
            }
        }],
        True
    ),
    (
        [{
            'ResponseMetadata': {
                'HTTPStatusCode': 404
            }
        }],
        False
    )
])
@mock.patch('twindb_infrastructure.providers.aws.boto3')
def test_terminate_instance(mock_boto3, response, expected_code):
    mock_ec2 = mock.Mock()
    mock_boto3.resource.return_value = mock_ec2
    mock_instance = mock.Mock()
    mock_ec2.instances.filter.return_value = mock_instance
    mock_instance.terminate.return_value = response
    assert terminate_instance('foo-bar') == expected_code
    mock_boto3.resource.assert_called_once_with('ec2')
    mock_ec2.instances.filter.assert_called_once_with(InstanceIds=['foo-bar'])
    mock_instance.terminate.assert_called_once()


@pytest.mark.parametrize('response, expected_code', [
    (
        [{
            'ResponseMetadata': {
                'HTTPStatusCode': 200
            }
        }],
        True
    ),
    (
        [{
            'ResponseMetadata': {
                'HTTPStatusCode': 404
            }
        }],
        False
    )
])
@mock.patch('twindb_infrastructure.providers.aws.boto3')
def test_stop_instance(mock_boto3, response, expected_code):
    mock_ec2 = mock.Mock()
    mock_boto3.resource.return_value = mock_ec2
    mock_instance = mock.Mock()
    mock_ec2.instances.filter.return_value = mock_instance
    mock_instance.stop.return_value = response
    assert stop_instance('foo-bar') == expected_code
    mock_boto3.resource.assert_called_once_with('ec2')
    mock_ec2.instances.filter.assert_called_once_with(InstanceIds=['foo-bar'])
    mock_instance.stop.assert_called_once()


@mock.patch('twindb_infrastructure.providers.aws.boto3')
def test_start_instance_exception(mock_boto3):
    mock_boto3.resource.side_effect = ResourceNotExistsError(mock.Mock(), 'error', '')
    assert not start_instance('foo-bar')
    mock_boto3.resource.side_effect = UnknownAPIVersionError(mock.Mock(), 'error', '')
    assert not start_instance('foo-bar')
    mock_ec2 = mock.Mock()
    mock_boto3.resource.return_value = mock_ec2
    mock_instance = mock.Mock()
    mock_ec2.instances.filter.return_value = mock_instance
    mock_ec2.instances.side_effect = ClientError
    assert not start_instance('foo-bar')


@mock.patch('twindb_infrastructure.providers.aws.boto3')
def test_stop_instance_exception(mock_boto3):
    mock_boto3.resource.side_effect = ResourceNotExistsError(mock.Mock(), 'error', '')
    assert not stop_instance('foo-bar')
    mock_boto3.resource.side_effect = UnknownAPIVersionError(mock.Mock(), 'error', '')
    assert not stop_instance('foo-bar')
    mock_ec2 = mock.Mock()
    mock_boto3.resource.return_value = mock_ec2
    mock_instance = mock.Mock()
    mock_ec2.instances.filter.return_value = mock_instance
    mock_ec2.instances.side_effect = ClientError
    assert not start_instance('foo-bar')


@mock.patch('twindb_infrastructure.providers.aws.boto3')
def test_term_instance_exception(mock_boto3):
    mock_boto3.resource.side_effect = ResourceNotExistsError(mock.Mock(), 'error', '')
    assert not terminate_instance('foo-bar')
    mock_boto3.resource.side_effect = UnknownAPIVersionError(mock.Mock(), 'error', '')
    assert not terminate_instance('foo-bar')
    mock_ec2 = mock.Mock()
    mock_boto3.resource.return_value = mock_ec2
    mock_instance = mock.Mock()
    mock_ec2.instances.filter.return_value = mock_instance
    mock_ec2.instances.side_effect = ClientError
    assert not start_instance('foo-bar')
