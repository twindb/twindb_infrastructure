from ConfigParser import ConfigParser
from twindb_infrastructure.config import TWINDB_INFRA_CONFIG
from twindb_infrastructure.config.aws_credentials import AwsCredentials
from twindb_infrastructure.config.cloudflare_credentials import \
    CloudFlareCredentials
from twindb_infrastructure.config.ssh_credentials import SshCredentials


class Config(object):
    config = None
    config_path = None
    aws = None
    ssh = None
    cloudflare = None

    def __init__(self, config_path=TWINDB_INFRA_CONFIG):
        self.config_path = config_path
        self.config = ConfigParser()
        self.config.read(config_path)
        self.aws = AwsCredentials(config_path=self.config_path)
        self.ssh = SshCredentials(config_path=self.config_path)
        self.cloudflare = CloudFlareCredentials(config_path=self.config_path)
