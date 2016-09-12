import boto3
from twindb_infrastructure.providers.aws import util

US_EAST_1 = 'us-east-1'
US_WEST_1 = 'us-west-1'
US_WEST_2 = 'us-west-2'
EU_WEST_1 = 'eu-west-1'
AP_NORTHEAST_1 = 'ap-northeast-1'
AP_SOUTHEAST_1 = 'ap-southeast-1'
AP_SOUTHEAST_2 = 'ap-southeast-2'
SA_EAST_1 = 'sa-east-1'


class AWSConnection(object):
    def __init__(self, aws_access_key_id, aws_secret_access_key, region):
        self._aws_access_key_id = aws_access_key_id
        self._aws_secret_access_key = aws_secret_access_key

        if not util.is_region(region):
            raise ValueError('Incorrect region %s passed' % region)

        self._region = region

    def get_connection(self):
        session = boto3.Session(aws_access_key_id=self._aws_access_key_id,
                                aws_secret_access_key=self._aws_secret_access_key, region_name=self._region)

        return session

    @property
    def region(self):
        return self._region
