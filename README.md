# Website SEO Orchestrator

A Python-based orchestrator that streamlines the process of generating SEO content for multiple websites. This tool connects your existing content generation module with website enrichment to create a complete end-to-end workflow for website SEO management.

## 🚀 Features

- Complete end-to-end workflow from website export to import
- Integrates with existing content generation and website enricher modules
- Supports managing multiple websites with different configurations
- YAML-based configuration for maximum readability and flexibility
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
  username: your-hostinger-username
  password: your-hostinger-password
  # Can use environment variables like ${HOSTINGER_PASSWORD}
  
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

### Running the Full Pipeline

```bash
python main.py --website your-site --all
```

### Running Individual Steps

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

### Advanced Options

```bash
# Test without making changes
python main.py --website your-site --all --dry-run

# Use custom config path
python main.py --website your-site --all --config path/to/config.yaml

# Verbose logging
python main.py --website your-site --all --verbose
```

## 📁 Project Structure

```
website-seo-orchestrator/
├── main.py                  # Main orchestrator script
├── config.yaml              # Global configuration
├── requirements.txt         # Python dependencies
├── modules/                 # Python modules
│   ├── __init__.py
│   ├── exporter.py          # Website export module
│   ├── content_generator.py # Content generation wrapper
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

## ⚠️ Troubleshooting

### Common Issues

- **Hostinger Authentication Errors**: Check your username and password in the website config
- **Content Generation Fails**: Ensure your topics file exists and has the correct format
- **Enricher Fails**: Check that Node.js is installed and paths are correct
- **Import Fails**: Verify Hostinger permissions and connectivity

### Logs

Check detailed logs in the `logs/` directory for more information about errors.

## 🛠️ Development

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