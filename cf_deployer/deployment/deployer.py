import logging
import signal
import time
from cf_deployer.aws.clients import AWSClientFactory
from cf_deployer.config.loader import ConfigLoader
from cf_deployer.deployment.stack_manager import StackManager

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def handle_interrupt(signum, frame):
    logger.warning("Deployment interrupted! Exiting cleanly.")
    exit(1)

signal.signal(signal.SIGINT, handle_interrupt)

def wait_for_ssm_parameters(ssm_client, parameter_paths, timeout=300):
    """
    Wait until all specified SSM parameters exist.
    """
    start = time.time()
    while True:
        all_exist = True
        for path in parameter_paths:
            try:
                ssm_client.get_parameter(Name=path)
            except ssm_client.exceptions.ParameterNotFound:
                all_exist = False

        if all_exist:
            return

        if time.time() - start > timeout:
            raise TimeoutError(f"Timeout waiting for SSM parameters: {parameter_paths}")

        time.sleep(5)

def run_deployment(env: str, team: str = None, stack: str = None, dry_run: bool = False):
    """
    Deploy all stacks for environment/team/stack with SSM & Secrets support.
    """
    cfg = ConfigLoader.load(f"configs/{env}.yaml")
    profile = cfg.aws_profile
    region = cfg.region

    cf = AWSClientFactory.get_cf_client(profile, region)
    ssm = AWSClientFactory.get_ssm_client(profile, region)
    manager = StackManager(cf)

    teams_to_deploy = {team: cfg.teams[team]} if team else cfg.teams

    for team_name, team_cfg in teams_to_deploy.items():
        logger.info(f"Deploying team '{team_name}' in environment '{env}'")

        for s in team_cfg.stacks:
            stack_name = f"{team_name}-{s.name}"
            if stack and stack != s.name:
                continue

            # Load template
            try:
                with open(s.template, "r") as f:
                    template_body = f.read()
            except FileNotFoundError:
                logger.error(f"Template not found: {s.template}")
                continue

            # Wait for any SSM parameter references
            ssm_refs = ConfigLoader.extract_ssm_refs(s.parameters)
            if ssm_refs:
                logger.info(f"Waiting for SSM parameters: {ssm_refs}")
                wait_for_ssm_parameters(ssm, ssm_refs)

            # Resolve parameters
            resolved_params = ConfigLoader.resolve_parameters(s.parameters, profile, region)

            # Mask secrets for logging
            masked_params = {
                k: ("***" if isinstance(v, str) and "SECRET:" in str(s.parameters.get(k, "")) else v)
                for k, v in resolved_params.items()
            }

            if dry_run:
                logger.info(f"[Dry-Run] Would deploy '{stack_name}' with parameters: {masked_params}")
                continue

            # Deploy stack
            manager.deploy(stack_name, template_body, resolved_params)

    logger.info(f"Deployment completed for environment '{env}'.")
