# Webflow Blog Generator

A powerful Node.js tool that enriches Webflow exports with advanced blog functionality. This tool allows you to transform your static Webflow exports into a dynamic blog platform with features like post listings, pagination, and customizable templates.

## 🚀 Features

- Enriches Webflow exports with blog functionality
- Generates blog listing pages with customizable layouts
- Creates individual blog post pages
- Supports custom templates using Handlebars
- Configurable through JSON files
- Asset management and optimization
- Responsive design support
- SEO-friendly output
- Social media integration
- Custom theming capabilities

## 📋 Prerequisites

- Node.js (v12 or higher)
- npm or yarn package manager
- A Webflow export of your site
- Blog posts data in CSV format

## 🛠️ Installation

1. Clone the repository:
```bash
git clone [repository-url]
cd webflow-blog-generator
```

2. Install dependencies:
```bash
npm install
```

## ⚙️ Configuration

1. Create a config file based on the examples provided. You can use either JSON or YAML format:
```bash
# JSON format (blog config only)
cp blog-config.example.json blog-config.json

# Or YAML format (can be full site config with blog_config section)
cp example-config.yaml your-config.yaml
```

2. Customize the configuration file with your settings:

### JSON Format (Blog Config Only)
```json
{
    "site": {
        "title": "Your Blog Title",
        "description": "Your blog description",
        "logo": "/images/logo.png",
        "favicon": "/images/favicon.ico"
    },
    "social": {
        "facebook": "https://facebook.com/yourblog",
        "twitter": "https://twitter.com/yourblog",
        "linkedin": "https://linkedin.com/company/yourblog"
    },
    "contact": {
        "email": "contact@yourblog.com",
        "phone": "your-phone-number"
    },
    "seo": {
        "defaultTitle": "Your Blog - Articles and News",
        "defaultDescription": "Your default SEO description",
        "defaultImage": "/images/default-share.jpg",
        "googleAnalyticsId": "your-ga-id"
    }
}
```

### YAML Format
YAML configs can be either:

1. A standalone blog config (similar to JSON structure):
```yaml
site:
  title: Your Blog Title
  description: Your blog description
  logo: /images/logo.png
  favicon: /images/favicon.ico
# ... more blog config ...
```

2. Or a full site configuration with a nested blog_config section (like @dogtolib.yaml):
```yaml
website:
  name: your-site
  domain: example.com
  # ... other site settings ...
  
# ... other sections ...

# This is the section used by the enricher
blog_config:
  site:
    title: Your Blog Title
    # ... more blog config ...
```

The tool will automatically detect if it's a full site YAML (with blog_config) or a standalone blog config.

## 📊 CSV Format

Your blog posts should be in a CSV file with the following columns:
- Titre (Title)
- Résumé de l'article (Article Summary)
- auteur (Author)
- Date de publication (Publication Date)
- Durée de lecture (Reading Time)
- photo article (Article Image)
- Slug (URL-friendly identifier)
- Content (Article Content)

## 🚦 Usage

Run the generator with the following command:

```bash
node enrich-webflow-export.js --export <webflow-export-dir> --csv <posts-csv-directory> --config <config-file> --output <output-dir> [--port <port-number>]
```

Options:
- `--export, -e`: Path to Webflow export directory (required)
- `--csv, -c`: Path to blog posts CSV file (required)
- `--config, -f`: Path to blog config file in JSON or YAML format (required)
- `--output, -o`: Output directory (default: 'dist')
- `--port, -p`: Port for local testing (default: 3000)

Example:
```bash
# Using JSON config
node enrich-webflow-export.js -e ./webflow-export -c ./posts.csv -f ./blog-config.json -o ./dist

# Using YAML config
node enrich-webflow-export.js -e ./webflow-export -c ./posts.csv -f ./config.yaml -o ./dist
```

## 🔧 Code Architecture

The codebase is now fully modular for maintainability and extensibility:

- **enrich-webflow-export.js**: Minimal CLI entrypoint. Parses arguments and orchestrates the build using modules.
- **config.js**: Handles loading and validating configuration from JSON or YAML files.
- **utils.js**: General utility functions (date parsing, slugify, text truncation, content processing, etc).
- **posts.js**: Handles reading, validating, and normalizing blog post data from CSV/JSON.
- **blog.js**: Generates blog listing and individual post pages from normalized data.
- **images.js**: Handles default image logic, image validation, and copying dog pictures.
- **assets.js**: Asset copying and minification (CSS, JS, images, etc).
- **templates.js**: Handlebars helpers and template reading/compilation.
- **sitemap.js**: Sitemap and robots.txt generation.
- **htaccess.js**: .htaccess file generation for Apache hosting.

### How to Extend
- Add new helpers to `utils.js` or `templates.js`.
- Add new blog generation logic to `blog.js`.
- Add new asset types or minification logic to `assets.js`.
- All business logic should be in modules, not in the CLI entrypoint.

## 📝 Available Helpers

Handlebars helpers available in templates:
- `formatDate`: Formats dates in French locale
- `truncate`: Truncates text with ellipsis
- `currentYear`: Returns current year
- `eq`: Compares values
- `hasValue`: Checks if value exists and is not empty
- `getConfig`: Gets configuration values
- `socialIcon`: Renders social media icons

## 🔧 Development & Testing

To serve the generated site locally:
```bash
npm run serve
```

### Testing
- Run the CLI with various combinations of CSV/JSON, config, and export directories.
- Check the output in the `dist/` directory for correct HTML, assets, and sitemaps.
- Review the console output for warnings or errors.
- To add tests, create test scripts or use a framework like Jest for unit testing helpers in `utils.js`, `posts.js`, etc.

### Developer Notes
- All new features should be implemented in modules, not in the CLI entrypoint.
- Keep code DRY and modular for easy updates.
- See `tasks.md` for the current refactor and implementation plan.

## 🎨 Customization

### Templates
Custom templates are located in the `src/templates` directory:
- `blog.html`: Blog listing page template
- `blog-post.html`: Individual blog post template

### Styles
- Custom styles can be added in `src/assets/css/blog-style.css`
- Theme colors and UI settings can be configured in the config file

## 📄 License

ISC License

## 👥 Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a new Pull Request

## 🤝 Support

For support, please open an issue in the repository or contact the maintainers.

## ✨ Acknowledgments

- Built with Node.js
- Uses Handlebars for templating
- Powered by Webflow exports 