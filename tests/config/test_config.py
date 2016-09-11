import pytest
from twindb_infrastructure.config.aws_credentials import AwsCredentials
from twindb_infrastructure.config.cloudflare_credentials import \
    CloudFlareCredentials
from twindb_infrastructure.config.credentials import Credentials, \
    CredentialsException
from twindb_infrastructure.config.ssh_credentials import SshCredentials


@pytest.fixture
def config(tmpdir):
    fp = tmpdir.join('config')
    fp.write('# this is a test config')
    return fp


@pytest.fixture
def private_key(tmpdir):
    fp = tmpdir.join('id_rsa')
    fp.write("""-----BEGIN RSA PRIVATE KEY-----
MIIEogIBAAKCAQEAqDshVjmu8khTpde8xVy2W4bD4BcZ4IzL4/AoCUJvxVtFT1xL
J7kG/8Zos/5DCM5Lq4+Q1T3umdoT7xNDJ8vOOoHkhXlB1IGnegqDciGnZASTxy0e
HmLZDwrJ6sWWdhySlCz2gUTlWembhHgQ7pFIlAKuUgmut2TP/tDjpNT2prEiarZt
UEs8AcpD6rDVO8ur3uNPYo5KTvDbe747BYz6B8Ksz9Pz3285F1Fes/OLQ1Pe6V/F
z8nmkewT9jGmUMwSQt33YXOlwy2jbKvd/JkhYWsRqyyK299YP57gPitfPrJlavxt
8E5Tw6/Ify2TCh9CfD/SKU43IAwe6UfCQDicDwIDAQABAoIBAF1z64LwrESe9Qit
nYmthQe3B1yWuKNK04Cdyj/Kjjh+CTSauo0odcDkQQmr9yUPJG37ZKNwsfj5chVf
B/E1gCx0N7QFthIMrDJZYMen9krTWBxO7epHUvjOL3ihpoGaQbrad108HoQiB2hB
InbEciL2kku0YUAzWm/dLnhEbXgPC894+20jWfeHOAGFgciGmgXHUZRmIImXJn+Y
/sfY/tkr+f8rD8nxLTsNJRWZJGNBifHjaIYjtKK7tz6SINSuc42Bx09cViSRw++N
wDVCM3ijXKGQi71lWYKDPNyhgXLAjngrcn0sRimhZcRMjvYpMKs0n34MVjDFWbUl
OaroPpECgYEA0jpcwryqG4RNpcIUxJnZ+CrbW46PrL/7G5hJJVZiEtLhFJJ5Wug2
6tVLKDk6P7YqktePp/k4kub7hOJ6p/bQUyRexVznYV/ynxMQ0AkDQqNP1sMNXQTm
cWi9a1OaD5h2Jg/f1swEpOUN3ZU6/GVAx8IxPkiijxkU8vSQ1zI6KV0CgYEAzNvy
7N8o3HVSUVaERjNfkCXTDLVohZ/IQM3t9XVlVSQDXgW19kyCTNmV0MCFGuqoIOJd
6sa+l5eHiC8PFASQ51PJ4aoQql7fF/k63G0pmm4CGoL/AaNhF7m4uAPEXIs7sL7o
Xhhpqx2HL9sYGe/XVEnDkkw68uh+LdZCntQ1CFsCgYA0eQjKOpkjAST4aLcSU2yK
evgBpFXMQqcEvkATp7oXBLfVkLHltOxwNQjrY01ctbVurYtX2+b5E9pX0sfWwM5C
0mMtVAEU1wQSHIonwvgjW+wDqO/e9egnCoOtFFLx7ZYf7fpq/MVz+xA47JSqhwNi
WOA9sZeRrCsEcXLto8XMqQKBgB2y4VPfwk+7nnR2Q3Td68O9CAy2m/GLSX/DmvTT
0R33u5k84LVVQCqd/K8nyeQuErO5vX3U1Dqr2BUxJVF0nAE9T24stn/MgzE5i4P7
O2XM/vcS+J8nLWNAJHxg5223La8g7hT+GwuYm0mfzK2t7JymmPiznnQqqmhAwKXA
A/QzAoGAGQAzjHkhlUEHBSGEuzPG5C2hxlu0/pPysti2NIlwWG6vy2coyfAPDK0a
ArKlXxiiEsDbyRolRDMLfq4ovCFFqv3q+fY80/owBu3KcaXN260IQTpHuVRYM9Ax
XFS1IpIg+KIzUDtmGDi5uIB4KTps3YmpF3iqCn6oQkQnFZBFBbY=
-----END RSA PRIVATE KEY-----
""")
    fp.chmod(0400)
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


def test_ssh_sets_options(config, private_key):
    config.write("""
[ssh]
private_key_file = %s
""" % str(private_key))
    c = SshCredentials(config_path=str(config))
    assert c.private_key == """-----BEGIN RSA PRIVATE KEY-----
MIIEogIBAAKCAQEAqDshVjmu8khTpde8xVy2W4bD4BcZ4IzL4/AoCUJvxVtFT1xL
J7kG/8Zos/5DCM5Lq4+Q1T3umdoT7xNDJ8vOOoHkhXlB1IGnegqDciGnZASTxy0e
HmLZDwrJ6sWWdhySlCz2gUTlWembhHgQ7pFIlAKuUgmut2TP/tDjpNT2prEiarZt
UEs8AcpD6rDVO8ur3uNPYo5KTvDbe747BYz6B8Ksz9Pz3285F1Fes/OLQ1Pe6V/F
z8nmkewT9jGmUMwSQt33YXOlwy2jbKvd/JkhYWsRqyyK299YP57gPitfPrJlavxt
8E5Tw6/Ify2TCh9CfD/SKU43IAwe6UfCQDicDwIDAQABAoIBAF1z64LwrESe9Qit
nYmthQe3B1yWuKNK04Cdyj/Kjjh+CTSauo0odcDkQQmr9yUPJG37ZKNwsfj5chVf
B/E1gCx0N7QFthIMrDJZYMen9krTWBxO7epHUvjOL3ihpoGaQbrad108HoQiB2hB
InbEciL2kku0YUAzWm/dLnhEbXgPC894+20jWfeHOAGFgciGmgXHUZRmIImXJn+Y
/sfY/tkr+f8rD8nxLTsNJRWZJGNBifHjaIYjtKK7tz6SINSuc42Bx09cViSRw++N
wDVCM3ijXKGQi71lWYKDPNyhgXLAjngrcn0sRimhZcRMjvYpMKs0n34MVjDFWbUl
OaroPpECgYEA0jpcwryqG4RNpcIUxJnZ+CrbW46PrL/7G5hJJVZiEtLhFJJ5Wug2
6tVLKDk6P7YqktePp/k4kub7hOJ6p/bQUyRexVznYV/ynxMQ0AkDQqNP1sMNXQTm
cWi9a1OaD5h2Jg/f1swEpOUN3ZU6/GVAx8IxPkiijxkU8vSQ1zI6KV0CgYEAzNvy
7N8o3HVSUVaERjNfkCXTDLVohZ/IQM3t9XVlVSQDXgW19kyCTNmV0MCFGuqoIOJd
6sa+l5eHiC8PFASQ51PJ4aoQql7fF/k63G0pmm4CGoL/AaNhF7m4uAPEXIs7sL7o
Xhhpqx2HL9sYGe/XVEnDkkw68uh+LdZCntQ1CFsCgYA0eQjKOpkjAST4aLcSU2yK
evgBpFXMQqcEvkATp7oXBLfVkLHltOxwNQjrY01ctbVurYtX2+b5E9pX0sfWwM5C
0mMtVAEU1wQSHIonwvgjW+wDqO/e9egnCoOtFFLx7ZYf7fpq/MVz+xA47JSqhwNi
WOA9sZeRrCsEcXLto8XMqQKBgB2y4VPfwk+7nnR2Q3Td68O9CAy2m/GLSX/DmvTT
0R33u5k84LVVQCqd/K8nyeQuErO5vX3U1Dqr2BUxJVF0nAE9T24stn/MgzE5i4P7
O2XM/vcS+J8nLWNAJHxg5223La8g7hT+GwuYm0mfzK2t7JymmPiznnQqqmhAwKXA
A/QzAoGAGQAzjHkhlUEHBSGEuzPG5C2hxlu0/pPysti2NIlwWG6vy2coyfAPDK0a
ArKlXxiiEsDbyRolRDMLfq4ovCFFqv3q+fY80/owBu3KcaXN260IQTpHuVRYM9Ax
XFS1IpIg+KIzUDtmGDi5uIB4KTps3YmpF3iqCn6oQkQnFZBFBbY=
-----END RSA PRIVATE KEY-----
"""
    assert c.public_key == """ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQCoOyFWOa7ySFOl17zFXLZbhsPgFxngjMvj8CgJQm/FW0VPXEsnuQb/xmiz/kMIzkurj5DVPe6Z2hPvE0Mny846geSFeUHUgad6CoNyIadkBJPHLR4eYtkPCsnqxZZ2HJKULPaBROVZ6ZuEeBDukUiUAq5SCa63ZM/+0OOk1PamsSJqtm1QSzwBykPqsNU7y6ve409ijkpO8Nt7vjsFjPoHwqzP0/PfbzkXUV6z84tDU97pX8XPyeaR7BP2MaZQzBJC3fdhc6XDLaNsq938mSFhaxGrLIrb31g/nuA+K18+smVq/G3wTlPDr8h/LZMKH0J8P9IpTjcgDB7pR8JAOJwP
"""

