"""Utilities for working with Amazon Web Services resources."""

# Values taken from
# http://docs.aws.amazon.com/AWSEC2/latest/UserGuide/using-regions-availability-zones.html
REGIONS = ['us-east-1',
           'us-west-2',
           'us-west-1',
           'eu-west-1',
           'eu-central-1',
           'ap-southeast-1',
           'ap-northeast-1',
           'ap-southeast-2',
           'ap-northeast-2',
           'sa-east-1']


def is_region(param):
    """
    Check if input parameter is a region name
    :param param: string with a name
    :return: True if param is a valid region name
    """
    return param in REGIONS


def is_valid_zone(zone):
    """
    Check if the parameter is a correct zone
    :param zone: the name of the zone
    :return: True if the region for the zone exists, false otherwise
    """
    return is_region(zone[:-1])


def get_region(param):
    """
    Extract region name from zone name
    :param param: zone name or region name
    :return: region name or None if error
    """
    # Handle None input
    if not param:
        return None

    if is_region(param):
        return param
    elif is_region(param[:-1]):
        return param[:-1]
    else:
        return None
