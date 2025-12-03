import yaml
import logging
import base64

logger = logging.getLogger(__name__)

class ConfigLoader:

    @staticmethod
    def load(path):
        """
        Load environment YAML config.
        """
        with open(path, "r") as f:
            cfg = yaml.safe_load(f)

        required_keys = ["aws_profile", "region", "teams"]
        for k in required_keys:
            if k not in cfg:
                raise ValueError(f"Missing required key in config: {k}")
        return cfg

    @staticmethod
    def resolve_parameters(params, team_name, env, profile, region):
        """
        Resolve parameters:
        - Fetch SSM parameter values
        - Fetch Secrets Manager secrets as actual values
        """
        # Lazy imports to avoid circular import
        from cf_deployer.aws_client import get_ssm_client, get_secrets_client

        ssm = get_ssm_client(profile, region)
        secrets = get_secrets_client(profile, region)

        def resolve(val):
            if isinstance(val, dict):
                return {k: resolve(v) for k, v in val.items()}
            if isinstance(val, list):
                return [resolve(v) for v in val]

            if isinstance(val, str):
                if val.startswith("SSM:"):
                    path = val[4:]
                    param = ssm.get_parameter(Name=path, WithDecryption=True)
                    return param["Parameter"]["Value"]

                if val.startswith("SECRET:"):
                    secret_name = val[7:]
                    resp = secrets.get_secret_value(SecretId=secret_name)
                    if "SecretString" in resp:
                        return resp["SecretString"]
                    else:
                        return base64.b64decode(resp["SecretBinary"]).decode("utf-8")

            return val

        return {k: resolve(v) for k, v in params.items()}

    @staticmethod
    def extract_ssm_refs(params):
        """
        Return a list of all SSM paths used in parameters.
        """
        refs = []
        for v in params.values():
            if isinstance(v, str) and v.startswith("SSM:"):
                refs.append(v[4:])
        return refs
