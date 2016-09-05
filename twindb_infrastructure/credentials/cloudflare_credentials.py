from twindb_infrastructure.credentials.credentials import Credentials, \
    CREDENTIALS_CONFIG, CredentialsException


class CloudFlareCredentials(Credentials):

    cloudflare_email = None
    cloudflare_auth_key = None

    def __init__(self, config_path=CREDENTIALS_CONFIG):
        super(CloudFlareCredentials, self).__init__(config_path=config_path)
        if not self.config.has_section('cloudflare'):
            raise CredentialsException('There is no cloudflare '
                                       'section in config %s'
                                       % self.config_path)
        for option in self.config.options('cloudflare'):
            value = self.config.get('cloudflare', option).strip('"\'')
            setattr(self, option, value)

