import mock
import pytest
from botocore.exceptions import ClientError

from twindb_infrastructure.providers.aws import launch_ec2_instance, AwsError


@mock.patch('twindb_infrastructure.providers.aws.boto3')
def test_launch_ec2_instance_client_aws_exception(mock_boto3):
    mock_client = mock.Mock()
    mock_boto3.client.return_value = mock_client
    mock_boto3.client.side_effect = ClientError({'Error': {'Code': '404', 'Message': 'Not Found'}}, [])

    with pytest.raises(AwsError):
        launch_ec2_instance({}, 'bar')


@mock.patch('twindb_infrastructure.providers.aws.boto3')
def test_launch_ec2_instance_run_instances_exception(mock_boto3):
    mock_client = mock.Mock()
    mock_boto3.client.return_value = mock_client
    instance_profile = {
        'ImageId': '',
        'InstanceType': '',
        'KeyName': '',
        'SubnetId': '',
        'SecurityGroupIds': [],
        'RootVolumeSize': 0,
        'MinCount': 1,
        'MaxCount': 1,
        'BlockDeviceMappings': [
            {
                'DeviceName': 'Such name',
                'VolumeSize': 0,
                'VolumeType': 'such type'
            }
        ],
    }
    mock_client.run_instances.side_effect = ClientError({'Error': {'Code': '404', 'Message': 'Not Found'}}, [])

    with pytest.raises(AwsError):
        launch_ec2_instance(instance_profile)


@mock.patch('twindb_infrastructure.providers.aws.wait_sshd')
@mock.patch('twindb_infrastructure.providers.aws.get_instance_public_ip')
@mock.patch('twindb_infrastructure.providers.aws.get_instance_state')
@mock.patch('twindb_infrastructure.providers.aws.boto3')
def test_calls_with_srcdst_check(mock_boto3,
                                 mock_get_instance_state,
                                 mock_get_instance_public_ip,
                                 mock_wait_sshd):

    mock_wait_sshd.return_value = True
    mock_get_instance_public_ip.return_value = 'some ip'
    mock_get_instance_state.return_value = 'running'
    mock_client = mock.Mock()
    mock_boto3.client.return_value = mock_client

    response = {
        'Instances': [
            {
                'InstanceId': 'foo'
            }
        ]
    }
    mock_client.run_instances.return_value = response
    instance_profile = {
        'ImageId': '',
        'InstanceType': '',
        'KeyName': '',
        'SubnetId': '',
        'SecurityGroupIds': [],
        'RootVolumeSize': 0,
        'MinCount': 1,
        'MaxCount': 1,
        'UserName': 'centos',
        'SourceDestCheck': False,
    }
    instance_id = launch_ec2_instance(instance_profile)

    mock_client.modify_instance_attribute.assert_called_once_with(
        SourceDestCheck={
            'Value': False
        },
        InstanceId=instance_id
    )



