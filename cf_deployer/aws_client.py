import boto3

def get_boto3_client(service, profile, region):
    """
    Create a boto3 client for the specified service, profile, and region.
    """
    session = boto3.Session(profile_name=profile, region_name=region)
    return session.client(service)

def get_cf_client(profile, region):
    """
    Get CloudFormation client.
    """
    return get_boto3_client("cloudformation", profile, region)

def get_ssm_client(profile, region):
    """
    Get SSM client.
    """
    return get_boto3_client("ssm", profile, region)
