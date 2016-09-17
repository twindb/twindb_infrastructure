# -*- coding: utf-8 -*-
from twindb_infrastructure.config.config import Config, ConfigException

__author__ = 'TwinDB Development Team'
__email__ = 'dev@twindb.com'
__version__ = '0.1.3'


class TwinDBInfraException(Exception):
    pass


class ConfigPath(object):
    config_path = None


def parse_config(path):
    """Parse TwinDB Infrastructure config"""
    try:
        return Config(path)
    except ConfigException as err:
        log.error(err)
        exit(-1)
