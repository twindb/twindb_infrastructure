import os
import os.path
import stat
import tempfile
from botocore.exceptions import ClientError
from twindb_infrastructure.providers.aws.connection import AWSConnection


class AWSSsh(object):
    """
    :type _aws_connection: AWSConnection
    """

    def __init__(self, aws_connection, ssh_key_name):
        self._aws_connection = aws_connection
        self._ec2 = self._aws_connection.client('ec2')

        self.ssh_key_name = ssh_key_name

    @property
    def ssh_port(self):
        return 22

    @property
    def ssh_username(self):
        return 'ec2-user'

    @property
    def ssh_key_file_path(self):
        ssh_key_file_path = os.path.join(tempfile.gettempdir(), '%s.pem' % self.ssh_key_name)
        return ssh_key_file_path

    def create_ssh_key(self):
        key_pair = self._ec2.create_key_pair(KeyName=self.ssh_key_name)

        with open(name=self.ssh_key_file_path, mode='w') as f:
            f.write(key_pair['KeyMaterial'])
            os.chmod(self.ssh_key_file_path, stat.S_IRWXU)

        return True

    def delete_ssh_key(self, local=False):
        if not local:
            self._ec2.delete_key_pair(KeyName=self.ssh_key_name)

        os.unlink(self.ssh_key_file_path)

        return True

    def exists_ssh_key(self):
        if not os.path.exists(self.ssh_key_file_path):
            return False

        try:
            self._ec2.describe_key_pairs(KeyNames=[self.ssh_key_name])
        except ClientError as e:
            # Cleanup the file because the key does not exist on the AWS side
            self.delete_ssh_key(local=True)

            return False

        return True

    def get_ssh_options(self):
        """Return common set of SSH and SCP options."""
        options = [
          '-2',
          '-o', 'UserKnownHostsFile=/dev/null',
          '-o', 'StrictHostKeyChecking=no',
          '-o', 'IdentitiesOnly=yes',
          '-o', 'PreferredAuthentications=publickey',
          '-o', 'PasswordAuthentication=no',
          '-o', 'ConnectTimeout=5',
          '-o', 'GSSAPIAuthentication=no',
          '-o', 'ServerAliveInterval=30',
          '-o', 'ServerAliveCountMax=10',
          '-i', self.ssh_key_file_path
        ]

        return options
