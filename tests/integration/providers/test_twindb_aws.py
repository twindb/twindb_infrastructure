import pytest

from twindb_infrastructure.providers.aws import launch_ec2_instance, terminate_instance, AwsError, get_instance_state, \
    ec2_describe_instance, add_name_tag, start_instance, get_instance_private_ip, get_instance_public_ip


@pytest.fixture(scope='session')
def instance_id(request):
    instance_profile = {
        "ImageId": "ami-a58d0dc5",
        "InstanceType": "t2.micro",
        "KeyName": "tester",
        "SecurityGroupIds": ["sg-7e3bd205"],
        "SubnetId": "subnet-f0190aa8",
        "RootVolumeSize": 200,
        "InstanceInitiatedShutdownBehavior": 'stop',
        "AvailabilityZone": "us-west-2c",
        "UserName": "ubuntu",
        "Name": "integraion-test-01",
        "Region": "us-west-2"
    }
    inst_id = launch_ec2_instance(instance_profile, region=instance_profile['Region'])

    def resource_teardown():
        terminate_instance(inst_id)

    request.addfinalizer(resource_teardown)
    return inst_id


def test_instance_state(instance_id):
    with not pytest.raises(AwsError):
        get_instance_state(instance_id)


def test_describe_instance(instance_id):
    with not pytest.raises(AwsError):
        ec2_describe_instance(instance_id)


def test_add_name_tag(instance_id):
    with not pytest.raises(AwsError):
        assert add_name_tag(instance_id)


def test_get_instance_private_ip(instance_id):
    with not pytest.raises(AwsError):
        get_instance_private_ip(instance_id)


def test_get_instance_public_ip(instance_id):
    with not pytest.raises(AwsError):
        get_instance_public_ip(instance_id)
