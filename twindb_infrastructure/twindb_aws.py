# -*- coding: utf-8 -*-
"""
TwinDB Amazon infrastructure
"""
import boto3
import click
from twindb_infrastructure.config.config import TWINDB_INFRA_CONFIG, Config


class TwinDBInfraException(Exception):
    pass


class ConfigPath(object):
    config_path = None

pass_path = click.make_pass_decorator(ConfigPath, ensure=True)


@click.group()
@click.option('--config', default=TWINDB_INFRA_CONFIG,
              help='Config file')
@pass_path
def main(c_path, config):
    """
    Console script to work with TwinDB Amazon Infrastructure
    """
    c_path.config_path = config


@main.command()
@click.option('--tags', is_flag=True, help='Show instance tags')
@pass_path
def show(c_path, tags):
    """List TwinDB servers"""
    Config(c_path.config_path)

    client = boto3.client('ec2')
    response = client.describe_instances()
    for reservation in response['Reservations']:
        for instance in reservation['Instances']:
            print(instance['InstanceId'])
            if tags:
                for tag in instance['Tags']:
                    print("\t%s: %s" % (tag['Key'], tag['Value']))


if __name__ == "__main__":
    # main()
    pass
