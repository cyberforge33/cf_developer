import threading
from cf_deployer.aws.clients import AWSClientFactory
import base64
import logging

logger = logging.getLogger(__name__)


class ParameterCache:
    """
    In-memory cache for SSM parameters and Secrets Manager secrets.
    Thread-safe for synchronous deployment.
    """
    _ssm_cache = {}
    _secret_cache = {}
    _lock = threading.Lock()

    @classmethod
    def get_ssm(cls, path: str, profile: str, region: str):
        key = (profile, region, path)
        with cls._lock:
            if key in cls._ssm_cache:
                return cls._ssm_cache[key]

            ssm_client = AWSClientFactory.get_ssm_client(profile, region)
            try:
                response = ssm_client.get_parameter(Name=path, WithDecryption=True)
                value = response["Parameter"]["Value"]
                cls._ssm_cache[key] = value
                return value
            except ssm_client.exceptions.ParameterNotFound:
                logger.error(f"SSM Parameter not found: {path}")
                raise

    @classmethod
    def get_secret(cls, name: str, profile: str, region: str):
        key = (profile, region, name)
        with cls._lock:
            if key in cls._secret_cache:
                return cls._secret_cache[key]

            secrets_client = AWSClientFactory.get_secrets_client(profile, region)
            try:
                resp = secrets_client.get_secret_value(SecretId=name)
                if "SecretString" in resp:
                    value = resp["SecretString"]
                else:
                    value = base64.b64decode(resp["SecretBinary"]).decode("utf-8")
                cls._secret_cache[key] = value
                return value
            except secrets_client.exceptions.ResourceNotFoundException:
                logger.error(f"Secret not found: {name}")
                raise
