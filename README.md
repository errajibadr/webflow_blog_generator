# Website SEO Orchestrator

A Python-based orchestrator that streamlines the process of generating SEO content for multiple websites. This tool connects your existing content generation module with website enrichment to create a complete end-to-end workflow for website SEO management.

## 🚀 Features

- Complete end-to-end workflow from website export to import
- Integrates with existing content generation and website enricher modules
- Supports managing multiple websites with different configurations
- YAML-based configuration for maximum readability and flexibility
- Secure credential management with multiple backend options
- Modular architecture for improved maintainability
- Detailed logging and error handling
- Dry-run capability for testing without making changes

## 📋 Prerequisites

- Python 3.11+
- Node.js 18+ (for the website enricher module)
- Hostinger account with website access
- Access to both content generation and website enricher modules

## 📦 Installation

1. Clone this repository:
```bash
git clone https://github.com/yourusername/website-seo-orchestrator.git
cd website-seo-orchestrator
```

2. Install Python dependencies:
```bash
pip install -r requirements.txt
```

3. Set up configuration:
```bash
# Copy example configs
cp examples/config.yaml config.yaml
cp examples/website_configs/example.yaml website_configs/your-site.yaml

# Edit with your settings
nano config.yaml
nano website_configs/your-site.yaml
```

4. Set up credentials:
```bash
# Configure credentials securely (interactive mode)
python main.py --credential configure --website-cred your-site --interactive
```

## ⚙️ Configuration

### Main Configuration (config.yaml)

```yaml
# Global settings
logging:
  level: INFO
  file: logs/orchestrator.log

paths:
  workspaces: workspaces  # Root directory for all website workspaces
  logs: logs

# Default settings for websites
defaults:
  content_generation:
    batch_size: 2
    max_concurrent: 3
  
  website_enricher:
    port: 3000
```

### Website Configuration (website_configs/your-site.yaml)

```yaml
website:
  name: My Website
  domain: mywebsite.com
  workspace: mywebsite  # Name of the workspace directory
  
hostinger:
  # Secure credential references
  username: ${cred:MYWEBSITE_FTP_USERNAME}
  password: ${cred:MYWEBSITE_FTP_PASSWORD}
  # Can also use environment variables like ${env:HOSTINGER_PASSWORD}
  
content_generation:
  topics_file: website/topics_data/mywebsite_topics.csv
  batch_size: 2
  max_concurrent: 3
  
website_enricher:
  config_file: config/websites/mywebsite_blog_config.yaml
```

### Blog Configuration (config/websites/mywebsite_blog_config.yaml)

```yaml
site:
  title: My Website Blog
  description: Blog description
  company_name: My Company
  author:
    name: Default Author
    photo: src/assets/images/author.jpg
  cta_link: https://mywebsite.com/contact

social:
  facebook: https://facebook.com/mywebsite
  twitter: https://twitter.com/mywebsite
  linkedin: https://linkedin.com/company/mywebsite

blog:
  showRecentPosts: true
  recentPostsCount: 3
  showAuthorBio: true
  showSocialShare: true
  blogIndexBackground: src/assets/images/background/waterfall.jpg

ui:
  primaryColor: "#007bff"
  headerBackground: "#343a40"
  textColor: "#212529"
  linkColor: "#007bff"
  backgroundColor: "#ffffff"
```

## 💻 Usage

### Using the Makefile

The project includes a Makefile for common operations:

```bash
# Run the full pipeline for a website
make run SITE=your-site

# Run individual steps
make export SITE=your-site
make generate SITE=your-site
make enrich SITE=your-site
make import SITE=your-site

# Dry run (no changes)
make dry-run SITE=your-site

# Manage credentials
make configure-credentials SITE=your-site
make list-credentials
```

### Running Directly

#### Running the Full Pipeline

```bash
python main.py --website your-site --all
```

#### Running Individual Steps

Export website from Hostinger:
```bash
python main.py --website your-site --export
```

Generate content:
```bash
python main.py --website your-site --generate
```

Enrich website with content:
```bash
python main.py --website your-site --enrich
```

Import website to Hostinger:
```bash
python main.py --website your-site --import
```

#### Credential Management

List available credential backends:
```bash
python main.py --credential-backend list
```

Select a credential backend:
```bash
python main.py --credential-backend file  # File-based storage (default)
python main.py --credential-backend env   # Environment variables
```

Configure credentials interactively:
```bash
python main.py --credential configure --website-cred your-site --interactive
```

Add a specific credential:
```bash
python main.py --credential add --website-cred your-site --type FTP_USERNAME --value yourusername
python main.py --credential add --website-cred your-site --type FTP_PASSWORD --interactive
```

List credentials:
```bash
python main.py --credential list
```

### Advanced Options

```bash
# Test without making changes
python main.py --website your-site --all --dry-run

# Use custom config path
python main.py --website your-site --all --config path/to/config.yaml

# Verbose logging
python main.py --website your-site --all --verbose

# Purge remote files before import (use with caution!)
python main.py --website your-site --import --purge-remote
```

## 📁 Project Structure

```
website-seo-orchestrator/
├── main.py                  # Main orchestrator script
├── config.yaml              # Global configuration
├── Makefile                 # Common operations
├── requirements.txt         # Python dependencies
├── modules/                 # Python modules
│   ├── __init__.py
│   ├── cli/                 # Command-line interface
│   │   ├── __init__.py
│   │   └── parser.py        # Argument parsing
│   ├── config/              # Configuration handling
│   │   ├── __init__.py
│   │   ├── loader.py        # Config loading and processing
│   │   └── logging.py       # Logging setup
│   ├── credentials/         # Credential management
│   │   ├── __init__.py
│   │   ├── api.py           # Public API
│   │   ├── backends/        # Storage backends
│   │   ├── cli.py           # CLI commands
│   │   ├── manager.py       # Backend management
│   │   └── types.py         # Type definitions
│   ├── pipeline/            # Pipeline orchestration
│   │   ├── __init__.py
│   │   └── runner.py        # Step execution
│   ├── exporter.py          # Website export module
│   ├── content_generator/   # Content generation wrapper
│   ├── enricher.py          # Website enricher wrapper
│   └── importer.py          # Website import module
├── website_configs/         # Website-specific configs
│   ├── site1.yaml
│   └── site2.yaml
├── workspaces/              # Website workspaces
│   ├── site1/               # Workspace for site1
│   │   ├── export/          # Exported website files
│   │   ├── content/         # Generated content
│   │   └── output/          # Enriched website
│   └── site2/               # Workspace for site2
│       ├── export/
│       ├── content/
│       └── output/
├── logs/                    # Log files
└── examples/                # Example configurations
```

## 🔄 Workflow Details

The orchestrator follows these main steps:

1. **Export**: Extract website from Hostinger
   - Downloads website files using Hostinger's export functionality
   - Stores files in `workspaces/{site}/export`

2. **Generate**: Create SEO content
   - Calls your existing Python content generator module
   - Uses topics defined in configuration
   - Outputs JSON files and images to `workspaces/{site}/content`

3. **Enrich**: Enhance website with content
   - Uses the website enricher module to integrate generated content
   - Takes website export and content as inputs
   - Outputs enhanced website to `workspaces/{site}/output`

4. **Import**: Deploy to Hostinger
   - Uploads the enriched website back to Hostinger
   - Handles any necessary database configurations

## 🔐 Credential Management

The orchestrator includes a secure credential management system with multiple storage backends:

### Storage Backends

- **File Backend**: Encrypts credentials and stores them in local files (default)
- **Environment Backend**: Uses environment variables for containerized deployments
- **Vault Backend**: (Planned) Integration with HashiCorp Vault for enterprise deployments

### Credential References

You can use credential references in your configuration files with the following format:
```
${cred:WEBSITE_CREDENTIAL_TYPE}
```

For example:
```yaml
hostinger:
  username: ${cred:MYWEBSITE_FTP_USERNAME}
  password: ${cred:MYWEBSITE_FTP_PASSWORD}
```

This approach enhances security by:
1. Keeping sensitive data out of configuration files
2. Enabling secure storage with encryption
3. Supporting different storage methods for different environments

## ⚠️ Troubleshooting

### Common Issues

- **Hostinger Authentication Errors**: Check your credentials with `python main.py --credential test --website-cred your-site`
- **Content Generation Fails**: Ensure your topics file exists and has the correct format
- **Enricher Fails**: Check that Node.js is installed and paths are correct
- **Import Fails**: Verify Hostinger permissions and connectivity
- **Credential Errors**: Make sure you've properly set up credentials with the `--credential configure` command

### Logs

Check detailed logs in the `logs/` directory for more information about errors.

## 🛠️ Development

### Modular Architecture

The codebase follows a modular structure:
- **CLI Module**: Handles command-line argument parsing and user interaction
- **Config Module**: Manages configuration loading and processing
- **Credentials Module**: Provides secure credential storage and retrieval
- **Pipeline Module**: Orchestrates the execution of pipeline steps

This architecture makes it easier to:
- Add new features without modifying existing code
- Replace components with alternative implementations
- Test individual components in isolation
- Understand and maintain the codebase

### Adding Support for New Hosting Providers

The modular architecture makes it easy to add support for additional hosting providers:

1. Create a new module in the `modules/` directory
2. Implement export and import functions for the new provider
3. Update configuration schema to include new provider options

### Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

MIT License

## 🙏 Acknowledgments

- Content generation module by [Original Author]
- Website enricher module by [Original Author] 