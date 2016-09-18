from twindb_infrastructure.providers.aws import network
from moto import mock_ec2


@mock_ec2
def test__network_create_vpc_creates_the_vpc(aws_connection, aws_zone):
    aws_network = network.AWSNetwork(aws_connection, aws_zone)

    vpc = aws_network.create_vpc()

    assert 'vpc-' in vpc.id
    assert aws_network.get_default_vpc().id == vpc.id

    vpcs = aws_network.ec2_client.describe_vpcs(VpcIds=[vpc.id])
    assert len(vpcs['Vpcs']) == 1

    assert vpc.cidr_block == '10.0.0.0/16'
    assert vpc.instance_tenancy == 'default'
    assert vpc.is_default

    response = vpc.describe_attribute(Attribute='enableDnsHostnames')
    attr = response.get('EnableDnsHostnames')
    assert attr.get('Value')


@mock_ec2
def test__network_get_default_vpc_creates_vpc_if_does_not_exist(aws_connection, aws_zone):
    aws_network = network.AWSNetwork(aws_connection, aws_zone)

    vpc = aws_network.get_default_vpc()
    assert 'vpc-' in vpc.id


@mock_ec2
def test__network_create_subnet_creates_the_subnet(aws_connection, aws_zone):
    aws_network = network.AWSNetwork(aws_connection, aws_zone)

    vpc = aws_network.get_default_vpc()
    subnet = aws_network.create_subnet(vpc.id)

    assert 'subnet-' in subnet.id
    assert aws_network.get_default_subnet().id == subnet.id

    subnets = aws_network.ec2_client.describe_subnets(SubnetIds=[subnet.id])
    assert len(subnets['Subnets']) == 1

    assert subnet.vpc_id == vpc.id
    assert subnet.cidr_block == '10.0.0.0/24'
    assert subnet.availability_zone == aws_zone


@mock_ec2
def test__network_get_default_subnet_creates_subnet_if_does_not_exist(aws_connection, aws_zone):
    aws_network = network.AWSNetwork(aws_connection, aws_zone)

    subnet = aws_network.get_default_subnet()
    assert 'subnet-' in subnet.id


@mock_ec2
def test__network_create_firewall_creates_the_firewall(aws_connection, aws_zone):
    aws_network = network.AWSNetwork(aws_connection, aws_zone)
    aws_firewall = network.AWSFirewall(aws_connection, aws_network)

    security_group = aws_firewall.create_security_group(aws_firewall.DEFAULT_SECURITY_GROUP_NAME, 'Testing group')

    assert 'sg-' in security_group.id
    assert aws_firewall.get_default_security_group().id == security_group.id

    groups = aws_network.ec2_client.describe_security_groups(GroupIds=[security_group.id])
    assert len(groups['SecurityGroups']) == 1

    assert security_group.vpc_id == aws_network.get_default_vpc().id
    assert security_group.group_name == aws_firewall.DEFAULT_SECURITY_GROUP_NAME


@mock_ec2
def test__network_cleanup_firewall_deletes_security_group(aws_connection, aws_zone):
    aws_network = network.AWSNetwork(aws_connection, aws_zone)
    aws_firewall = network.AWSFirewall(aws_connection, aws_network)

    aws_firewall.get_default_security_group()
    aws_firewall.cleanup()

    assert aws_firewall._default_group is None


@mock_ec2
def test__network_firewall_allow_port_opens_up_the_port(aws_connection, aws_zone):
    aws_network = network.AWSNetwork(aws_connection, aws_zone)
    aws_firewall = network.AWSFirewall(aws_connection, aws_network)

    aws_firewall.create_security_group(aws_firewall.DEFAULT_SECURITY_GROUP_NAME, 'Testing group')
    aws_firewall.allow_port(22, '10.0.0.0/0', 'udp')

    security_group = aws_firewall.get_default_security_group()

    assert len(security_group.ip_permissions) == 1
    assert security_group.ip_permissions[0]['FromPort'] == 22
    assert security_group.ip_permissions[0]['IpProtocol'] == 'udp'
