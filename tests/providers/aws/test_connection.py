import boto3
from botocore.session import Session
import pytest

from twindb_infrastructure.providers.aws import connection


def test__aws_connection_object_can_be_created_with_valid_region(aws_access_key_id, aws_secret_access_key, aws_region):
    conn = connection.AWSConnection(aws_access_key_id, aws_secret_access_key, aws_region)

    assert conn.region == connection.US_EAST_1


def test__aws_connection_object_creation_fails_for_invalid_region(aws_access_key_id, aws_secret_access_key):
    with pytest.raises(ValueError):
        connection.AWSConnection(aws_access_key_id, aws_secret_access_key, 'invalid-region')


def test__get_connection_returns_boto3_session(aws_access_key_id, aws_secret_access_key, aws_region, mocker):
    conn = connection.AWSConnection(aws_access_key_id, aws_secret_access_key, aws_region)

    set_credentials_mock = mocker.patch.object(Session, 'set_credentials')
    set_config_variable_mock = mocker.patch.object(Session, 'set_config_variable')

    boto3_session = conn.get_connection()

    set_credentials_mock.assert_called_once_with(aws_access_key_id, aws_secret_access_key, None)
    set_config_variable_mock.assert_called_once_with('region', aws_region)

    assert isinstance(boto3_session, boto3.Session)
