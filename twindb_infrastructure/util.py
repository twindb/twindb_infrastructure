import sys
from subprocess import Popen
from twindb_infrastructure import log
from twindb_infrastructure.config.config import Config

CONFIG = None


def printf(fmt, *args):
    sys.stdout.write(fmt % args)


def parse_config(path):
    """Parse TwinDB Infrastructure config

    :param path: path to config file
    :raise ConfigException if config can't be parsed
    """
    return Config(path)


def _execute_remote(cmd, node):

    ssh_cmd = ['ssh', '-t', '-o', 'StrictHostKeyChecking=no', '-i',
               '/home/twindbcom/.ssh/id_rsa', '-l', 'centos', node, cmd]
    log.debug('Executing %s' % ' '.join(ssh_cmd))
    proc = Popen(ssh_cmd)
    proc.communicate()


def stop_chef_client(nodes):
    log.info('Stopping Chef client on %s' % ', '.join(nodes))
    for node in nodes:
        _execute_remote("sudo systemctl stop chef-client", node)


def start_chef_client(nodes):
    log.info('Starting Chef client on %s' % ', '.join(nodes))
    for node in nodes:
        _execute_remote("sudo systemctl start chef-client", node)


def stop_galera(nodes):
    log.info('Stopping Galera on %s' % ', '.join(nodes))
    for node in nodes:
        _execute_remote("sudo systemctl stop mysql.service", node)
        _execute_remote("sudo systemctl stop mysql@bootstrap.service", node)


def start_galera(nodes):
    log.info('Starting Galera on %s' % ', '.join(nodes))
    for node in nodes:
        _execute_remote("sudo systemctl start mysql", node)


def remote_rmdir(directory, nodes):
    for node in nodes:
        log.info('Removing %s on %s' % (directory, node))
        _execute_remote("sudo rm -rf \"%s\"/*" % directory, node)


def remote_restore(node, backup_copy, datadir):
    log.info('Restoring backup copy %s on %s' % (backup_copy, node))
    _execute_remote("sudo twindb-backup restore mysql --dst %s %s"
                    % (datadir, backup_copy),
                    node)


def bootstrap_first_node(node, datadir):
    _execute_remote("sudo chown -R mysql:mysql '%s'" % (datadir, ), node)
    _execute_remote("sudo systemctl start mysql@bootstrap.service", node)


def bootstrap_next_node(node, datadir):

    _execute_remote("sudo mysql_install_db", node)
    _execute_remote('sudo chown -R mysql:mysql "%s"' % (datadir, ), node)
    _execute_remote("sudo systemctl start mysql", node)


def domainname(name):
    """Extracts domain name from a fqdn

    :param name: FQDN like www.google.com or www.yahoo.com.
    :type name: str
    :return: domain name like google.com  or yahoo.com.
    :rtype: str
    """
    result = name.split('.')
    result.pop(0)
    return '.'.join(result)
