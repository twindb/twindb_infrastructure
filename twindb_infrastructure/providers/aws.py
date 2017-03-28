from subprocess import call
import time
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


class AwsError(Exception):
    """General error in AWS"""


def ec2_describe_instance(instance_id):
    """
    Describe EC2 instance by instance id and return an object with its
    properties

    :param instance_id: Instance id
    :type instance_id: str
    :raise: AwsError
    :return: object with instance properties
    :rtype: dict
    """
    try:
        client = boto3.client('ec2')
        return client.describe_instances(InstanceIds=[instance_id])
    except ClientError as err:
        raise AwsError(err)
    except ValueError as err:
        raise AwsError('Internal bug in boto3: %s', err)


def get_instance_state(instance_id):
    """
    Get state of instance by instance id

    :param instance_id: Instance id
    :type instance_id: str
    :raise: AwsError
    :return: instance state
    :rtype str
    """
    try:
        response = ec2_describe_instance(instance_id)
        state = response["Reservations"][0]["Instances"][0]["State"]["Name"]
        log.debug("Instance: %s, State: %s" % (instance_id, state))
        return state
    except AwsError as err:
        raise err


def get_instance_private_ip(instance_id):
    """
    Get private IP of instance by instance id

    :param instance_id: Instance id
    :type instance_id: str
    :raise: AwsError
    :return: private ip address of instance
    :rtype str
    """
    try:
        response = ec2_describe_instance(instance_id)
        return response["Reservations"][0]["Instances"][0]["PrivateIpAddress"]
    except AwsError as err:
        raise err


def get_instance_public_ip(instance_id):
    """
    Get public IP of instance by instance id

    :param instance_id: Instance id
    :type instance_id: str
    :raise: AwsError
    :return: public ip address of instance
    :rtype str
    """
    try:
        response = ec2_describe_instance(instance_id)
        return response["Reservations"][0]["Instances"][0]["PublicIpAddress"]
    except AwsError as err:
        raise err


def launch_ec2_instance(instance_profile, region=AWS_REGIONS[0], private_key_file=None):
    """
    Launch instance

    :param instance_profile: Instance profile
    :param private_key_file: Private key file
    :param region: Region name
    :type instance_profile: dict
    :type private_key_file: str
    :type region: str
    :raise AwsError:
    :return: Instance id
    :rtype: str
    """
    try:
        client = boto3.client('ec2', region_name=region)
    except ClientError as err:
        raise AwsError(err)

    client_args = {
        'ImageId': instance_profile['ImageId'],
        'InstanceType': instance_profile['InstanceType'],
        'KeyName': instance_profile['KeyName'],
        'SubnetId': instance_profile["SubnetId"],
    }
    security_group_ids = list(instance_profile['SecurityGroupIds'])

    client_args['SecurityGroupIds'] = security_group_ids

    if instance_profile.get('MinCount'):
        client_args['MinCount'] = instance_profile["MinCount"]
    else:
        client_args['MinCount'] = 1

    if instance_profile.get('MaxCount'):
        client_args['MaxCount'] = instance_profile["MaxCount"]
    else:
        client_args['MaxCount'] = 1

    if instance_profile.get('AvailabilityZone'):
        client_args['Placement'] = {
            'AvailabilityZone': instance_profile['AvailabilityZone']
        }

    if instance_profile.get('EbsOptimized', False):
        client_args['EbsOptimized'] = True

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

    client_args['BlockDeviceMappings'] = device_mappings
    try:
        response = client.run_instances(**client_args)
    except ClientError as err:
        raise AwsError(err)

    try:
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
            try:
                add_name_tag(instance_id, instance_profile["Name"])
            except AwsError as err:
                raise err

        if "PublicIP" in instance_profile:
            public_ip = instance_profile['PublicIP']
            try:
                associate_address(instance_id, public_ip=public_ip)
            except AwsError as err:
                raise err

        # Wait will sshd is up
        try:
            ip = get_instance_public_ip(instance_id)
        except AwsError as err:
            raise err
        username = instance_profile["UserName"]
        if not wait_sshd(ip, private_key_file, username):
            return None

        if 'BlockDeviceMappings' in instance_profile:
            mount_volumes(ip, private_key_file, username,
                          volumes=instance_profile['BlockDeviceMappings'])
        return instance_id
    except AwsError as err:
        raise AwsError(err)


def add_name_tag(instance_id, name):
    """
    Added tag to instance

    :param instance_id: Instance id
    :param name: Tag for instance
    :type instance_id: str
    :type name: str
    :raise: AwsError
    :return: Result of setting tag
    :rtype: bool
    """
    try:
        client = boto3.client('ec2')
        response = client.create_tags(
            Resources=[instance_id],
            Tags=[
                {
                    'Key': 'Name',
                    'Value': name
                }
            ]
        )
        return response['ResponseMetadata']['HTTPStatusCode'] == 200
    except ClientError as err:
        raise AwsError(err)
    except ValueError as err:
        raise AwsError('Internal bug in boto3: %s', err)


def associate_address(instance_id, public_ip=None, private_ip=None):
    """
    Associates an Elastic IP address with an instance

    :param instance_id: Instance id
    :param public_ip: Public ip
    :param private_ip: Private ip
    :type instance_id: str
    :type public_ip: str
    :type private_ip: str
    :raise: AwsError
    """

    kwargs = {
        'InstanceId': instance_id
    }
    if public_ip or private_ip:
        try:
            client = boto3.client('ec2')

            if public_ip:
                kwargs['PublicIp'] = public_ip

            if private_ip:
                kwargs['PrivateIpAddress'] = private_ip

            client.associate_address(**kwargs)

        except ClientError as err:
            raise AwsError(err)
        except ValueError as err:
            raise AwsError('Internal bug in boto3: %s', err)
    else:
        return None


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
