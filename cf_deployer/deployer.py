import logging
import signal
from cf_deployer.aws_client import get_cf_client, get_ssm_client
from cf_deployer.stack_manager import StackManager
from cf_deployer.config_loader import ConfigLoader
import time

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

# Handle Ctrl+C gracefully
def handle_interrupt(signum, frame):
    logger.warning("Deployment interrupted! Exiting cleanly.")
    exit(1)

signal.signal(signal.SIGINT, handle_interrupt)

# ---- SSM Utilities ----
def write_outputs_to_ssm(outputs, stack_name, team_name, env, profile, region):
    """
    Write CloudFormation outputs to SSM for cross-stack references.
    """
    ssm = get_ssm_client(profile, region)
    for key, value in outputs.items():
        param_name = f"/cf-deployer/{env}/{team_name}/{stack_name}/{key}"
        if len(str(value)) > 4000:
            logger.error(f"Output {key} too large for SSM (<4KB). Skipping.")
            continue
        ssm.put_parameter(Name=param_name, Value=str(value), Type="String", Overwrite=True)
        logger.debug(f"Wrote {param_name} to SSM.")

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

# ---- Deployment Orchestration ----
def run_deployment(env, team=None, stack=None, dry_run=False):
    """
    Orchestrate deployment of all stacks for the specified environment and optional team/stack.
    """
    cfg = ConfigLoader.load(f"configs/{env}.yaml")
    profile = cfg["aws_profile"]
    region = cfg["region"]

    cf = get_cf_client(profile, region)
    manager = StackManager(cf)
    ssm = get_ssm_client(profile, region)

    teams_to_deploy = {team: cfg["teams"][team]} if team else cfg["teams"]

    for team_name, team_cfg in teams_to_deploy.items():
        logger.info(f"Deploying stacks for {team_name} in {env}")

        for s in team_cfg["stacks"]:
            stack_name = f"{team_name}-{s['name']}"
            if stack and stack != s["name"]:
                continue

            # Resolve template body
            with open(s["template"], "r") as f:
                template_body = f.read()

            # Resolve parameters (SSM references)
            resolved_params = ConfigLoader.resolve_parameters(
                s.get("parameters", {}), team_name, env, profile, region
            )

            # Wait for SSM parameters if any reference exists
            ssm_refs = [v[4:] for v in s.get("parameters", {}).values() if isinstance(v, str) and v.startswith("SSM:")]
            if ssm_refs:
                wait_for_ssm_parameters(ssm, ssm_refs)

            if dry_run:
                logger.info(f"Dry-run: would deploy {stack_name} with parameters {resolved_params}")
                continue

            # Deploy the stack
            manager.deploy(stack_name, template_body, resolved_params)

            # Write outputs to SSM for downstream stacks
            outputs = manager.get_outputs(stack_name)
            write_outputs_to_ssm(outputs, s["name"], team_name, env, profile, region)

    logger.info(f"Deployment for {env} completed successfully.")
