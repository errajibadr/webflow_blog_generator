# CLI Interface Design for Credential Management

## Overview

This document outlines the design for the command-line interface (CLI) extensions needed to support the new credential management system. The CLI will allow users to add, remove, list, and test FTP credentials for websites in a secure manner, with support for selecting and configuring different backend storage options.

## Command Structure

### Credential Management Commands
```
python main.py --credential <action> [options]
```

Where `<action>` is one of:
- `add`: Add or update credentials
- `remove`: Remove credentials
- `list`: List available credentials
- `test`: Test FTP connection with credentials

### Backend Management Commands
```
python main.py --credential-backend <backend_type> [options]
```

Where `<backend_type>` is one of:
- `file`: Use the file-based backend (default)
- `env`: Use the environment variable backend
- `vault`: Use HashiCorp Vault backend (when implemented)

## Command Details

### Add Credentials

```
python main.py --credential add --website WEBSITE_NAME --type TYPE --value VALUE
```

Parameters:
- `--website`: Name of the website (required)
- `--type`: Type of credential (required, e.g., "FTP_USERNAME", "FTP_PASSWORD")
- `--value`: The credential value (required)
- `--interactive`: Prompt for value instead of providing on command line (optional)

Example:
```
python main.py --credential add --website sample-website --type FTP_USERNAME --value myusername
```

Interactive mode (safer for passwords):
```
python main.py --credential add --website sample-website --type FTP_PASSWORD --interactive
```

### Remove Credentials

```
python main.py --credential remove --website WEBSITE_NAME [--type TYPE]
```

Parameters:
- `--website`: Name of the website (required)
- `--type`: Type of credential (optional, if omitted, removes all credentials for the website)
- `--force`: Skip confirmation prompt (optional)

Example:
```
python main.py --credential remove --website sample-website --type FTP_PASSWORD
```

### List Credentials

```
python main.py --credential list [--website WEBSITE_NAME] [--show-values]
```

Parameters:
- `--website`: Name of the website (optional, if omitted, lists all websites)
- `--show-values`: Show credential values (optional, requires confirmation)

Example:
```
python main.py --credential list
```

Output:
```
Available credentials:
- sample-website:
  - FTP_USERNAME
  - FTP_PASSWORD
- another-website:
  - FTP_USERNAME
  - FTP_PASSWORD
```

### Test Credentials

```
python main.py --credential test --website WEBSITE_NAME
```

Parameters:
- `--website`: Name of the website to test credentials for (required)
- `--host`: Override the FTP host from config (optional)

Example:
```
python main.py --credential test --website sample-website
```

Output:
```
Testing FTP credentials for sample-website (ftp.sample-website.com)...
Connection successful!
```

### Select Backend

```
python main.py --credential-backend TYPE [--backend-config KEY=VALUE]
```

Parameters:
- `TYPE`: Type of backend to use (file, env, vault)
- `--backend-config`: Key-value pairs for backend configuration (optional, can be specified multiple times)

Examples:

File backend (default):
```
python main.py --credential-backend file --backend-config path=/path/to/.env.encrypted
```

Environment backend:
```
python main.py --credential-backend env --backend-config prefix=CRED_
```

Vault backend (future):
```
python main.py --credential-backend vault --backend-config url=https://vault.example.com --backend-config token_env=VAULT_TOKEN
```

### List Available Backends

```
python main.py --credential-backend list
```

Output:
```
Available credential backends:
- file (current): File-based encrypted storage
- env: Environment variable storage
- vault: HashiCorp Vault integration (requires additional setup)
```

## Integration with Main CLI

The credential management commands will be integrated into the existing CLI structure in `main.py`. The following additions will be made:

### Argument Parser Modifications

```python
# Credential management
credential_group = parser.add_argument_group('Credential Management')
credential_group.add_argument('--credential', choices=['add', 'remove', 'list', 'test'],
                             help='Credential management action')
credential_group.add_argument('--website', help='Website name for credential action')
credential_group.add_argument('--type', help='Type of credential (e.g., FTP_USERNAME, FTP_PASSWORD)')
credential_group.add_argument('--value', help='Value for the credential')
credential_group.add_argument('--interactive', action='store_true', 
                             help='Prompt for credential value instead of command line')
credential_group.add_argument('--force', action='store_true', 
                             help='Skip confirmation for dangerous operations')
credential_group.add_argument('--show-values', action='store_true',
                             help='Show credential values when listing (requires confirmation)')
credential_group.add_argument('--host', help='Override FTP host for testing')

# Backend management
backend_group = parser.add_argument_group('Credential Backend Management')
backend_group.add_argument('--credential-backend', 
                          help='Select credential backend (file, env, vault) or "list" to show available backends')
backend_group.add_argument('--backend-config', action='append', 
                          help='Backend configuration in KEY=VALUE format (can specify multiple times)')
```

### Command Handling Logic

```python
# Handle credential backend selection
if args.credential_backend:
    if args.credential_backend == 'list':
        # Import the module only when needed
        from modules.cred_manager import list_available_backends
        backends = list_available_backends()
        print("Available credential backends:")
        for backend in backends:
            print(f"- {backend['name']}{' (current)' if backend['current'] else ''}: {backend['description']}")
        sys.exit(0)
    else:
        # Import the module only when needed
        from modules.cred_manager import set_backend
        
        # Parse backend config if provided
        backend_config = {}
        if args.backend_config:
            for config_item in args.backend_config:
                if '=' in config_item:
                    key, value = config_item.split('=', 1)
                    backend_config[key] = value
                else:
                    parser.error(f"Invalid backend config format: {config_item}. Use KEY=VALUE format.")
        
        # Set the backend
        try:
            set_backend(args.credential_backend, **backend_config)
            print(f"Credential backend set to: {args.credential_backend}")
            sys.exit(0)
        except Exception as e:
            print(f"Error setting credential backend: {e}")
            sys.exit(1)

# Handle credential management commands
if args.credential:
    if not args.credential in ['add', 'remove', 'list', 'test']:
        parser.error("Invalid credential action. Choose from: add, remove, list, test")
        
    # Import the module only when needed
    from modules.cred_manager import manage_credentials
    
    if args.credential == 'add' and not (args.website and args.type):
        parser.error("--website and --type are required for credential add")
        
    if args.credential == 'remove' and not args.website:
        parser.error("--website is required for credential remove")
        
    if args.credential == 'test' and not args.website:
        parser.error("--website is required for credential test")
    
    # Call the credential manager
    result = manage_credentials(
        action=args.credential,
        website=args.website,
        cred_type=args.type,
        value=args.value,
        interactive=args.interactive,
        force=args.force,
        show_values=args.show_values,
        host=args.host
    )
    
    # Return early, no pipeline execution needed
    if result:
        print(result)
    sys.exit(0)
```

## User Experience Considerations

### Interactive Mode

For sensitive credentials like passwords, interactive mode will be available:

```python
def get_credential_interactively(website, cred_type):
    """Prompt user for a credential value."""
    import getpass
    prompt = f"Enter {cred_type} for {website}: "
    if "PASSWORD" in cred_type.upper():
        return getpass.getpass(prompt)
    else:
        return input(prompt)
```

### Confirmation Prompts

For sensitive operations, confirmation prompts will be used:

```python
def confirm_action(action, details):
    """Ask for confirmation before proceeding with sensitive actions."""
    response = input(f"{action} {details}. Are you sure? (y/N): ")
    return response.lower() in ['y', 'yes']
```

### Secure Value Display

When showing credential values:

```python
def display_credential_value(value, sensitive=True):
    """Display credential value, obscuring if sensitive."""
    if sensitive:
        # Show only first and last character, rest as *
        if len(value) <= 2:
            return "**"
        return value[0] + "*" * (len(value) - 2) + value[-1]
    return value
```

### Backend Selection Experience

Transitioning between backends seamlessly:

```python
def transition_credentials(source_backend, target_backend):
    """Transition credentials from one backend to another."""
    credentials = source_backend.list_credentials()
    for website, creds in credentials.items():
        for cred_type, value in creds.items():
            target_backend.store_credential(website, cred_type, value)
    return len(credentials)
```

## Backend-Specific Error Handling

Clear error messages will be provided for common issues:

### File Backend Errors
```
Error: Cannot access credentials file: Permission denied
Error: Encryption key not found. Set CRED_ENCRYPTION_KEY environment variable
Error: Credentials file is corrupt or has been tampered with
```

### Environment Backend Errors
```
Error: Environment variable CRED_SAMPLE_WEBSITE_FTP_PASSWORD not set
Error: Cannot set environment variable (permission denied)
Error: Environment variables may not persist after application exit
```

### Vault Backend Errors
```
Error: Cannot connect to Vault server at https://vault.example.com
Error: Vault authentication failed: invalid token
Error: Requested secret path not found in Vault
```

## General Error Messages
```
Error: Website 'unknown-website' not found in credentials store
Error: Credential type 'FTP_PASSWORD' not found for website 'sample-website'
Error: FTP connection failed: Connection refused
Error: Permission denied when accessing credential store
```

## Help and Documentation

Help text will be comprehensive:

```
Credential Management:
  --credential {add,remove,list,test}
                        Credential management action
  --website WEBSITE     Website name for credential action
  --type TYPE           Type of credential (e.g., FTP_USERNAME, FTP_PASSWORD)
  --value VALUE         Value for the credential
  --interactive         Prompt for credential value instead of command line
  --force               Skip confirmation for dangerous operations
  --show-values         Show credential values when listing (requires confirmation)
  --host HOST           Override FTP host for testing

Credential Backend Management:
  --credential-backend {file,env,vault,list}
                        Select credential backend or list available backends
  --backend-config KEY=VALUE
                        Backend configuration (can specify multiple times)
```

Extended help with examples will be available via:

```
python main.py --credential add --help
python main.py --credential-backend --help
```

## Container-Specific Commands

For container environments, additional helpful commands will be provided:

```
# Export credentials to Docker environment file
python main.py --credential export-env --output .env.docker

# Generate Kubernetes secret manifest
python main.py --credential export-k8s --output ftp-secrets.yaml

# Import credentials from container environment
python main.py --credential import-env
```

## Implementation Notes

1. The credential management interface will be implemented as a separate module function that's called from main.py
2. All user interaction will use standard input/output with proper escaping
3. Confirmation will be required for sensitive operations
4. Error handling will provide clear, actionable messages
5. Help text will be comprehensive and context-sensitive
6. Backend selection will be persistent (stored in config.yaml)
7. Performance optimization through caching will be implemented for all backends 