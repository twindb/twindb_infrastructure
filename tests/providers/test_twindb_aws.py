from boto3.exceptions import ResourceNotExistsError, UnknownAPIVersionError
from botocore.exceptions import ClientError
from click.testing import CliRunner
import mock
import pytest
from twindb_infrastructure import twindb_aws
from twindb_infrastructure.config.config import Config, ConfigException
from twindb_infrastructure.providers.aws import start_instance, terminate_instance, stop_instance, ec2_describe_instance, \
    AwsError, get_instance_state, get_instance_private_ip, get_instance_public_ip, add_name_tag, associate_address, \
    launch_ec2_instance
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
def test_start_instance_resource_exception(mock_boto3):
    mock_boto3.resource.side_effect = ResourceNotExistsError(mock.Mock(), 'error', '')
    assert not start_instance('foo-bar')


@mock.patch('twindb_infrastructure.providers.aws.boto3')
def test_start_instance_api_exception(mock_boto3):
    mock_boto3.resource.side_effect = UnknownAPIVersionError(mock.Mock(), 'error', '')
    assert not start_instance('foo-bar')


@mock.patch('twindb_infrastructure.providers.aws.boto3')
def test_start_instance_exception(mock_boto3):
    mock_ec2 = mock.Mock()
    mock_boto3.resource.return_value = mock_ec2
    mock_instance = mock.Mock()
    mock_ec2.instances.filter.return_value = mock_instance
    mock_instance.start.side_effect = ClientError({'Error': {'Code': '404', 'Message': 'Not Found'}}, [])
    assert not start_instance('foo-bar')


@mock.patch('twindb_infrastructure.providers.aws.boto3')
def test_start_instance_filter_exception(mock_boto3):
    mock_ec2 = mock.Mock()
    mock_boto3.resource.return_value = mock_ec2
    mock_ec2.instances.filter.side_effect = ClientError({'Error': {'Code': '404', 'Message': 'Not Found'}}, [])
    assert not start_instance('foo-bar')


@mock.patch('twindb_infrastructure.providers.aws.boto3')
def test_stop_instance_resource_exception(mock_boto3):
    mock_boto3.resource.side_effect = ResourceNotExistsError(mock.Mock(), 'error', '')
    assert not stop_instance('foo-bar')


@mock.patch('twindb_infrastructure.providers.aws.boto3')
def test_stop_instance_api_exception(mock_boto3):
    mock_boto3.resource.side_effect = UnknownAPIVersionError(mock.Mock(), 'error', '')
    assert not stop_instance('foo-bar')


@mock.patch('twindb_infrastructure.providers.aws.boto3')
def test_stop_instance_exception(mock_boto3):
    mock_ec2 = mock.Mock()
    mock_boto3.resource.return_value = mock_ec2
    mock_instance = mock.Mock()
    mock_ec2.instances.filter.return_value = mock_instance
    mock_instance.stop.side_effect = ClientError({'Error': {'Code': '404', 'Message': 'Not Found'}}, [])
    assert not stop_instance('foo-bar')


@mock.patch('twindb_infrastructure.providers.aws.boto3')
def test_stop_instance_filter_exception(mock_boto3):
    mock_ec2 = mock.Mock()
    mock_boto3.resource.return_value = mock_ec2
    mock_ec2.instances.filter.side_effect = ClientError({'Error': {'Code': '404', 'Message': 'Not Found'}}, [])
    assert not stop_instance('foo-bar')


@mock.patch('twindb_infrastructure.providers.aws.boto3')
def test_term_instance_resource_exception(mock_boto3):
    mock_boto3.resource.side_effect = ResourceNotExistsError(mock.Mock(), 'error', '')
    assert not terminate_instance('foo-bar')


@mock.patch('twindb_infrastructure.providers.aws.boto3')
def test_term_instance_api_exception(mock_boto3):
    mock_boto3.resource.side_effect = UnknownAPIVersionError(mock.Mock(), 'error', '')
    assert not terminate_instance('foo-bar')


@mock.patch('twindb_infrastructure.providers.aws.boto3')
def test_term_instance_exception(mock_boto3):
    mock_ec2 = mock.Mock()
    mock_boto3.resource.return_value = mock_ec2
    mock_instance = mock.Mock()
    mock_ec2.instances.filter.return_value = mock_instance
    mock_instance.terminate.side_effect = ClientError({'Error': {'Code': '404', 'Message': 'Not Found'}}, [])
    assert not terminate_instance('foo-bar')


@mock.patch('twindb_infrastructure.providers.aws.boto3')
def test_term_instance_filter_exception(mock_boto3):
    mock_ec2 = mock.Mock()
    mock_boto3.resource.return_value = mock_ec2
    mock_ec2.instances.filter.side_effect = ClientError({'Error': {'Code': '404', 'Message': 'Not Found'}}, [])
    assert not terminate_instance('foo-bar')


@mock.patch('twindb_infrastructure.providers.aws.boto3')
def test_ec2_describe_instance(mock_boto3):
    mock_ec2 = mock.Mock()
    mock_boto3.client.return_value = mock_ec2

    ec2_describe_instance('foo')
    mock_ec2.describe_instances.assert_called_once_with(InstanceIds=['foo'])


@mock.patch('twindb_infrastructure.providers.aws.boto3')
def test_ec2_describe_instance_aws_error_on_client_error(mock_boto3):
    mock_ec2 = mock.Mock()
    mock_boto3.client.return_value = mock_ec2
    mock_ec2.describe_instances.side_effect = ClientError({'Error': {'Code': '404', 'Message': 'Not Found'}}, [])

    with pytest.raises(AwsError):
        ec2_describe_instance('foo')


@mock.patch('twindb_infrastructure.providers.aws.ec2_describe_instance')
def test_get_instance_state(mock_describe):
    get_instance_state('foo')
    mock_describe.assert_called_once_with('foo')


@mock.patch('twindb_infrastructure.providers.aws.ec2_describe_instance')
def test_get_instance_state_aws_exception(mock_describe):
    mock_describe.side_effect = AwsError('AwsError exception')
    with pytest.raises(AwsError):
        get_instance_state('foo')


@mock.patch('twindb_infrastructure.providers.aws.ec2_describe_instance')
def test_get_instance_private_ip(mock_describe):
    get_instance_private_ip('foo')
    mock_describe.assert_called_once_with('foo')


@mock.patch('twindb_infrastructure.providers.aws.ec2_describe_instance')
def test_get_instance_private_ip_aws_exception(mock_describe):
    mock_describe.side_effect = AwsError('AwsError exception')
    with pytest.raises(AwsError):
        get_instance_private_ip('foo')


@mock.patch('twindb_infrastructure.providers.aws.ec2_describe_instance')
def test_get_instance_public_ip(mock_describe):
    get_instance_public_ip('foo')
    mock_describe.assert_called_once_with('foo')


@mock.patch('twindb_infrastructure.providers.aws.ec2_describe_instance')
def test_get_instance_public_ip_aws_exception(mock_describe):
    mock_describe.side_effect = AwsError('AwsError exception')
    with pytest.raises(AwsError):
        get_instance_public_ip('foo')


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
def test_add_name_tag(mock_boto3, response, expected_code):
    mock_client = mock.Mock()
    mock_boto3.client.return_value = mock_client
    mock_client.create_tags.return_value = response
    assert add_name_tag('foo', 'bar') == expected_code
    mock_client.create_tags.assert_called_once_with(
        Resources=['foo'],
        Tags=[
            {
                'Key': 'Name',
                'Value': 'bar'
            }
        ]
    )
    mock_boto3.client.assert_called_once_with('ec2')


@mock.patch('twindb_infrastructure.providers.aws.boto3')
def test_add_name_tag_exception(mock_boto3):
    mock_client = mock.Mock()
    mock_boto3.client.return_value = mock_client
    mock_boto3.client.side_effect = ClientError({'Error': {'Code': '404', 'Message': 'Not Found'}}, [])
    with pytest.raises(AwsError):
        add_name_tag('foo', 'bar')


@mock.patch('twindb_infrastructure.providers.aws.boto3')
def test_add_name_tag_value_exception(mock_boto3):
    mock_client = mock.Mock()
    mock_boto3.client.return_value = mock_client
    mock_client.create_tags.side_effect = ValueError

    with pytest.raises(AwsError):
        add_name_tag('foo', 'bar')


@mock.patch('twindb_infrastructure.providers.aws.boto3')
def test_associate_address(mock_boto3):
    mock_client = mock.Mock()
    mock_boto3.client.return_value = mock_client
    associate_address('foo', 'bar', 'bah')
    mock_boto3.client.assert_called_once_with('ec2')
    mock_client.associate_address.assert_called_once()


def test_associate_address_no_params():
    assert not associate_address('foo')


@mock.patch('twindb_infrastructure.providers.aws.boto3')
def test_associate_address_ec2_exception(mock_boto3):
    mock_client = mock.Mock()
    mock_boto3.client.return_value = mock_client
    mock_boto3.client.side_effect = ClientError({'Error': {'Code': '404', 'Message': 'Not Found'}}, [])

    with pytest.raises(AwsError):
        associate_address('foo', 'bar', 'bah')


@mock.patch('twindb_infrastructure.providers.aws.boto3')
def test_associate_address_address_exception(mock_boto3):
    mock_client = mock.Mock()
    mock_boto3.client.return_value = mock_client
    mock_client.associate_address.side_effect = ClientError({'Error': {'Code': '404', 'Message': 'Not Found'}}, [])

    with pytest.raises(AwsError):
        associate_address('foo', 'bar', 'bah')


@mock.patch('twindb_infrastructure.providers.aws.boto3')
def test_ec2_instance_client_aws_exception(mock_boto3):
    mock_client = mock.Mock()
    mock_boto3.client.return_value = mock_client
    mock_boto3.client.side_effect = ClientError({'Error': {'Code': '404', 'Message': 'Not Found'}}, [])

    with pytest.raises(AwsError):
        launch_ec2_instance({}, 'bar')
