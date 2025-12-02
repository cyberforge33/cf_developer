import yaml
from cf_deployer.aws_client import get_ssm_client
import logging

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
        Resolve parameters, replacing SSM references with actual values.
        """
        resolved = {}
        ssm = get_ssm_client(profile, region)
        for key, val in params.items():
            resolved[key] = ConfigLoader._resolve_value(val, ssm)
        return resolved

    @staticmethod
    def _resolve_value(val, ssm_client):
        """
        If the value is a string starting with 'SSM:', fetch from Parameter Store.
        """
        if isinstance(val, str) and val.startswith("SSM:"):
            path = val[4:]
            param = ssm_client.get_parameter(Name=path)
            return param["Parameter"]["Value"]
        return val
