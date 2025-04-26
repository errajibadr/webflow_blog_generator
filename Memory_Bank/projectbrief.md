# Website Blog Generator Orchestrator - Project Brief

## System Overview

The Website Blog Generator Orchestrator is a Python-based system that automates the process of:

1. Exporting websites from Hostinger via FTP
2. Generating blog posts by calling an external API
3. Enriching the website with the generated blog posts using a Node.js tool
4. Uploading the enriched website back to Hostinger

## Architecture

The system follows a modular pipeline design with these core components:

- **Main Orchestrator (main.py)**: Central coordination script
- **Exporter Module**: Downloads website content from Hostinger
- **Content Generator**: Creates blog posts via API
- **Enricher Module**: Integrates blog posts into website
- **Importer Module**: Uploads enriched website back to Hostinger

## Configuration

- Global config in config.yaml
- Per-website configs in website_configs/*.yaml
- Topics for blog generation in CSV files

## Data Flow

```
[Hostinger FTP] → [export/] → [Node.js Enricher] → [output/] → [Hostinger FTP]
                               ↑
[Content API] → [content/] ────┘
```

## Current State

The system is operational and follows a well-organized structure with modular components and clear separation of concerns. 