import sys
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
