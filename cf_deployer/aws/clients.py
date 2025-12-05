import boto3
from functools import lru_cache

class AWSClientFactory:
    """
    Factory to create boto3 clients with optional caching.
    """

    @staticmethod
    @lru_cache(maxsize=None)
    def get_client(service: str, profile: str, region: str):
        """
        Returns a cached boto3 client for the given service/profile/region.
        """
        session = boto3.Session(profile_name=profile, region_name=region)
        return session.client(service)

    @staticmethod
    def get_cf_client(profile: str, region: str):
        return AWSClientFactory.get_client("cloudformation", profile, region)

    @staticmethod
    def get_ssm_client(profile: str, region: str):
        return AWSClientFactory.get_client("ssm", profile, region)

    @staticmethod
    def get_secrets_client(profile: str, region: str):
        return AWSClientFactory.get_client("secretsmanager", profile, region)
