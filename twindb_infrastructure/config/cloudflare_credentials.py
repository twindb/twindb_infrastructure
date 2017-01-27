from ConfigParser import NoSectionError
from twindb_infrastructure.config import TWINDB_INFRA_CONFIG
from twindb_infrastructure.config.credentials import Credentials


class CloudFlareCredentials(Credentials):

    cloudflare_email = None
    cloudflare_auth_key = None

    def __init__(self, config_path=TWINDB_INFRA_CONFIG):
        super(CloudFlareCredentials, self).__init__(config_path=config_path)
        try:
            for option in self.config.options('cloudflare'):
                value = self.config.get('cloudflare', option).strip('"\'')
                setattr(self, option, value)

        except NoSectionError:
            pass
