from subprocess import Popen, check_call

from twindb_infrastructure import log


def start_proxy(proxy):
    """Start ProxySQL on a remote server proxy"""
    cmd = [
        'ssh',
        proxy,
        'sudo /etc/init.d/proxysql start'
    ]
    log.info('Executing %r', cmd)
    check_call(cmd)


def stop_proxy(proxy):
    """Stop ProxySQL on a remote server proxy"""
    cmd = [
        'ssh',
        proxy,
        'sudo killall -9 proxysql'
    ]
    log.info('Executing %r', cmd)
    check_call(cmd)


def restart_proxy(proxy):
    """Restart ProxySQL on server proxy"""
    log.info('Restarting %s', proxy)
    stop_proxy(proxy)
    start_proxy(proxy)


def change_names_to(names, ip_addr):
    if names:
        for name in names:
            log.info('Updating A record of %s to %s', name, ip_addr)


def log_remaining_sessions(host, user='root', password='', port=3306):
    """Connect to host and print existing sessions."""
    pass
