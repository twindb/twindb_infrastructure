import pytest

from twindb_infrastructure.providers.aws import launch_ec2_instance, terminate_instance, AwsError


def test_launch_temninate_ec2_instance():
    instance_profile = {
        "ImageId": "ami-7e69e51e",
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
        "InstanceType": "t2.micro",
        "KeyName": "tester",
        "SecurityGroupIds": ["sg-de8a66a5"],
        "SubnetId": "subnet-f0190aa8",
        "RootVolumeSize": 200,
        "AvailabilityZone": "us-west-2c",
        "UserName": "mkryva",
        "Name": "integraion-test-01",
        "Region": "us-west-2"
    }

    try:
        instance_id = launch_ec2_instance(instance_profile, region=instance_profile['Region'])
    except AwsError as err:
        print err
