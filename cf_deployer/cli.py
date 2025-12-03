import argparse
from cf_deployer import deployer
from colorama import Fore, Style, init
import sys

init(autoreset=True)

def confirm(prompt: str) -> bool:
    while True:
        ans = input(f"{Fore.YELLOW}{prompt} [y/n]: {Style.RESET_ALL}").lower()
        if ans in ["y", "yes"]:
            return True
        elif ans in ["n", "no"]:
            return False

def main():
    parser = argparse.ArgumentParser(
        description="cf-deployer: Deploy CloudFormation stacks"
    )
    parser.add_argument("command", choices=["deploy"], help="Command to execute")
    parser.add_argument("-e", "--env", required=True, help="Environment (dev/test/prod)")
    parser.add_argument("-t", "--team", help="Specific team to deploy (optional)")
    parser.add_argument("-s", "--stack", help="Specific stack to deploy (optional)")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be deployed")
    parser.add_argument("--yes", action="store_true", help="Skip confirmations")

    args = parser.parse_args()

    if args.command == "deploy":
        if not args.yes:
            confirmed = confirm(
                f"Proceed to deploy environment '{args.env}'"
                + (f", team '{args.team}'" if args.team else "") + "?"
            )
            if not confirmed:
                print(f"{Fore.RED}Deployment aborted by user.{Style.RESET_ALL}")
                sys.exit(0)

        print(f"{Fore.GREEN}Starting deployment for environment '{args.env}'...{Style.RESET_ALL}")
        deployer.run_deployment(
            env=args.env,
            team=args.team,
            stack=args.stack,
            dry_run=args.dry_run
        )
        print(f"{Fore.GREEN}Deployment finished successfully.{Style.RESET_ALL}")

if __name__ == "__main__":
    main()
