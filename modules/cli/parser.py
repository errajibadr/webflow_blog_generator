"""
Command line argument parsing for Website SEO Orchestrator.
"""

import argparse
import sys
from typing import List

from modules.credentials import list_available_backends, manage_credentials, set_backend


def parse_args() -> argparse.Namespace:
    """
    Parse command line arguments.

    Returns:
        Parsed command line arguments
    """
    parser = argparse.ArgumentParser(description="Website SEO Orchestrator")
    parser.add_argument("--website", help="Website name (must match a config file)")
    parser.add_argument("--config", default="config.yaml", help="Path to main config file")

    # Steps to run
    parser.add_argument("--export", action="store_true", help="Export website from Hostinger")
    parser.add_argument("--generate", action="store_true", help="Generate SEO content")
    parser.add_argument("--enrich", action="store_true", help="Enrich website with content")
    parser.add_argument(
        "--upload", dest="upload_website", action="store_true", help="Upload website to Hostinger"
    )
    parser.add_argument(
        "--force-hta", action="store_true", help="Force overwrite of .htaccess file"
    )
    parser.add_argument("--all", action="store_true", help="Run all steps")

    # Other options
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    parser.add_argument("--dry-run", action="store_true", help="Dry run (no actual changes)")
    parser.add_argument(
        "--purge-remote",
        action="store_true",
        help="Purge all files in the remote directory before upload (DANGEROUS)",
    )

    credential_group = parser.add_argument_group("Credential Management")
    credential_group.add_argument(
        "--credential",
        choices=["add", "remove", "list", "test", "configure"],
        help="Credential management action",
    )

    credential_group.add_argument(
        "--website-cred", help="Website name for credential action", dest="cred_website"
    )

    credential_group.add_argument(
        "--type", help="Type of credential (e.g., FTP_USERNAME, FTP_PASSWORD)"
    )

    credential_group.add_argument("--value", help="Value for the credential")

    credential_group.add_argument(
        "--interactive",
        action="store_true",
        help="Prompt for credential value instead of command line",
    )

    credential_group.add_argument(
        "--force", action="store_true", help="Skip confirmation for dangerous operations"
    )

    credential_group.add_argument(
        "--show-values",
        action="store_true",
        help="Show credential values when listing (requires confirmation)",
    )

    # Backend management
    backend_group = parser.add_argument_group("Credential Backend Management")
    backend_group.add_argument(
        "--credential-backend",
        help='Select credential backend (file, env, vault) or "list" to show available backends',
    )

    backend_group.add_argument(
        "--backend-config",
        action="append",
        help="Backend configuration in KEY=VALUE format (can specify multiple times)",
    )

    return parser.parse_args()


def handle_credential_backend(args: argparse.Namespace) -> bool:
    """
    Handle credential backend selection if requested.

    Args:
        args: Parsed command line arguments

    Returns:
        True if backend selection was handled and the program should exit,
        False otherwise
    """
    if not args.credential_backend:
        return False

    if args.credential_backend == "list":
        backends = list_available_backends()
        print("Available credential backends:")
        for backend in backends:
            print(
                f"- {backend['name']}{' (current)' if backend['current'] else ''}: {backend['description']}"
            )
        return True
    else:
        # Parse backend config if provided
        backend_config = {}
        if args.backend_config:
            for config_item in args.backend_config:
                if "=" in config_item:
                    key, value = config_item.split("=", 1)
                    backend_config[key] = value
                else:
                    print(
                        f"Error: Invalid backend config format: {config_item}. Use KEY=VALUE format."
                    )
                    sys.exit(1)

        # Set the backend
        try:
            set_backend(args.credential_backend, **backend_config)
            print(f"Credential backend set to: {args.credential_backend}")
            return True
        except Exception as e:
            print(f"Error setting credential backend: {e}")
            sys.exit(1)


def handle_credential_management(args: argparse.Namespace) -> bool:
    """
    Handle credential management commands if requested.

    Args:
        args: Parsed command line arguments

    Returns:
        True if credential management was handled and the program should exit,
        False otherwise
    """
    if not args.credential:
        return False

    result = manage_credentials(
        action=args.credential,
        website=args.cred_website,
        cred_type=args.type,
        value=args.value,
        interactive=args.interactive,
        force=args.force,
        show_values=args.show_values,
        host=args.website,  # Use website as host if needed
    )

    print(result)
    return True


def get_steps_from_args(args: argparse.Namespace) -> List[str]:
    """
    Determine which pipeline steps to run based on command line arguments.

    Args:
        args: Parsed command line arguments

    Returns:
        List of step names to execute
    """
    steps = []
    if args.export:
        steps.append("export")
    if args.generate:
        steps.append("generate")
    if args.enrich:
        steps.append("enrich")
    if args.upload_website:
        steps.append("upload")
    if args.all or not steps:  # Default to all if no steps specified
        steps = ["export", "generate", "enrich", "upload"]

    return steps
