"""
Credential CLI Module

This module provides CLI functions for credential management.
"""

import getpass
import logging
from typing import Optional

from modules.credentials.api import (
    delete_credential,
    get_credential,
    list_credentials,
    store_credential,
)

# Configure logging
logger = logging.getLogger(__name__)


def manage_credentials(
    action: str,
    website: Optional[str] = None,
    cred_type: Optional[str] = None,
    value: Optional[str] = None,
    interactive: bool = False,
    force: bool = False,
    show_values: bool = False,
    host: Optional[str] = None,
) -> str:
    """Manage credentials from the CLI.

    Args:
        action: Action to perform (add, remove, list, test, configure)
        website: Website name
        cred_type: Credential type
        value: Credential value
        interactive: Whether to prompt for credential value
        force: Whether to skip confirmation for dangerous actions
        show_values: Whether to show credential values when listing
        host: Override host for testing

    Returns:
        str: Result message
    """
    try:
        if action == "add":
            if not website:
                return "Error: Website name is required"

            if not cred_type:
                return "Error: Credential type is required"

            if interactive and not value:
                import getpass

                prompt = f"Enter {cred_type} for {website}: "
                if cred_type and "PASSWORD" in cred_type.upper():
                    value = getpass.getpass(prompt)
                else:
                    value = input(prompt)

            if not value:
                return "Error: Credential value is required"

            store_credential(website, cred_type, value)
            return f"Credential {website}/{cred_type} stored successfully"

        elif action == "remove":
            if not website:
                return "Error: Website name is required"

            if not force:
                confirmation = input(
                    f"Are you sure you want to delete credential(s) for {website}"
                    + (f"/{cred_type}" if cred_type else "")
                    + "? (y/N): "
                )
                if confirmation.lower() not in ("y", "yes"):
                    return "Operation cancelled"

            if cred_type:
                # Delete specific credential
                if delete_credential(website, cred_type):
                    return f"Credential {website}/{cred_type} deleted successfully"
                else:
                    return f"Credential {website}/{cred_type} not found"
            else:
                # Delete all credentials for website
                credentials = list_credentials(website)
                if not credentials or website not in credentials:
                    return f"No credentials found for {website}"

                count = 0
                for cred_type_name in list(credentials[website].keys()):
                    if delete_credential(website, cred_type_name):
                        count += 1

                return f"Deleted {count} credential(s) for {website}"

        elif action == "list":
            credentials = list_credentials(website)

            if not credentials:
                return "No credentials found"

            lines = ["Available credentials:"]

            for site, creds in credentials.items():
                lines.append(f"- {site}:")
                for cred_type_name, cred_value in creds.items():
                    if show_values:
                        if not force:
                            confirmation = input(
                                "Show credential values? This is insecure and "
                                + "should only be done in a secure environment. (y/N): "
                            )
                            if confirmation.lower() not in ("y", "yes"):
                                return "Operation cancelled"

                        if "PASSWORD" in cred_type_name:
                            display_value = (
                                f"{cred_value[0]}{'*' * (len(cred_value) - 2)}{cred_value[-1]}"
                                if len(cred_value) > 2
                                else "****"
                            )
                        else:
                            display_value = cred_value

                        lines.append(f"  - {cred_type_name}: {display_value}")
                    else:
                        lines.append(f"  - {cred_type_name}")

            return "\n".join(lines)

        elif action == "test":
            if not website:
                return "Error: Website is required for testing"

            try:
                username = get_credential(website, "FTP_USERNAME")
                password = get_credential(website, "FTP_PASSWORD")

                # Get host from config if not provided
                if not host:
                    # This would need to be updated to get from config
                    return "Error: Host is required for testing (use --host)"

                # Test FTP connection
                import ftplib

                with ftplib.FTP() as ftp:
                    ftp.connect(host)
                    ftp.login(username, password)
                    ftp.quit()

                return f"FTP connection to {host} successful using credentials for {website}"

            except Exception as e:
                return f"FTP connection failed: {str(e)}"

        elif action == "configure":
            return configure_website_credentials(website, force)

        else:
            return f"Unknown action: {action}"

    except Exception as e:
        return f"Error: {str(e)}"


def configure_website_credentials(website_name: Optional[str] = None, force: bool = False) -> str:
    """Configure all necessary credentials for a website interactively.

    This function will prompt for FTP username and password for a website
    and store them securely in the credential manager.

    Args:
        website_name: Name of the website to configure
        force: Whether to overwrite existing credentials without confirmation

    Returns:
        str: Result message
    """
    import getpass

    if not website_name:
        return "Error: Website name is required"

    website_name = website_name.lower().strip()

    # Check if credentials already exist
    try:
        existing_creds = list_credentials(website_name)
        if existing_creds and website_name in existing_creds:
            if not force:
                confirmation = input(
                    f"Credentials already exist for {website_name}. Overwrite? (y/N): "
                )
                if confirmation.lower() not in ("y", "yes"):
                    return "Configuration cancelled"
    except Exception:
        # If there's an error checking credentials, proceed anyway
        pass

    print(f"\nConfiguring FTP credentials for {website_name}")
    print("============================================")

    # Prompt for username
    username = input(f"Enter FTP username for {website_name}: ")
    if not username:
        return "Error: Username cannot be empty"

    # Prompt for password
    password = getpass.getpass(f"Enter FTP password for {website_name}: ")
    if not password:
        return "Error: Password cannot be empty"

    # Store the credentials
    try:
        store_credential(website_name, "FTP_USERNAME", username)
        store_credential(website_name, "FTP_PASSWORD", password)

        return f"Successfully configured credentials for {website_name}"
    except Exception as e:
        return f"Error storing credentials: {str(e)}"
