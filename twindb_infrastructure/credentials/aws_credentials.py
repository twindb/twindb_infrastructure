from twindb_infrastructure.credentials.credentials import Credentials, \
    CREDENTIALS_CONFIG, CredentialsException


class AwsCredentials(Credentials):

    aws_access_key_id = None
    aws_secret_access_key = None
    aws_default_region = "us-east-1"
    aws_default_ami = "ami-6d1c2007"

    aws_instance_username = {
        aws_default_ami: "centos"
    }

    def __init__(self, config_path=CREDENTIALS_CONFIG):
        super(AwsCredentials, self).__init__(config_path=config_path)
        if not self.config.has_section('aws'):
            raise CredentialsException('There is no aws section in config %s'
                                       % self.config_path)
        for option in self.config.options('aws'):
            value = self.config.get('aws', option).strip('"\'')
            option_lower = option.lower()

            if option_lower.startswith('aws_instance_username_'):
                ami = option_lower.replace('aws_instance_username_', '')
                self.aws_instance_username[ami] = value
            else:
                setattr(self, option, value)

