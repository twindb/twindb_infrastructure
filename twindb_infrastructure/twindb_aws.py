# -*- coding: utf-8 -*-
"""
TwinDB Amazon infrastructure
"""
import logging
import boto3
from botocore.exceptions import ClientError
import click
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
    Console script to work with TwinDB Amazon Infrastructure
    """
    setup_logging(log, debug=debug)
    log.debug('Using config %s' % config)
    c_path.config_path = config


@main.command()
@click.option('--tags', is_flag=True, help='Show instance tags')
@pass_path
def show(c_path, tags):
    """List TwinDB servers"""
    parse_config(c_path.config_path)

    client = boto3.client('ec2')
    response = client.describe_instances()
    for reservation in response['Reservations']:
        for instance in reservation['Instances']:
            print(instance['InstanceId'])
            if tags:
                for tag in instance['Tags']:
                    print("\t%s: %s" % (tag['Key'], tag['Value']))


@main.command()
@click.argument('instance-id')
@pass_path
def terminate(c_path, instance_id):
    """Terminate Amazon instance"""
    parse_config(c_path.config_path)

    try:
        ec2 = boto3.resource('ec2')
        ec2.instances.filter(InstanceIds=[instance_id]).terminate()

    except ClientError as err:
        log.error(err)


@main.command()
@click.argument('instance-id')
@pass_path
def stop(c_path, instance_id):
    """Stop Amazon instance"""
    parse_config(c_path.config_path)

    try:
        ec2 = boto3.resource('ec2')
        ec2.instances.filter(InstanceIds=[instance_id]).stop()

    except ClientError as err:
        log.error(err)


@main.command()
@click.argument('instance-id')
@pass_path
def start(c_path, instance_id):
    """Start Amazon instance"""
    parse_config(c_path.config_path)

    try:
        ec2 = boto3.resource('ec2')
        ec2.instances.filter(InstanceIds=[instance_id]).start()

    except ClientError as err:
        log.error(err)

if __name__ == "__main__":
    pass
