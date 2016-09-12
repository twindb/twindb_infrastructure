import os
import time
from botocore.exceptions import ClientError
from twindb_infrastructure.providers.aws.connection import AWSConnection


class AWSNetwork(object):
    """
    :type _aws_connection: AWSConnection
    """

    def __init__(self, aws_connection, zone):
        self._aws_connection = aws_connection
        self._ec2 = self._aws_connection.client('ec2')
        self._zone = zone

        self._default_vpc = None
        self._default_subnet = None

    def get_default_subnet(self):
        if self._default_subnet is None:
            vpc_id = self.get_default_vpc()

            if vpc_id is None:
                vpc_id = self._create_vpc()

            output = self._ec2.describe_subnets(
                Filters=[
                    {'Name': 'availabilityZone', 'Values': [self._zone]},
                    {'Name': 'state', 'Values': ['available']},
                    {'Name': 'vpc-id', 'Values': [vpc_id]}
                ]
            )

            if not output:
                return None

            if len(output['Subnets']) < 1:
                self._default_subnet = self._create_subnet()
            else:
                self._default_subnet = output['Subnets'].pop()['SubnetId']

        return self._default_subnet

    def get_default_vpc(self):
        if self._default_vpc is None:
            output = self._ec2.describe_vpcs(
                Filters=[
                    {'Name': 'state', 'Values': ['available']}
                ]
            )

            if not output:
                return None

            if len(output['Vpcs']) < 1:
                return None

            self._default_vpc = output['Vpcs'].pop()['VpcId']

        return self._default_vpc

    def _create_vpc(self):
        output = self._ec2.create_vpc(CidrBlock='10.0.0.0/16', InstanceTenancy='default')
        vpc_id = output['Vpc']['VpcId']

        # We wait for the VPC to be ready in 300 seconds
        timeout = 300
        while timeout > 0:
            output = self._ec2.describe_vpcs(
                VpcIds=[vpc_id],
                Filters=[
                    {'Name': 'state', 'Values': ['available']}
                ]
            )

            if len(output['Vpcs']) > 0:
                break

            time.sleep(2)
            timeout -= 1

        """By default, instances launched in non-default VPCs are assigned an
        unresolavable hostname. Setting the enableDnsHostnames attribute to
        'true' on the VPC resolves this. See:
        http://docs.aws.amazon.com/AmazonVPC/latest/UserGuide/VPC_DHCP_Options.html
        """
        output = self._ec2.modify_vpc_attribute(VpcId=vpc_id, EnableDnsHostnames=True)

        # If the timeout expired then we return an error
        if timeout < 0:
            return False

        return vpc_id

    def _create_subnet(self, vpc_id):
        output = self._ec2.create_subnet(VpcId=vpc_id, CidrBlock='10.0.0.0/24', AvailabilityZone=self._zone)
        subnet_id = output['Subnet']['SubnetId']

        # We wait for the VPC to be ready in 300 seconds
        timeout = 300
        while timeout > 0:
            output = self._ec2.describe_subnets(
                SubnetIds=[subnet_id],
                Filters=[
                    {'Name': 'state', 'Values': ['available']}
                ]
            )

            if len(output['Subnets']) > 0:
                break

            time.sleep(2)
            timeout -= 1

        # If the timeout expired then we return an error
        if timeout < 0:
            return False

        return subnet_id


class AWSFirewall(object):
    DEFAULT_SECURITY_GROUP_NAME = 'default_security_group'
    DEFAULT_SECURITY_GROUP_DESC = 'Default Security Group'

    def __init__(self, aws_connection, aws_network):
        """
        :param AWSConnection aws_connection: connection object that returns connection to AWS
        """
        self._aws_connection = aws_connection

        """
        :param AWSNetwork aws_network: network object that provides AWS VPC subnet API abstraction
        """
        self._aws_network = aws_network

        self._ec2 = self._aws_connection.client('ec2')
        self._default_group = None
        self._firewall_set = set()

    def get_default_security_group(self):
        if self._default_group is None:
            self._default_group = self._create_security_group(self.DEFAULT_SECURITY_GROUP_NAME,
                                                              self.DEFAULT_SECURITY_GROUP_DESC)

        return self._default_group

    def cleanup(self):
        return self._delete_security_group()

    def allow_port(self, port):
        if port in self._firewall_set:
            return True

        for protocol in ['tcp', 'udp']:
            self._ec2.authorize_security_group_ingress(GroupId=self._default_group, FromPort=port, ToPort=port,
                                                       CidrIp='0.0.0.0/0', IpProtocol=protocol)

        self._firewall_set.add(port)

        return True

    def _create_security_group(self, group_name, group_description):
        vpc_id = self._aws_network.get_default_vpc()
        output = self._ec2.create_security_group(GroupName=group_name, Description=group_description, VpcId=vpc_id)

        group_id = output['GroupId']

        # We wait for the VPC to be ready in 300 seconds
        timeout = 300
        while timeout > 0:
            try:
                output = self._ec2.describe_security_groups(
                    GroupIds=[group_id],
                    Filters=[
                        {'Name': 'vpc-id', 'Values': [vpc_id]}
                    ]
                )
            except ClientError as e:
                continue

            if len(output['SecurityGroups']) > 0:
                break

            time.sleep(2)
            timeout -= 1

        # If the timeout expired then we return an error
        if timeout < 0:
            return False

        return group_id

    def _delete_security_group(self):
        self._ec2.delete_security_group(GroupId=self._default_group)
        return True
