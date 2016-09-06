import ConfigParser
import os

CREDENTIALS_CONFIG = "/etc/twindb/twindb_infrastructure.conf"


class CredentialsException(Exception):
    """
    Exception for Credentials class errors
    """


class Credentials(object):
    """
    Class to work with TwinDB Infrastructure config file
    """
    config_path = None
    """TwinDB Intrastructure Config"""

    def __init__(self, config_path=CREDENTIALS_CONFIG):
        """

        :type config_path: str
        """
        if not os.path.exists(config_path):
            raise CredentialsException("Credentials config file %s not found"
                                       % config_path)
        self.config_path = config_path
        try:
            self.config = ConfigParser.ConfigParser()
            self.config.read(self.config_path)

        except ConfigParser.Error as err:
            raise CredentialsException(err)

        if not self.config.sections():
            raise CredentialsException('No sections in config %s'
                                       % self.config_path)
