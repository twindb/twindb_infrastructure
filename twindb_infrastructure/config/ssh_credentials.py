from subprocess import Popen, PIPE
from twindb_infrastructure.config import TWINDB_INFRA_CONFIG
from twindb_infrastructure.config.credentials import Credentials, \
    CredentialsException


class SshCredentials(Credentials):

    private_key_file = None
    private_key = None
    public_key = None

    def __init__(self, config_path=TWINDB_INFRA_CONFIG):
        super(SshCredentials, self).__init__(config_path=config_path)
        my_section = 'ssh'
        if not self.config.has_section(my_section):
            raise CredentialsException('There is no %s '
                                       'section in config %s'
                                       % (my_section, self.config_path))
        self.private_key_file = self.config.get(my_section,
                                                'private_key_file')\
            .strip('"\'')
        with open(self.private_key_file) as fp:
            self.private_key = fp.read()

        p = Popen(['ssh-keygen', '-y', '-f', self.private_key_file],
                  stdout=PIPE, stderr=PIPE)
        self.public_key, cerr = p.communicate()
