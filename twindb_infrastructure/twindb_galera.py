import click
from subprocess import Popen
from twindb_infrastructure import setup_logging, __version__
from twindb_infrastructure import log
from twindb_infrastructure.config import TWINDB_INFRA_CONFIG
from twindb_infrastructure.config.config import ConfigException
from twindb_infrastructure.util import parse_config, stop_chef_client, \
    stop_galera, remote_rmdir, remote_restore, \
    bootstrap_first_node, bootstrap_next_node


CONFIG = None


@click.group(invoke_without_command=True)
@click.option('--config', default=TWINDB_INFRA_CONFIG,
              help='Config file',
              show_default=True,
              type=click.Path())
@click.option('--debug', is_flag=True, default=False,
              help='Print debug messages')
@click.option('--version', help='Show tool version and exit.', is_flag=True,
              default=False)
@click.pass_context
def main(ctx, config, debug, version):
    """
    Console script to work with Galera
    """
    global CONFIG
    if not ctx.invoked_subcommand:
        if version:
            print(__version__)
        else:
            print(ctx.get_help())
        return 0

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
    if backup_copy:
        all_nodes = list(node) + [founder]
        stop_chef_client(all_nodes)
        stop_galera(all_nodes)
        remote_rmdir(datadir, all_nodes)

        remote_restore(founder, backup_copy, datadir)
        bootstrap_first_node(founder, datadir)
        bootstrap_next_node(node[0], datadir)
        # for n in node:
        #    bootstrap_next_node(n, datadir)
        # start_chef_client(all_nodes)
        pass
    else:
        log.info('No backup copy specified. Choose one from below:')
        proc = Popen(['twindb-backup', 'ls'])
        proc.communicate()
