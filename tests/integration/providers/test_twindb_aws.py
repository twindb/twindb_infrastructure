import pytest
import time

from twindb_infrastructure.providers.aws import launch_ec2_instance, terminate_instance, AwsError, get_instance_state, \
    ec2_describe_instance, add_name_tag, start_instance, get_instance_private_ip, get_instance_public_ip, stop_instance

AWS_INSTANCE_STATES = [
    'running',
    'shutting-down',
    'pending',
    'stopping',
    'stopped',
    'terminated',
    'rebooting',
]


@pytest.fixture(scope='session')
def instance_id(request):
    instance_profile = {
        "ImageId": "ami-405f7226",
        "InstanceType": "t2.micro",
        "KeyName": "travis-ci",
        "SecurityGroupIds": ["sg-086eb471"],
        "SubnetId": "subnet-339a797a",
        "RootVolumeSize": 200,
        "InstanceInitiatedShutdownBehavior": 'stop',
        "AvailabilityZone": "eu-west-1c",
        "UserName": "ubuntu",
        "Name": "integraion-test-01",
        "Region": "eu-west-1"
    }
    inst_id = launch_ec2_instance(instance_profile, region=instance_profile['Region'])
    assert get_instance_state(inst_id) == "running"

    def resource_teardown():
        terminate_instance(inst_id)
        time.sleep(2)
        assert get_instance_state(inst_id) == "shutting-down"

    request.addfinalizer(resource_teardown)
    return inst_id


def test_instance_state(instance_id):
    assert get_instance_state(instance_id) in AWS_INSTANCE_STATES


def test_describe_instance(instance_id):
    assert ec2_describe_instance(instance_id)


def test_add_name_tag(instance_id):
    assert add_name_tag(instance_id, 'Test name')
    response = ec2_describe_instance(instance_id)
    assert response["Reservations"][0]["Instances"][0]['Tags'][0]['Value'] == 'Test name'


def test_get_instance_private_ip(instance_id):
    assert get_instance_private_ip(instance_id)


def test_get_instance_public_ip(instance_id):
    assert get_instance_public_ip(instance_id)


def test_stop_start_instance(instance_id):
    stop_instance(instance_id)
    flag = False
    time_over = time.time() + 15 * 60
    while time.time() < time_over:
        if get_instance_state(instance_id) == "stopped":
            flag = True
            break
        time.sleep(1)
    assert flag
    start_instance(instance_id)
    flag = False
    time_over = time.time() + 15 * 60

    while time.time() < time_over:
        if get_instance_state(instance_id) == "running":
            flag = True
            break
        time.sleep(1)
    assert flag


