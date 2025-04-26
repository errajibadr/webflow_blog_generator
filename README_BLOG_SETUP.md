# Website Blog Generator Setup Guide

This guide walks you through the complete process of setting up and running the Website Blog Generator pipeline for a new website.

## Prerequisites

Before starting, ensure you have:
- Python 3.11+ installed
- Node.js 18+ installed (for the website enricher)
- Access to the target website's FTP credentials
- SEMrush data for keyword targeting (or another source for target keywords)

## 1. Initialize the Project Structure

First, create the necessary directory structure:

```bash
# Create the basic directory structure
make init

# Or manually:
mkdir -p logs
mkdir -p workspaces
mkdir -p website_configs/topics
```

## 2. Create a Website Configuration File

Create a configuration file for your website in the `website_configs` folder:

```bash
# Copy the sample configuration
cp website_configs/sample.yaml website_configs/your-site.yaml
```

```bash
# Edit the configuration file
nano website_configs/your-site.yaml
```

Edit the configuration file with your website details:

```yaml
website:
  name: your-site
  domain: your-site.com
  workspace: your-site
  
hostinger:
  host: ftp.your-site.com  # Optional, defaults to ftp.{domain}
  # Use credential references for security
  username: ${cred:YOUR-SITE_FTP_USERNAME}
  password: ${cred:YOUR-SITE_FTP_PASSWORD}
  remote_dir: / 

export:
  method: auto  # Options: auto, ftp, selenium, simulate
  
content_generation:
  topics_file: topics/your-site-topics.csv
  batch_size: 2  # Number of blogs to generate at a given time
  max_concurrent: 3  # Number of blogs to generate concurrently
  
blog_config:
  site:
    title: Your Site - Blog Title
    description: A brief description of your blog
    company_name: Your Company
    author:
      name: Author Name
      photo: src/assets/images/author.jpg
    cta_link: https://your-site.com/contact

  social:
    facebook: https://facebook.com/your-site
    twitter: https://twitter.com/your-site
    linkedin: https://linkedin.com/company/your-site
    instagram: https://instagram.com/your-site

  contact:
    email: info@your-site.com
    phone: +1 234 567 8900

  seo:
    defaultTitle: Your Site - Default SEO Title
    defaultDescription: Your default SEO description
    defaultKeywords: keyword1, keyword2, keyword3

  ui:
    primaryColor: "#007bff"
    headerBackground: "#343a40"
    textColor: "#212529"
    linkColor: "#007bff"
    backgroundColor: "#ffffff"

  blog:
    showRecentPosts: true
    recentPostsCount: 3
    showAuthorBio: true
    showSocialShare: true
    blogIndexBackground: src/assets/images/background/your-background.jpg
```

## 3. Prepare Target Keywords

Create a CSV file with your target keywords:

```bash
# Create the topics directory if it doesn't exist
mkdir -p website_configs/topics

# Create the CSV file
touch website_configs/topics/your-site-topics.csv

# Edit the file
nano website_configs/topics/your-site-topics.csv
```

Fill the CSV file with your target keywords. The file should include these columns:

**Required columns:**
- Keyword
- Page
- Topic
- Volume
- Keyword Difficulty
- Intent
- Content references
- Competitors

**Example format:**
```csv
Keyword,Page,Topic,Volume,Keyword Difficulty,Intent,Content references,Competitors
"website seo tips","/blog/website-seo-tips","SEO",1200,45,"informational","competitor1.com, competitor2.com","competitor1.com, competitor2.com, competitor3.com"
"content marketing strategy","/blog/content-marketing-strategy","Content Marketing",2500,67,"commercial","competitor1.com/blog, competitor3.com/strategy","competitor1.com, competitor2.com, competitor4.com"
```

You can export this data from SEMrush or another SEO tool, then format it according to the requirements.

## 4. Set Up Secure Credentials

Set up the FTP credentials securely using the credential management system:

```bash
# List available credential backends
make list-backends

# Configure credentials interactively (recommended)
make configure-credentials SITE=your-site

# Or add credentials individually
make add-credential SITE=your-site TYPE=FTP_USERNAME VALUE=your-username
make add-credential SITE=your-site TYPE=FTP_PASSWORD
# (You'll be prompted to enter the password securely)

# Test your credentials
make test-credential SITE=your-site
```

## 5. Run the Pipeline

You can now run the complete pipeline or individual steps:

### Run the Complete Pipeline

```bash
# Run the full pipeline (export → generate → enrich → import)
make run SITE=your-site

# Or with the Python command
python main.py --website your-site --all
```

### Run Individual Steps

If you prefer to run steps individually:

```bash
# Export website from Hostinger
make export SITE=your-site

# Generate content
make generate SITE=your-site

# Enrich website with content
make enrich SITE=your-site

# Import website back to Hostinger
make import SITE=your-site
```

### Test with Dry Run

Before running the actual pipeline, you can perform a dry run to verify everything is set up correctly:

```bash
# Perform a dry run (no actual changes)
make dry-run SITE=your-site

# Or with verbose logging for more details
make verbose SITE=your-site
```

## 6. Troubleshooting

If you encounter issues during the setup or execution:

### Check Logs

```bash
# View the log file
cat logs/orchestrator.log
```

### Verify Credentials

```bash
# List and verify credentials
make list-credentials

# Test credentials for your site
make test-credential SITE=your-site
```

### Reset and Try Again

If you need to start fresh:

```bash
# Remove credentials
make remove-credential SITE=your-site TYPE=FTP_USERNAME
make remove-credential SITE=your-site TYPE=FTP_PASSWORD

# Clean project files
make clean
```

## 7. Maintenance and Updates

### Update Credentials

If your FTP credentials change:

```bash
# Update credentials
make add-credential SITE=your-site TYPE=FTP_PASSWORD
```

### Update Topics

To refresh your target keywords:

1. Update your CSV file with new keywords
2. Run the generate and enrich steps:

```bash
make generate SITE=your-site
make enrich SITE=your-site
make import SITE=your-site
```

## Need More Help?

For more details on configuration options and advanced usage, refer to the main README.md file:

```bash
cat README.md
```

Or run the help command for a list of available commands:

```bash
make help
``` 