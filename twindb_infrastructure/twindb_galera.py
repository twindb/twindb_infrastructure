import click
from twindb_infrastructure import setup_logging
from twindb_infrastructure import log
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
    Console script to work with Galera
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
@click.argument('backup_copy', required=False)
@click.option('--datadir', help='Directory where to restore the backup copy',
              default='/var/lib/mysql', show_default=True)
@click.option('--founder', help='IP address of a founder node',
              show_default=True)
@click.option('--node', '-n', multiple=True,
              help='IP addresses on cluster nodes. '
                   'Multiple options are allowed')
def cluster(backup_copy, datadir, founder, node):
    """Bootstrap xtradb cluster"""
    pass
