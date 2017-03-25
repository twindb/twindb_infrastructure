import pytest
from click.testing import CliRunner

from twindb_infrastructure import twindb_chef
from twindb_infrastructure.twindb_chef import get_mounts_from_template


def test_main():
    runner = CliRunner()
    result = runner.invoke(twindb_chef.main)
    assert result.exit_code == 0


@pytest.mark.parametrize('instance_profile, mounts', [
    (
        None,
        {}
    ),
    (
        {},
        {}
    ),
    (
        {
            "ImageId": "ami-9b19f7fb",
            "InstanceType": "m4.4xlarge",
            "KeyName": "deployer",
            "SecurityGroupId": "sg-8dd1cae9",
            "SubnetId": "subnet-646cef3d",
            "RootVolumeSize": 200,
            "EbsOptimized": True,
            "UserName": "centos",
            "Name": "db-node01",
            "Region": "us-west-2"
        },
        {}
    ),
    (
        {
            "ImageId": "ami-9b19f7fb",
            "BlockDeviceMappings": [
                {
                    "DeviceName": "/dev/xvdb",
                    "VolumeSize": 200,
                    "VolumeType": "io1",
                    "MountPoint": "/var/lib/mysql",
                    "Iops": 4000
                },
                {
                    "DeviceName": "/dev/xvdc",
                    "VolumeSize": 300,
                    "VolumeType": "gp2",
                    "MountPoint": "/var/log/mysql"
                }
            ],
            "InstanceType": "m4.4xlarge",
            "KeyName": "deployer",
            "SecurityGroupId": "sg-8dd1cae9",
            "SubnetId": "subnet-646cef3d",
            "RootVolumeSize": 200,
            "EbsOptimized": True,
            "UserName": "centos",
            "Name": "db-node01",
            "Region": "us-west-2"
        },
        {
            "var_lib_mysql": {
                "device": "/dev/xvdb",
                "type": "xfs",
                "opts": "rw,relatime,attr2,inode64,noquota,noatime",
                "mount_point": "/var/lib/mysql"
            },
            "var_log_mysql": {
                "device": "/dev/xvdc",
                "type": "xfs",
                "opts": "rw,relatime,attr2,inode64,noquota,noatime",
                "mount_point": "/var/log/mysql"
            }
        }
    )


])
def test_get_mounts_from_tempate(instance_profile, mounts):
    assert get_mounts_from_template(instance_profile) == mounts
