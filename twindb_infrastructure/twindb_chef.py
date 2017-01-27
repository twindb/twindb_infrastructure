import click
from subprocess import Popen
import json
import os
from twindb_infrastructure import setup_logging, log, __version__
from twindb_infrastructure.config import TWINDB_INFRA_CONFIG
from twindb_infrastructure.config.config import ConfigException
from twindb_infrastructure.util import parse_config


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
    Console script to work with Chef
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


def get_mounts_from_template(instance_profile):
    mounts = {}
    if not instance_profile \
            or "BlockDeviceMappings" not in instance_profile:
        return mounts

    for volume in instance_profile['BlockDeviceMappings']:
        key = volume['MountPoint'].replace('/', '_').lstrip('_')
        mounts[key] = {
            "device": volume['DeviceName'],
            "type": "xfs",
            "opts": "rw,relatime,attr2,inode64,noquota,noatime",
            "mount_point": volume['MountPoint']
        }
    return mounts


@main.command()
@click.option('--founder', default=False, is_flag=True,
              help='The node is a cluster founder')
@click.option('--recipe',
              help='Chef recipe to run')
@click.option('--cluster-name', help='Galer cluster name',
              default='PXC', show_default=True)
@click.option('--template', help='Instance profile')
@click.argument('ip')
@click.argument('node_name', required=False)
def bootstrap(founder, recipe, cluster_name, template, ip, node_name):
    """Run chef client on the server"""
    log.debug('node_name = %s' % node_name)
    node = None

    if node_name:
        node = node_name
    elif template:
        with open(template) as fp:
            instance_profile = json.loads(fp.read())
            node = instance_profile["Name"]
    if not node:
        log.error("If node_name agrument is not given "
                  "you must specify --template.")
        exit(1)

    cmd = [
        'knife',
        'bootstrap', ip, '--node-name', node,
        '--yes',
        '--ssh-user', 'centos', '--sudo',
        '--ssh-identity-file',
        os.path.expanduser('~/.ssh/id_rsa'),
        '--secret-file',
        os.path.expanduser('~/.chef/encrypted_data_bag_secret'),
        '--environment', 'staging',
        '--run-list', "role[base],recipe[%s]" % recipe
        ]
    attributes = {
        "percona": {
            "cluster": {
                "wsrep_cluster_name": cluster_name,
                "founder": founder
            }
        }
    }
    if template:
        with open(template) as fp:
            instance_profile = json.loads(fp.read())
            mounts = get_mounts_from_template(instance_profile)

            if mounts:
                attributes["fb_fstab"] = {
                    "mounts": mounts
                }

    cmd.append('--json-attributes')
    cmd.append(json.dumps(attributes))
    log.debug('Executing %s' % ' '.join(cmd))
    proc = Popen(cmd)
    proc.communicate()
