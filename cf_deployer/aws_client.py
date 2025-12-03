import boto3

def get_boto3_client(service, profile, region):
    session = boto3.Session(profile_name=profile, region_name=region)
    return session.client(service)

def get_cf_client(profile, region):
    return get_boto3_client("cloudformation", profile, region)

def get_ssm_client(profile, region):
    return get_boto3_client("ssm", profile, region)

def get_secrets_client(profile, region):
    return get_boto3_client("secretsmanager", profile, region)
