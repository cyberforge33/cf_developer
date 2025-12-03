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
        if ans in ["n", "no"]:
            return False

def main():
    parser = argparse.ArgumentParser(description="cf-deployer")
    parser.add_argument("command", choices=["deploy"])
    parser.add_argument("-e", "--env", required=True)
    parser.add_argument("-t", "--team")
    parser.add_argument("-s", "--stack")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--yes", action="store_true")

    args = parser.parse_args()

    if args.command == "deploy":
        if not args.yes:
            if not confirm(f"Deploy env '{args.env}'" +
                           (f", team '{args.team}'" if args.team else "") +
                           "?"):
                print(Fore.RED + "Deployment aborted.")
                sys.exit(0)

        print(Fore.GREEN + f"Starting deployment for env {args.env}...")
        deployer.run_deployment(args.env, args.team, args.stack, args.dry_run)
        print(Fore.GREEN + "Deployment finished successfully.")

if __name__ == "__main__":
    main()
