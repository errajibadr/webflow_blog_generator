# Multi-Website Blog Generation and Deployment Automation

## Project Overview

This project automates the end-to-end process of generating AI-powered blog content and deploying it to multiple websites. The workflow consists of:

1. Exporting website from Hostinger (or Webflow)
2. Generating blog articles and images using a Python AI agent
3. Enriching the exported website with the generated content using the enrich-webflow-export.js script
4. Deploying the enriched website back to Hostinger

## Folder Structure

```
webflow_blog_generator/
├── configs/                       # Configuration files for each website
│   ├── dogtolib-config.json
│   ├── website2-config.json
│   └── ...
├── data/                          # Input data for blog generation
│   ├── éducateur-canin_clusters_2025-03-28.csv
│   └── ...
├── output/                        # Output directory for generated blog content
│   ├── dogtolib/                  # Organized by website
│   │   ├── blog-post-1.json
│   │   ├── images/
│   └── website2/
│       └── ...
├── websites/                      # Exported websites
│   ├── dogtolib/
│   ├── website2/
│   └── ...
├── dist/                          # Enriched websites ready for deployment
│   ├── dogtolib/
│   ├── website2/
│   └── ...
├── src/                           # Source code for the enrich-webflow-export.js
├── scripts/                       # Helper scripts for automation
│   ├── export_website.js          # Script for exporting websites
│   ├── deploy_website.js          # Script for deploying websites
│   ├── run_workflow.js            # Main automation script
│   └── config_template.json       # Template for new website configurations
├── enrich-webflow-export.js       # Main enrichment script
└── automation.js                  # Entry point for the automation
```

## Components

### 1. Configuration Management

Each website requires a configuration file (`configs/{website-name}-config.json`) containing:

- Website metadata (name, URL, etc.)
- API credentials for Hostinger/Webflow
- Blog generation parameters (topics, tone, style)
- Paths to website-specific resources
- Scheduling preferences

Example configuration:

```json
{
  "site": {
    "name": "DogToLib",
    "url": "https://dogtolib.com",
    "company_name": "DogToLib",
    "description": "The dog training library",
    "author": {
      "name": "Default Author",
      "photo": "src/assets/images/author/default-author.jpg"
    },
    "cta_link": "https://dogtolib.com/contact"
  },
  "ui": {
    "primaryColor": "#4a6bdc",
    "headerBackground": "#ffffff",
    "textColor": "#333333",
    "linkColor": "#4a6bdc",
    "backgroundColor": "#f9f9f9"
  },
  "blog": {
    "showAuthorBio": true,
    "showSocialShare": true,
    "showRecentPosts": true,
    "recentPostsCount": 3,
    "blogIndexBackground": "src/assets/images/background/dog-background.jpg"
  },
  "social": {
    "facebook": "https://facebook.com/dogtolib",
    "twitter": "https://twitter.com/dogtolib",
    "linkedin": "https://linkedin.com/company/dogtolib"
  },
  "hostinger": {
    "apiKey": "YOUR_HOSTINGER_API_KEY",
    "siteId": "your-site-id"
  },
  "blogGeneration": {
    "topics": ["dog training", "puppy care", "dog behavior"],
    "frequency": "weekly",
    "articlesPerBatch": 3,
    "language": "fr",
    "inputDataFile": "data/éducateur-canin_clusters_2025-03-28.csv",
    "aiParams": {
      "maxConcurrent": 3,
      "batchSize": 10
    }
  }
}
```

### 2. Python AI Agent Integration

The Python AI agent is responsible for generating blog content and images:

- Input: CSV files with topic clusters
- Output: JSON blog articles and related images
- Command: `uv run main.py --input {input_file} --output {output_dir} --batch {batch_size} --max-concurrent {concurrent_jobs}`

The output follows a standard format compatible with the enrichment script:

```
output/{website}/
├── blog-post-1.json
├── blog-post-2.json
└── images/
    ├── blog-post-1-image.jpg
    └── blog-post-2-image.jpg
```

### 3. Website Enrichment

The enrichment process uses the existing `enrich-webflow-export.js` script:

- Input: Exported website and generated blog content
- Output: Enriched website ready for deployment
- Command: `node enrich-webflow-export.js --export ./websites/{website}/ --csv ./output/{website}/ --config ./configs/{website}-config.json --output ./dist/{website}`

### 4. Deployment to Hostinger

The deployment process uploads the enriched website back to Hostinger:

- Input: Enriched website
- Output: Live website with new blog content
- Script: `scripts/deploy_website.js`

## Automation Workflow

The main automation script (`automation.js`) orchestrates the entire process:

```javascript
// Example usage:
// node automation.js --website dogtolib --generate-articles 3 --deploy true
```

The workflow consists of:

1. Parse command line arguments to determine which website to process
2. Load the website configuration
3. Export the website from Hostinger/Webflow (if needed)
4. Generate blog articles using the Python AI agent
5. Enrich the website with the generated content
6. Deploy the enriched website back to Hostinger
7. Log the results and send notifications (if configured)

### Scheduling

For regular blog updates, you can schedule the automation script using:

- Cron jobs
- PM2
- GitHub Actions

Example cron job:

```
# Generate 2 new articles for dogtolib every Monday at 2 AM
0 2 * * 1 cd /path/to/webflow_blog_generator && node automation.js --website dogtolib --generate-articles 2 --deploy true
```

## Getting Started

1. Clone this repository
2. Install dependencies: `npm install`
3. Create website configuration files in the `configs/` directory
4. Run the automation script: `node automation.js --website {website_name}`

## Future Enhancements

- Web dashboard for monitoring and triggering the workflow
- Quality validation of generated content
- A/B testing of different blog templates
- Analytics integration to track blog performance
- Multi-language support
- Batch processing of multiple websites 