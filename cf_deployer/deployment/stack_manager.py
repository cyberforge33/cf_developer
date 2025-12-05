import botocore
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class StackManager:
    """
    Manages CloudFormation stack operations with ChangeSets.
    """

    def __init__(self, cf_client):
        self.cf = cf_client

    def exists(self, stack_name: str) -> bool:
        """
        Check if a CloudFormation stack exists.
        """
        try:
            self.cf.describe_stacks(StackName=stack_name)
            return True
        except botocore.exceptions.ClientError as e:
            if (e.response["Error"]["Code"] == "ValidationError" and
                "does not exist" in e.response["Error"]["Message"]):
                return False
            raise

    def deploy(self, stack_name: str, template_body: str, parameters: Dict[str, Any]):
        """
        Deploy a stack via ChangeSet: create if missing, update if exists.
        """
        params = [{"ParameterKey": k, "ParameterValue": str(v)} for k, v in parameters.items()]

        if self.exists(stack_name):
            change_set_type = "UPDATE"
            logger.info(f"Updating stack {stack_name} using ChangeSet.")
        else:
            change_set_type = "CREATE"
            logger.info(f"Creating stack {stack_name} using ChangeSet.")

        change_set_name = f"{stack_name}-changeset"

        try:
            self.cf.create_change_set(
                StackName=stack_name,
                TemplateBody=template_body,
                Parameters=params,
                ChangeSetName=change_set_name,
                ChangeSetType=change_set_type,
                Capabilities=['CAPABILITY_NAMED_IAM']
            )

            self.wait_for_changeset(change_set_name, stack_name)
            self.execute_changeset(change_set_name, stack_name)

        except botocore.exceptions.ClientError as e:
            if "No updates are to be performed" in str(e):
                logger.info(f"No changes detected for stack {stack_name}.")
            else:
                logger.error(f"CloudFormation error for stack {stack_name}: {e}")
                raise

    def wait_for_changeset(self, change_set_name: str, stack_name: str):
        """
        Wait for the ChangeSet to be created.
        """
        waiter = self.cf.get_waiter('change_set_create_complete')
        try:
            logger.info(f"Waiting for ChangeSet {change_set_name} to complete...")
            waiter.wait(
                ChangeSetName=change_set_name,
                StackName=stack_name,
                WaiterConfig={'Delay': 5, 'MaxAttempts': 60}  # ~5 min max
            )
            logger.info(f"ChangeSet {change_set_name} is ready.")
        except botocore.exceptions.WaiterError as e:
            logger.error(f"ChangeSet creation failed for {stack_name}: {e}")
            raise

    def execute_changeset(self, change_set_name: str, stack_name: str):
        """
        Execute a completed ChangeSet.
        """
        logger.info(f"Executing ChangeSet {change_set_name} for stack {stack_name}.")
        self.cf.execute_change_set(ChangeSetName=change_set_name, StackName=stack_name)
        self.wait(stack_name, "stack_update_complete" if self.exists(stack_name) else "stack_create_complete")

    def wait(self, stack_name: str, waiter_type: str):
        """
        Wait for stack creation or update to complete.
        """
        waiter = self.cf.get_waiter(waiter_type)
        try:
            logger.info(f"Waiting for stack {stack_name} ({waiter_type}) to complete...")
            waiter.wait(StackName=stack_name)
            logger.info(f"Stack {stack_name} deployment complete.")
        except botocore.exceptions.WaiterError as e:
            logger.error(f"Stack {stack_name} failed to reach {waiter_type}: {e}")
            raise

    def get_outputs(self, stack_name: str) -> Dict[str, str]:
        """
        Retrieve stack outputs as a dictionary.
        """
        resp = self.cf.describe_stacks(StackName=stack_name)
        outputs = resp["Stacks"][0].get("Outputs", [])
        return {o["OutputKey"]: o["OutputValue"] for o in outputs}
