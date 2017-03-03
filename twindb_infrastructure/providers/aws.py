import json
from subprocess import Popen, PIPE, call
import time

import os

import boto3
from boto3.exceptions import ResourceNotExistsError, UnknownAPIVersionError
from botocore.exceptions import ClientError

from twindb_infrastructure import log
from twindb_infrastructure.providers.common import wait_sshd

AWS_REGIONS = [
    'us-east-1',
    'us-east-2',
    'us-west-1',
    'us-west-2',
    'ap-northeast-2',
    'ap-southeast-1',
    'ap-southeast-2',
    'ap-northeast-1',
    'eu-central-1',
    'eu-west-1'
]


def ec2_describe_instance(instance_id):
    cmd = [
        "aws", "ec2", "describe-instances",
        "--output", "json",
        "--instance-ids", instance_id
    ]

    try:
        log.debug("Executing: %r" % cmd)
        aws_process = Popen(cmd, stdout=PIPE, stderr=PIPE)
        cout, cerr = aws_process.communicate()

        if aws_process.returncode != 0:
            log.error(cerr)
            return None

        try:
            return json.loads(cout)
        except ValueError as err:
            log.error(err)
            log.error(cerr)
            return None
    except OSError as err:
        log.error(err)
        return None


def get_instance_state(instance_id):
    response = ec2_describe_instance(instance_id)

    try:
        state = response["Reservations"][0]["Instances"][0]["State"]["Name"]
        log.debug("Instance: %s, State: %s" % (instance_id, state))
        return state
    except ValueError as err:
        log.error(err)
        return None


def get_instance_private_ip(instance_id):
    response = ec2_describe_instance(instance_id)

    try:
        return response["Reservations"][0]["Instances"][0]["PrivateIpAddress"]
    except ValueError as err:
        log.error(err)
        return None


def get_instance_public_ip(instance_id):
    response = ec2_describe_instance(instance_id)

    try:
        return response["Reservations"][0]["Instances"][0]["PublicIpAddress"]
    except ValueError as err:
        log.error(err)
        return None


def launch_ec2_instance(instance_profile, region=AWS_REGIONS[0],
                        aws_access_key_id=None, aws_secret_access_key=None,
                        private_key_file=None):
    cmd = [
        "aws", "ec2", "run-instances",
        "--output", "json",
        "--image-id", instance_profile['ImageId'],
        "--instance-type", instance_profile['InstanceType'],
        "--key-name", instance_profile['KeyName'],
        "--subnet-id", instance_profile["SubnetId"]
    ]

    # Add the security group IDs to the command in the form
    # "string" "string" ...
    security_group_ids = list(instance_profile['SecurityGroupId'])
    cmd.append("--security-group-ids")
    for group_id in security_group_ids:
        cmd.append(group_id)

    if instance_profile.get('AvailabilityZone'):
        cmd.append('--placement')
        cmd.append('AvailabilityZone=%s' %
                   instance_profile['AvailabilityZone'])

    if instance_profile.get('EbsOptimized', False):
        cmd.append('--ebs-optimized')

    cmd.append('--block-device-mappings')
    device_mappings = [
        {
            "DeviceName": "/dev/sda1",
            "Ebs": {
                "VolumeSize": instance_profile['RootVolumeSize'],
                "DeleteOnTermination": True,
                "VolumeType": "gp2"
            }
        }
    ]

    try:
        for volume in instance_profile['BlockDeviceMappings']:
            ebs = {
                "VolumeSize": volume['VolumeSize'],
                "DeleteOnTermination": True,
                "VolumeType": volume['VolumeType']
            }
            if 'Iops' in volume:
                ebs['Iops'] = volume['Iops']

            device_mappings.append({
                "DeviceName": volume['DeviceName'],
                "Ebs": ebs
            })
    except KeyError:
        pass

    cmd.append(json.dumps(device_mappings))

    log.debug("Executing: %s" % ' '.join(cmd))
    aws_env = {
        'AWS_ACCESS_KEY_ID': aws_access_key_id,
        'AWS_SECRET_ACCESS_KEY': aws_secret_access_key,
        'AWS_DEFAULT_REGION': region,
        'PATH': os.environ['PATH'],
        'LC_ALL': 'en_US.UTF-8',
        'LC_CTYPE': 'UTF-8',
        'LANG': 'en_US'
    }

    cout, cerr = None, None
    try:
        aws_process = Popen(cmd, stdout=PIPE, stderr=PIPE, env=aws_env)
        cout, cerr = aws_process.communicate()

        if aws_process.returncode != 0:
            log.error('Failed to execute %s' % ' '.join(cmd))
            log.error(cerr)
            return None
    except OSError as err:
        log.error('Failed to execute %r' % cmd)
        log.error(err)
        exit(-1)

    try:
        response = json.loads(cout)
        instance_id = response["Instances"][0]["InstanceId"]

        # Wait till instance is running
        timeout = 300
        log.info("Waiting till the instance starts")
        while get_instance_state(instance_id) != "running":
            log.info("Waiting %d more seconds" % timeout)

            time.sleep(3)
            timeout -= 3
            if timeout == 0:
                log.error("Failed to start instance. Timeout expired")
                return None

        if "Name" in instance_profile:
            if not add_name_tag(instance_id, instance_profile["Name"]):
                log.error("Failed to set Name tag on instance %s"
                          % instance_id)
                return None

        if "PublicIP" in instance_profile:
            public_ip = instance_profile['PublicIP']
            if not associate_address(instance_id, public_ip=public_ip):
                log.error("Failed to assign %s to instance %s"
                          % (public_ip, instance_id))
                return None

        # Wait will sshd is up
        ip = get_instance_private_ip(instance_id)

        username = instance_profile["UserName"]
        if not wait_sshd(ip, private_key_file, username):
            return None

        if 'BlockDeviceMappings' in instance_profile:
            mount_volumes(ip, private_key_file, username,
                          volumes=instance_profile['BlockDeviceMappings'])
        return instance_id
    except OSError as err:
        log.error(err)
        return None


def add_name_tag(instance_id, name):
    cmd = ["aws", "ec2", "create-tags",
           "--output", "json",
           "--resources", instance_id,
           "--tags", "Key=Name,Value=%s" % name
           ]
    try:
        aws_process = Popen(cmd, stdout=PIPE, stderr=PIPE)
        cout, cerr = aws_process.communicate()

        if aws_process.returncode != 0:
            log.error(cerr)
            return False

        return True
    except OSError as err:
        log.error(err)
        return False


def associate_address(instance_id, public_ip=None, private_ip=None):
    if public_ip or private_ip:
        cmd = ["aws", "ec2", "associate-address",
               "--output", "json",
               "--instance-id", instance_id]
        if public_ip:
            cmd += ["--public-ip", public_ip]
        if private_ip:
            cmd += ["--private-ip-address", private_ip]

        try:
            aws_process = Popen(cmd, stdout=PIPE, stderr=PIPE)
            cout, cerr = aws_process.communicate()

            if aws_process.returncode != 0:
                log.error(cerr)
                return False

            return True
        except OSError as err:
            log.error(err)
            return False


def terminate_ec2_instance(instance_id):
    cmd = ["aws", "ec2", "terminate-instances",
           "--instance-ids", instance_id
           ]
    try:
        log.debug("Executing: %r" % cmd)
        aws_process = Popen(cmd, stdout=PIPE, stderr=PIPE)
        cout, cerr = aws_process.communicate()

        if aws_process.returncode != 0:
            log.error(cerr)
            return False

        return True
    except OSError as err:
        log.error(err)
        return False


def mount_volumes(ip, key_file, username, volumes=None):
    for volume in volumes:
        log.info("Mounting %s" % volume['MountPoint'])
        call(["ssh", "-t", "-o", "StrictHostKeyChecking=no",
              "-o", "PasswordAuthentication=no",
              "-i", key_file, "-l", username, ip,
              "sudo mkfs.xfs %s" % volume['DeviceName']])

        call(["ssh", "-t", "-o", "StrictHostKeyChecking=no",
              "-o", "PasswordAuthentication=no",
              "-i", key_file, "-l", username, ip,
              "sudo mkdir -p %s; sudo mount %s %s"
              % (volume['MountPoint'],
                 volume['DeviceName'],
                 volume['MountPoint'])])


def start_instance(instance_id):
    """
    Start Amazon instance


    :param instance_id: id of instance for run
    :type instance_id: str
    :return: Result of start
    :rtype: bool
    """
    try:
        ec2 = boto3.resource('ec2')
    except ResourceNotExistsError:
        return False
    except UnknownAPIVersionError:
        return False
    try:
        instance = ec2.instances.filter(InstanceIds=[instance_id])
    except ClientError:
        return False
    try:
        response = instance.start()
    except ClientError:
        return False
    return response[0]['ResponseMetadata']['HTTPStatusCode'] == 200


def terminate_instance(instance_id):
    """
    Terminate Amazon instance


    :param instance_id: id of instance for terminate
    :type instance_id: str
    :return: Result of terminate
    :rtype: bool
    """
    try:
        ec2 = boto3.resource('ec2')
    except ResourceNotExistsError:
        return False
    except UnknownAPIVersionError:
        return False
    try:
        instance = ec2.instances.filter(InstanceIds=[instance_id])
    except ClientError:
        return False
    try:
        response = instance.terminate()
    except ClientError:
        return False
    return response[0]['ResponseMetadata']['HTTPStatusCode'] == 200


def stop_instance(instance_id):
    """
    Stop Amazon instance


    :param instance_id: id of instance for stop
    :type instance_id: str
    :return: Result of stop
    :rtype: bool
    """
    try:
        ec2 = boto3.resource('ec2')
    except ResourceNotExistsError:
        return False
    except UnknownAPIVersionError:
        return False
    try:
        instance = ec2.instances.filter(InstanceIds=[instance_id])
    except ClientError:
        return False
    try:
        response = instance.stop()
    except ClientError:
        return False
    return response[0]['ResponseMetadata']['HTTPStatusCode'] == 200
