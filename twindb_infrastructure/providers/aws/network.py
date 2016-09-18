import boto3
import time
from botocore.exceptions import ClientError
from twindb_infrastructure.providers.aws.connection import AWSConnection


class AWSNetwork(object):
    """
    :type _aws_connection: AWSConnection
    """

    def __init__(self, aws_connection, zone):
        self._aws_connection = aws_connection
        self._zone = zone

        self.ec2_client = self._aws_connection.client('ec2')
        self.ec2_resource = boto3.resource('ec2')

        self._default_vpc = None
        self._default_subnet = None

    def get_default_vpc(self):
        if self._default_vpc is None:
            output = self.ec2_client.describe_vpcs(
                Filters=[
                    {'Name': 'state', 'Values': ['available']}
                ]
            )

            if not output:
                return None

            vpcs = output['Vpcs']

            self._default_vpc = self.create_vpc() if len(vpcs) < 1 else self.ec2_resource.Vpc(vpcs.pop()['VpcId'])

        return self._default_vpc

    def create_vpc(self):
        output = self.ec2_client.create_vpc(CidrBlock='10.0.0.0/16', InstanceTenancy='default')
        vpc_id = output['Vpc']['VpcId']

        # We wait for the VPC to be ready in 300 seconds
        timeout = 300
        while timeout > 0:
            output = self.ec2_client.describe_vpcs(
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
        self.ec2_client.modify_vpc_attribute(VpcId=vpc_id, EnableDnsHostnames={'Value': True})

        # If the timeout expired then we return an error
        if timeout < 0:
            return False

        return self.ec2_resource.Vpc(vpc_id)

    def get_default_subnet(self):
        if self._default_subnet is None:
            vpc = self.get_default_vpc()

            output = self.ec2_client.describe_subnets(
                Filters=[
                    {'Name': 'availabilityZone', 'Values': [self._zone]},
                    {'Name': 'vpc-id', 'Values': [vpc.id]}
                ]
            )

            if not output:
                return None

            subnets = output['Subnets']

            self._default_subnet = self.create_subnet(vpc.id) if len(subnets) < 1 else \
                self.ec2_resource.Subnet(subnets.pop()['SubnetId'])

        return self._default_subnet

    def create_subnet(self, vpc_id):
        output = self.ec2_client.create_subnet(VpcId=vpc_id, CidrBlock='10.0.0.0/24', AvailabilityZone=self._zone)
        subnet_id = output['Subnet']['SubnetId']

        # We wait for the VPC to be ready in 300 seconds
        timeout = 300
        while timeout > 0:
            output = self.ec2_client.describe_subnets(
                SubnetIds=[subnet_id],
                Filters=[]
            )

            if len(output['Subnets']) > 0:
                break

            time.sleep(2)
            timeout -= 1

        # If the timeout expired then we return an error
        if timeout < 0:
            return False

        return self.ec2_resource.Subnet(subnet_id)


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

        self.ec2_client = self._aws_connection.client('ec2')
        self.ec2_resource = boto3.resource('ec2')

        self._default_group = None
        self._firewall_set = set()

    def get_default_security_group(self):
        if self._default_group is None:
            vpc = self._aws_network.get_default_vpc()

            output = self.ec2_client.describe_security_groups(
                Filters=[
                    {'Name': 'group-name', 'Values': [self.DEFAULT_SECURITY_GROUP_NAME]},
                    {'Name': 'vpc-id', 'Values': [vpc.id]}
                ]
            )

            if not output:
                return None

            security_groups = output['SecurityGroups']
            if len(security_groups) < 1:
                self._default_group = self.create_security_group(self.DEFAULT_SECURITY_GROUP_NAME,
                                                                 self.DEFAULT_SECURITY_GROUP_DESC)
            else:
                self._default_group = self.ec2_resource.SecurityGroup(security_groups.pop()['GroupId'])

        return self._default_group

    def create_security_group(self, group_name, group_description):
        vpc = self._aws_network.get_default_vpc()
        output = self.ec2_client.create_security_group(GroupName=group_name, Description=group_description,
                                                       VpcId=vpc.id)

        group_id = output['GroupId']

        # We wait for the VPC to be ready in 300 seconds
        timeout = 300
        while timeout > 0:
            try:
                output = self.ec2_client.describe_security_groups(
                    GroupIds=[group_id],
                    Filters=[
                        {'Name': 'vpc-id', 'Values': [vpc.id]}
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

        return self.ec2_resource.SecurityGroup(group_id)

    def cleanup(self):
        return self.delete_security_group()

    def allow_port(self, port, cidr_ip='0.0.0.0/0', protocol='tcp'):
        if port in self._firewall_set:
            return True

        self.ec2_client.authorize_security_group_ingress(GroupId=self.get_default_security_group().id,
                                                         IpPermissions=[{
                                                             'IpProtocol': protocol,
                                                             'FromPort': port,
                                                             'ToPort': port,
                                                             'IpRanges': [
                                                                 {'CidrIp': cidr_ip}
                                                             ]
                                                         }])

        self._firewall_set.add(port)

        return True

    def delete_security_group(self):
        if self._default_group is not None:
            self.ec2_client.delete_security_group(GroupId=self._default_group.id)
            self._default_group = None

        return True
