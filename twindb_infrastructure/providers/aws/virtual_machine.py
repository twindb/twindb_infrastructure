import time
from twindb_infrastructure.providers.aws.connection import AWSConnection
from twindb_infrastructure.providers.aws.network import AWSNetwork, AWSFirewall
from twindb_infrastructure.providers.aws.ssh import AWSSsh

HVM = 'HVM'
PV = 'PV'
NON_HVM_PREFIXES = ['m1', 'c1', 't1', 'm2']
INSTANCE_EXISTS_STATUSES = frozenset(
    ['pending', 'running', 'stopping', 'stopped'])
INSTANCE_DELETED_STATUSES = frozenset(['shutting-down', 'terminated'])
INSTANCE_KNOWN_STATUSES = INSTANCE_EXISTS_STATUSES | INSTANCE_DELETED_STATUSES


class AWSVirtualMachine(object):
    """
    :type _connection: AWSConnection
    :type _network: AWSNetwork
    :type _firewall: AWSFirewall
    :type _ssh: AWSSsh
    :type _vm_spec: VMSpec
    """

    def __init__(self, vm_spec, aws_connection, aws_network, aws_firewall, aws_ssh):
        self._vm_spec = vm_spec

        self._connection = aws_connection
        self._network = aws_network
        self._firewall = aws_firewall
        self._ssh = aws_ssh

        self._id = None
        self._instance_type = self._vm_spec.instance_type
        self._ip_address = None
        self._internal_ip = None
        self._dns_name = None
        self._zone = None

        self._ssh_port = self._ssh.ssh_port
        self._ssh_username = self._ssh.ssh_username
        self._ssh_key_file_path = self._ssh.ssh_key_file_path

        if self._get_instance_virt_type() != HVM:
            raise ValueError('Non-HVM instance type not supported')

        self._ec2 = self._connection.client('ec2')

    @property
    def id(self):
        return self._id

    @property
    def instance_type(self):
        return self._instance_type

    @property
    def ip_address(self):
        return self._ip_address

    @property
    def internal_ip(self):
        return self._internal_ip

    @property
    def dns_name(self):
        return self._dns_name

    @property
    def zone(self):
        return self._zone

    def create(self):
        if not self._ssh.exists_ssh_key():
            self._ssh.create_ssh_key()

        default_ami = self.get_default_ami()

        output = self._ec2.run_instances(
            SubnetId=self._network.get_default_subnet(),
            ImageId=default_ami,
            InstanceType=self._instance_type,
            KeyName=self._ssh.ssh_key_name,
            SecurityGroupIds=[self._firewall.get_default_security_group()],
            MinCount=1,
            MaxCount=1,
            InstanceInitiatedShutdownBehavior='terminate',
            EbsOptimized=self._vm_spec.ebs_optimized
        )

        self._id = output['Instances'][0]['InstanceId']

        # We wait for the instance to be ready in 300 seconds
        timeout = 300
        while timeout > 0:
            output = self._ec2.describe_instances(
                InstanceIds=[self._id],
                Filters=[
                    {'Name': 'instance-state-name', 'Values': ['running']}
                ]
            )

            if len(output['Reservations']) > 0:
                instance = output['Reservations'][0]['Instances'][0]
                self._ip_address = instance['PublicIpAddress']
                self._internal_ip = instance['PrivateIpAddress']
                self._dns_name = instance['PublicDnsName']
                self._zone = str(instance['Placement']['AvailabilityZone'])

                break

            time.sleep(15)
            timeout -= 1

        # If the timeout expired then we return an error
        if timeout < 0:
            return False

        # Open up access to port 22 to allow SSH
        self._firewall.allow_port(self._ssh_port)

        return True

    def delete(self):
        self._ec2.terminate_instances(
            InstanceIds=[self._id]
        )

        retries = 0
        while retries < 10:
            if not self.exists():
                break

            time.sleep(2 ^ retries * 0.1)
            retries += 1

        return True

    def exists(self):
        if self._id is None:
            return False

        output = self._ec2.describe_instances(
            InstanceIds=[self._id]
        )

        if len(output['Reservations']) > 0:
            instances = output['Reservations'][0]['Instances']
            status = instances[0]['State']['Name']
            return status in INSTANCE_EXISTS_STATUSES

        return False

    def get_default_ami(self):
        prefix = self._instance_type.split('.')[0]
        virt_type = 'paravirtual' if prefix in NON_HVM_PREFIXES else 'hvm'

        output = self._ec2.describe_images(
            Owners=['amazon'],
            Filters=[
                {'Name': 'name', 'Values': ['amzn-ami-%s*' % virt_type]},
                {'Name': 'architecture', 'Values': ['x86_64']},
                {'Name': 'block-device-mapping.volume-type', 'Values': ['standard']},
                {'Name': 'virtualization-type', 'Values': [virt_type]}
            ]
        )

        if not output:
            return None

        images = output['Images']

        # We want to return the latest version of the image, and since the wildcard
        # portion of the image name is the image's creation date, we can just take
        # the image with the 'largest' name.
        return max(images, key=lambda image: image['Name'])['ImageId']

    def _get_instance_virt_type(self):
        prefix = self._instance_type.split('.')[0]
        virt_type = PV if prefix in NON_HVM_PREFIXES else HVM

        return virt_type


class VMSpec(object):
    def __init__(self, instance_type, ebs_optimized, ebs_volumes, allowed_ports):
        """Creates an object that stores specification for a VM

        :param str instance_type: Type of instance
        :param bool ebs_optimized: Whether the instance is to be launched as an EBS optimized instance
        :param list ebs_volumes: List of volumes
        :param list allowed_ports: List of ports to be opened up in security group
        """
        self.instance_type = instance_type
        self.ebs_optimized = ebs_optimized
        self.ebs_volumes = ebs_volumes
        self.allowed_ports = allowed_ports
