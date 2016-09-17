# -*- coding: utf-8 -*-
"""
TwinDB Amazon infrastructure
"""
import logging
import click
import etcd
from twindb_infrastructure import ConfigPath, parse_config
from twindb_infrastructure.clogging import setup_logging
from twindb_infrastructure.config.config import TWINDB_INFRA_CONFIG


pass_path = click.make_pass_decorator(ConfigPath, ensure=True)
log = logging.getLogger(__name__)


@click.group()
@click.option('--config', default=TWINDB_INFRA_CONFIG,
              help='Config file')
@click.option('--debug', is_flag=True, default=False,
              help='Print debug messages')
@pass_path
def main(c_path, config, debug):
    """
    Console script to work with TwinDB Etcd cluster
    """
    setup_logging(log, debug=debug)
    log.debug('Using config %s' % config)
    c_path.config_path = config


@main.command()
@pass_path
def show(c_path):
    """List Etcd nodes"""
    parse_config(c_path.config_path)

    client = etcd.Client(srv_domain='twindb.com')
    print(client.machines)


if __name__ == "__main__":
    pass
