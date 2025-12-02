**CF-Deployer** is a modular, multi-team, multi-environment CloudFormation deployment tool written in Python.  
It supports VPCs, Subnets, Security Groups, S3 Buckets, and EKS clusters with nodegroups.

---

## Features

- Multi-team, multi-environment deployment (Dev/Test/Prod)
- Cross-stack dependencies via SSM
- Deploys VPC, Subnets, Security Groups, S3, EKS Cluster & NodeGroup
- CLI with interactive confirmations, colorized logging, and dry-run
- Retry logic for transient errors (especially EKS NodeGroups)
- Logs to console and file for auditing
- Parallel deployment of independent teams
- Fully modular for onboarding new teams
- Supports dry-run mode and skipping confirmations for automation

---

## Installation

1. Clone the repository and navigate into it:

   git clone <repo-url>
   cd cf-deployer

2. Create and activate a virtual environment:

   python3 -m venv venv
   source venv/bin/activate

3. Install dependencies:

   pip install -r requirements.txt

Dependencies include:
- `boto3`
- `PyYAML`
- `colorama`

---

## Usage

Deploy all stacks in an environment:

   python -m cf_deployer.cli deploy -e dev

Deploy a specific team:

   python -m cf_deployer.cli deploy -e dev -t TeamA

Deploy a specific stack:

   python -m cf_deployer.cli deploy -e dev -t TeamA -s EKSNodeGroup

Dry-run mode (show planned deployment without executing):

   python -m cf_deployer.cli deploy -e dev --dry-run

Skip interactive confirmations:

   python -m cf_deployer.cli deploy -e dev --yes

---

## Environment Configuration
- Configs are YAML files in the `configs/` folder (`dev.yaml`, `test.yaml`, `prod.yaml`)
- Each team defines its stacks, templates, and parameters

---

## Notes
- Ensure AWS CLI profiles exist and have proper permissions
- NodeGroups require a valid IAM NodeRole ARN
- Dry-run mode shows deployment order and resolved parameters without executing
- Can be integrated into CI/CD pipelines using the `--yes` flag to skip confirmations
