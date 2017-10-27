# -*- coding: utf-8 -*-
"""
TwinDB Amazon infrastructure
"""
from subprocess import CalledProcessError

import boto3
import time
from botocore.exceptions import ClientError
import click
import json
from twindb_infrastructure import setup_logging, __version__
from twindb_infrastructure import log
from twindb_infrastructure.config.config import TWINDB_INFRA_CONFIG, \
    ConfigException
from twindb_infrastructure.providers.aws import AWS_REGIONS, \
    launch_ec2_instance, get_instance_private_ip
from twindb_infrastructure.switchover import change_names_to, \
    log_remaining_sessions, stop_proxy, eth1_present, start_proxy, restart_proxy
from twindb_infrastructure.tagset import TagSet
from twindb_infrastructure.util import printf, parse_config


class TwinDBInfraException(Exception):
    pass


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
    Console script to work with TwinDB Amazon Infrastructure
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
@click.option('--tags', is_flag=True, help='Show instance tags')
@click.option('--verbose', is_flag=True,
              help='Show more details about the instance')
@click.option('--region', type=click.Choice(AWS_REGIONS),
              help='AWS region name')
@click.argument('tags-filter', nargs=-1)
def show(tags, verbose, region, tags_filter):
    """List TwinDB servers"""

    if region:
        region_name = region
    else:
        region_name = CONFIG.aws.aws_default_region

    client = boto3.client('ec2', region_name=region_name)
    response = client.describe_instances()
    log.debug('response = %r' % response)
    for reservation in response['Reservations']:
        for instance in reservation['Instances']:
            if tags_filter \
                    and \
                    not TagSet(tags_filter).issubset(TagSet(instance['Tags'])):
                continue

            printf('%s' % instance['InstanceId'])

            if tags:
                printf(': Tags: ')
                try:
                    printf('%s', TagSet(instance['Tags']))
                except KeyError:
                    printf("None")
                    pass

            if verbose:
                if tags:
                    printf(",")
                printf(' State: %s,' % instance['State']['Name'])
                try:
                    printf(' PublicIP: %s,' % instance['PublicIpAddress'])
                except KeyError:
                    pass
                try:
                    printf(' PrivateIP: %s,' % instance['PrivateIpAddress'])
                except KeyError:
                    pass
                printf(' AvailabilityZone: %s'
                       % instance['Placement']['AvailabilityZone'])

            printf("\n")


@main.command()
@click.argument('instance-id')
def terminate(instance_id):
    """Terminate Amazon instance"""

    try:
        ec2 = boto3.resource('ec2')
        ec2.instances.filter(InstanceIds=[instance_id]).terminate()

    except ClientError as err:
        log.error(err)


@main.command()
@click.argument('instance-id')
def stop(instance_id):
    """Stop Amazon instance"""

    try:
        ec2 = boto3.resource('ec2')
        ec2.instances.filter(InstanceIds=[instance_id]).stop()

    except ClientError as err:
        log.error(err)


@main.command()
@click.argument('instance-id')
def start(instance_id):
    """Start Amazon instance"""

    try:
        ec2 = boto3.resource('ec2')
        ec2.instances.filter(InstanceIds=[instance_id]).start()

    except ClientError as err:
        log.error(err)


@main.command()
@click.argument('template')
def launch(template):
    """Launch new Amazon instance"""

    log.info("Starting instance")
    with open(template) as fp:
        instance_profile = json.loads(fp.read())

        private_key_file = CONFIG.ssh.private_key_file
        instance_id = \
            launch_ec2_instance(instance_profile,
                                private_key_file=private_key_file)

        if not instance_id:
            log.error("Failed to launch EC2 instance")
            exit(-1)

        log.info("Launched instance %s" % instance_id)

        ip = get_instance_private_ip(instance_id)
        log.info('Instance %s on %s' % (instance_id, ip))


@main.command()
@click.argument('proxy_a')
@click.argument('proxy_b')
@click.argument('vip')
@click.option('--dns', multiple=True,
              help='Update given DNS names.')
@click.option('--mysql-user', help='MySQL user to connect to proxies.',
              default='root', show_default=True)
@click.option('--mysql-password', help='Password for MySQL user.',
              default='', show_default=True)
@click.option('--mysql-port', help='TCP port that open for MySQL connections.',
              default=3306, show_default=True)
def switch_proxy(proxy_a, proxy_b, vip, dns,
                 mysql_user, mysql_password, mysql_port):
    """Switch active ProxySQL from proxy_a to proxy_b.

    proxy_a is a currently active proxy.

    proxy_b is to be active proxy.

    VIP is virtual IP.
    """
    # n_conn = log_remaining_sessions(proxy_a,
    #                                 mysql_user,
    #                                 mysql_password,
    #                                 mysql_port)
    # print(n_conn)
    # exit(0)
    if proxy_a == proxy_b:
        log.error('Proxy A and Proxy B cannot be same')
        exit(1)

    if vip in [proxy_a, proxy_b]:
        log.error('VIP address cannot be equal to proxy A or proxy B')
        exit(1)

    log.info("Switching active ProxySQL from %s to %s", proxy_a, proxy_b)
    log.debug('DNS names: %s', ', '.join(dns))

    if not eth1_present(proxy_a):
        log.error('It looks like %s is not active proxy', proxy_a)
        exit(1)

    if eth1_present(proxy_b):
        log.error('Interface eth1 is expected on %s, but found on %s. '
                  'Exiting', proxy_a, proxy_b)
        exit(1)

    # Step 1. Restart ProxyB
    try:
        restart_proxy(proxy_b)
        pass
    except CalledProcessError as err:
        log.error(err)
        exit(1)

    # Step 2, 3. Change DNS so dns points to Proxy B Private IP
    change_names_to(dns, proxy_b)

    # Step 4. Wait TTL * 2 time
    wait_time = 30 * 60
    timeout = time.time() + wait_time
    n_conn = 0
    while time.time() < timeout:
        # Step 5. Check if any MySQL users are connected to Proxy A
        #   (and log if any)
        n_conn = log_remaining_sessions(proxy_a,
                                        mysql_user,
                                        mysql_password,
                                        mysql_port)
        if not n_conn:
            log.info('All sessions disconnected from %s', proxy_a)
            break
        log.info('There are still %d open sessions on %s', n_conn, proxy_a)
        time.sleep(3)
    if n_conn > 0:
        log.warning('Will kill existing sessions anyway')
    # 6. Stop Proxy A
    stop_proxy(proxy_a)

    # 7. Wait until eth1 shows up on Proxy B. If not - log error and stop.
    wait_time = 60
    timeout = time.time() + wait_time
    while time.time() < timeout:
        if eth1_present(proxy_b):
            break
        time.sleep(3)

    if not eth1_present(proxy_b):
        log.error('Keepalived failed to move VIP to %s', proxy_b)
        exit(1)

    # 8. Start Proxy A
    start_proxy(proxy_a)

    # 9. Change DNS so dns points to points to VIP
    # 10. Change DNS so dns points to points to VIP
    change_names_to(dns, vip)
    log.info('Successfully done.')
