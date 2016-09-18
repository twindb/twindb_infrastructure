import pytest
import random
import string

from twindb_infrastructure.providers.aws import connection, network

AWS_ACCESS_KEY_LENGTH = 20
AWS_SECRET_KEY_LENGTH = 40


@pytest.fixture(scope='module')
def aws_access_key_id():
    return generate_random_string(AWS_ACCESS_KEY_LENGTH)


@pytest.fixture(scope='module')
def aws_secret_access_key():
    return generate_random_string(AWS_SECRET_KEY_LENGTH)


@pytest.fixture(scope='module')
def aws_region():
    return connection.US_EAST_1


@pytest.fixture(scope='module')
def aws_zone(aws_region):
    return '%sa' % aws_region


@pytest.fixture(scope='module')
def aws_connection(aws_access_key_id, aws_secret_access_key, aws_region):
    conn = connection.AWSConnection(aws_access_key_id, aws_secret_access_key, aws_region)
    return conn.get_connection()


def generate_random_string(string_length):
    return ''.join([random.choice(string.ascii_letters + string.digits) for n in xrange(string_length)])
