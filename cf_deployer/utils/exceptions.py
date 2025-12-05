class DeploymentError(Exception):
    """
    Base exception for deployment-related errors.
    """
    pass

class ParameterResolutionError(DeploymentError):
    """
    Raised when SSM parameter or Secrets Manager value cannot be resolved.
    """
    def __init__(self, name: str, message: str = "Failed to resolve parameter"):
        super().__init__(f"{message}: {name}")
        self.name = name

class StackDeploymentError(DeploymentError):
    """
    Raised when a CloudFormation stack fails to deploy.
    """
    def __init__(self, stack_name: str, message: str = "Stack deployment failed"):
        super().__init__(f"{message}: {stack_name}")
        self.stack_name = stack_name
