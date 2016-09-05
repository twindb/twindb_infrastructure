import mock as mock
import pytest
from twindb_infrastructure.credentials.aws_credentials import AwsCredentials
from twindb_infrastructure.credentials.cloudflare_credentials import \
    CloudFlareCredentials
from twindb_infrastructure.credentials.credentials import Credentials, \
    CredentialsException


@pytest.fixture
def config(tmpdir):
    fp = tmpdir.join('config')
    fp.write('# this is a test config')
    return fp


def test_credentials_raises_exception():
    with pytest.raises(CredentialsException):
        Credentials('aaa')


def test_credentials_init(config):
    config.write('[foo]')
    c = Credentials(str(config))
    assert c.config_path == str(config)


def test_malformed_config(config):
    config.write('aaa')
    with pytest.raises(CredentialsException):
        Credentials(str(config))


def test_empty_config(config):
    with pytest.raises(CredentialsException):
        Credentials(str(config))


def test_aws_credentials_raises_exception_if_no_aws_section(tmpdir):
    with pytest.raises(CredentialsException):
        config_file = tmpdir.join('some_config')
        config_file.write('[foo]')
        AwsCredentials(config_path=str(config_file))


def test_aws_sets_options(config):
    config.write("""
[aws]
AWS_ACCESS_KEY_ID = "foo"
AWS_SECRET_ACCESS_KEY = 'bar'
AWS_DEFAULT_REGION = 'xxx'
AWS_DEFAULT_AMI = 'yyy'
AWS_INSTANCE_USERNAME_yyy = "centos"
""")
    ac = AwsCredentials(config_path=str(config))
    assert ac.aws_access_key_id == 'foo'
    assert ac.aws_secret_access_key == 'bar'
    assert ac.aws_default_region == 'xxx'
    assert ac.aws_default_ami == 'yyy'
    assert ac.aws_instance_username['yyy'] == 'centos'


def test_cloudflare_sets_options(config):
    config.write("""
[cloudflare]
CLOUDFLARE_EMAIL = "foo"
CLOUDFLARE_AUTH_KEY = "bar"
""")
    cfc = CloudFlareCredentials(config_path=str(config))
    assert cfc.cloudflare_email == 'foo'
    assert cfc.cloudflare_auth_key == 'bar'
