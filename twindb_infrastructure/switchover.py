from contextlib import contextmanager
from pprint import pprint

import boto3
# import pymysql
from subprocess import check_call, CalledProcessError

import pymysql
from pymysql.cursors import DictCursor

from twindb_infrastructure import log
from twindb_infrastructure.util import domainname


def start_proxy(proxy):
    """Start ProxySQL on a remote server proxy"""
    cmd = [
        'sudo',
        'ssh',
        '-t',
        proxy,
        'sudo /etc/init.d/proxysql start'
    ]
    log.info('Executing: %s', ' '.join(cmd))
    check_call(cmd)


def stop_proxy(proxy):
    """Stop ProxySQL on a remote server proxy"""
    cmd = [
        'sudo',
        'ssh',
        '-t',
        proxy,
        'sudo killall -9 proxysql'
    ]
    log.info('Executing: %s', ' '.join(cmd))
    check_call(cmd)


def restart_proxy(proxy):
    """Restart ProxySQL on server proxy"""
    log.info('Restarting %s', proxy)
    stop_proxy(proxy)
    start_proxy(proxy)


def change_names_to(names, ip_addr):
    client = boto3.client('route53')
    if names:
        for name in names:
            log.info('Updating A record of %s to %s', name, ip_addr)

            print(name)
            response = client.list_hosted_zones_by_name(
                DNSName=domainname(name),
            )
            # pprint(response)
            zone_id = response['HostedZones'][0]['Id']
            # print(zone_id)
            # print(region)
            request = {
                'HostedZoneId': zone_id,
                'ChangeBatch': {
                    'Comment': 'Automated switchover DNS update',
                    'Changes': [
                        {
                            'Action': 'UPSERT',
                            'ResourceRecordSet': {
                                'Name': name,
                                'Type': 'A',
                                'TTL': 300,
                                'ResourceRecords': [
                                    {
                                        'Value': ip_addr
                                    },
                                ]
                            }
                        }
                    ]
                }
            }
            # print(request)
            response = client.change_resource_record_sets(**request)
            # print('response')
            # pprint(response)


def log_remaining_sessions(host, user='root', password='', port=3306):
    """Connect to host and print existing sessions.

    :return: Number of connected sessions
    :rtype: int
    """
    with _connect(host, user=user, password=password, port=port) as conn:
        cursor = conn.cursor()
        query = "SHOW PROCESSLIST"
        cursor.execute(query)
        nrows = cursor.rowcount
        while True:
            row = cursor.fetchone()
            if row:
                print(row)
            else:
                break

    return nrows


def eth1_present(proxy):
    """Check if eth1 is up on remote host proxy"""
    cmd = [
        'sudo',
        'ssh',
        '-t',
        proxy,
        '/sbin/ifconfig eth1'
    ]
    log.info('Executing: %s', ' '.join(cmd))
    try:
        check_call(cmd)
        return True
    except CalledProcessError:
        return False


@contextmanager
def _connect(host, user='root', password='', port=3306):
    """Connect to ProxySQL admin interface."""
    pass
    connect_args = {
        'host': host,
        'port': port,
        'user': user,
        'passwd': password,
        'connect_timeout': 60,
        'cursorclass': DictCursor
    }

    conn = pymysql.connect(**connect_args)
    yield conn
    conn.close()
