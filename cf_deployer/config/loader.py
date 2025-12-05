import yaml
import logging
from typing import Dict, Any
from cf_deployer.config.models import EnvironmentConfig, TeamConfig, StackConfig
from cf_deployer.aws.ssm_cache import ParameterCache

logger = logging.getLogger(__name__)

class ConfigLoader:
    @staticmethod
    def load(path: str) -> EnvironmentConfig:
        """
        Load environment YAML config and convert to typed dataclasses.
        """
        with open(path, "r") as f:
            cfg = yaml.safe_load(f)

        required_keys = ["aws_profile", "region", "teams"]
        for key in required_keys:
            if key not in cfg:
                raise ValueError(f"Missing required key in config: {key}")

        teams = {}
        for team_name, team_cfg in cfg["teams"].items():
            stacks = []
            for s in team_cfg.get("stacks", []):
                stacks.append(StackConfig(
                    name=s["name"],
                    template=s["template"],
                    parameters=s.get("parameters", {})
                ))
            teams[team_name] = TeamConfig(name=team_name, stacks=stacks)

        return EnvironmentConfig(
            aws_profile=cfg["aws_profile"],
            region=cfg["region"],
            teams=teams
        )

    @staticmethod
    def resolve_parameters(params: Dict[str, Any], profile: str, region: str) -> Dict[str, Any]:
        """
        Resolve parameters using SSM and Secrets Manager cache.
        """
        def resolve(value):
            if isinstance(value, dict):
                return {k: resolve(v) for k, v in value.items()}
            if isinstance(value, list):
                return [resolve(v) for v in value]
            if isinstance(value, str):
                if value.startswith("SSM:"):
                    path = value[4:]
                    return ParameterCache.get_ssm(path, profile, region)
                if value.startswith("SECRET:"):
                    secret_name = value[7:]
                    return ParameterCache.get_secret(secret_name, profile, region)
            return value

        return {k: resolve(v) for k, v in params.items()}

    @staticmethod
    def extract_ssm_refs(params: Dict[str, Any]) -> list:
        """
        Return a list of all SSM paths used in parameters.
        """
        refs = []
        for v in params.values():
            if isinstance(v, str) and v.startswith("SSM:"):
                refs.append(v[4:])
            elif isinstance(v, dict):
                refs.extend(ConfigLoader.extract_ssm_refs(v))
            elif isinstance(v, list):
                for item in v:
                    if isinstance(item, dict) or isinstance(item, list):
                        refs.extend(ConfigLoader.extract_ssm_refs({str(i): item[i] for i in range(len(item))}))
        return refs
