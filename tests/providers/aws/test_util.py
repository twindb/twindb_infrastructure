from twindb_infrastructure.providers.aws import util


def test__region_name_is_validated():
    assert util.is_region('incorrect-region') == False
    assert util.is_region('us-east-1')


def test__zone_name_is_validated():
    assert util.is_valid_zone('incorrect-zone') == False
    assert util.is_valid_zone('us-east-1a')


def test__get_region_returns_valid_region_name():
    assert util.get_region('invalid-zone') is None
    assert util.get_region('us-east-1a') == 'us-east-1'
