import click
from subprocess import Popen
import os
from twindb_infrastructure import setup_logging, log
from twindb_infrastructure.config import TWINDB_INFRA_CONFIG
from twindb_infrastructure.config.config import ConfigException
from twindb_infrastructure.util import parse_config


@click.group()
@click.option('--config', default=TWINDB_INFRA_CONFIG,
              help='Config file',
              show_default=True,
              type=click.Path(exists=True))
@click.option('--debug', is_flag=True, default=False,
              help='Print debug messages')
def main(config, debug):
    """
    Console script to work with Chef
    """
    global CONFIG

    setup_logging(log, debug=debug)
    log.debug('Using config %s' % config)
    try:
        CONFIG = parse_config(config)
    except ConfigException as err:  # pragma: no cover
        log.error(err)
        exit(-1)


@main.command()
@click.option('--founder', default=False, is_flag=True,
              help='The node is a cluster founder')
@click.option('--recipe',
              help='Chef recipe to run')
@click.argument('ip')
@click.argument('node_name')
def bootstrap(founder, recipe, ip, node_name):
    """Run chef client on the server"""
    cmd = [
        'knife',
        'bootstrap', ip, '--node-name', node_name,
        '--yes',
        '--ssh-user', 'centos', '--sudo',
        '--ssh-identity-file',
        os.path.expanduser('~/.ssh/id_rsa'),
        '--secret-file',
        os.path.expanduser('~/.chef/encrypted_data_bag_secret'),
        '--environment', 'staging',
        '--run-list', 'role[%s]' % recipe
        ]
    if founder:
        cmd.append('--json-attributes')
        cmd.append('{ "percona": { "cluster": { "founder": true } } }')

    proc = Popen(cmd)
    proc.communicate()
