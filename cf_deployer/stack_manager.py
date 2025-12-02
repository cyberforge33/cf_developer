import botocore
import logging

logger = logging.getLogger(__name__)

class StackManager:
    def __init__(self, cf_client):
        self.cf = cf_client

    def exists(self, stack_name):
        """
        Check if a CloudFormation stack exists.
        """
        try:
            self.cf.describe_stacks(StackName=stack_name)
            return True
        except self.cf.exceptions.ClientError as e:
            if "does not exist" in str(e):
                return False
            raise

    def deploy(self, stack_name, template_body, parameters):
        """
        Deploy a stack: create if it doesn't exist, update if it does.
        Waits for completion before returning.
        """
        params = [{"ParameterKey": k, "ParameterValue": str(v)} for k, v in parameters.items()]

        try:
            if self.exists(stack_name):
                logger.info(f"Updating stack {stack_name}")
                self.cf.update_stack(
                    StackName=stack_name,
                    TemplateBody=template_body,
                    Parameters=params,
                    Capabilities=['CAPABILITY_NAMED_IAM']
                )
                self.wait(stack_name, "stack_update_complete")
            else:
                logger.info(f"Creating stack {stack_name}")
                self.cf.create_stack(
                    StackName=stack_name,
                    TemplateBody=template_body,
                    Parameters=params,
                    Capabilities=['CAPABILITY_NAMED_IAM']
                )
                self.wait(stack_name, "stack_create_complete")
        except botocore.exceptions.ClientError as e:
            if "No updates are to be performed" in str(e):
                logger.info(f"No changes for stack {stack_name}")
            else:
                logger.error(f"CloudFormation error: {e}")
                raise

    def wait(self, stack_name, waiter_type):
        """
        Wait for a stack to reach CREATE_COMPLETE or UPDATE_COMPLETE.
        """
        waiter = self.cf.get_waiter(waiter_type)
        try:
            logger.info(f"Waiting for stack {stack_name} to complete...")
            waiter.wait(StackName=stack_name)
            logger.info(f"Stack {stack_name} is complete.")
        except botocore.exceptions.WaiterError as e:
            logger.error(f"Waiter failed for {stack_name}: {e}")
            raise

    def get_outputs(self, stack_name):
        """
        Retrieve outputs from a stack as a dictionary.
        """
        resp = self.cf.describe_stacks(StackName=stack_name)
        outputs = resp["Stacks"][0].get("Outputs", [])
        return {o["OutputKey"]: o["OutputValue"] for o in outputs}
