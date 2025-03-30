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

1. Create a `blog-config.json` file based on the example provided:
```bash
cp blog-config.example.json blog-config.json
```

2. Customize the configuration file with your settings:
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
node enrich-webflow-export.js --export <webflow-export-dir> --csv <posts-csv-file> --config <config-json-file> --output <output-dir> [--port <port-number>]
```

Options:
- `--export, -e`: Path to Webflow export directory (required)
- `--csv, -c`: Path to blog posts CSV file (required)
- `--config, -f`: Path to blog config JSON file (required)
- `--output, -o`: Output directory (default: 'dist')
- `--port, -p`: Port for local testing (default: 3000)

Example:
```bash
node enrich-webflow-export.js -e ./webflow-export -c ./posts.csv -f ./blog-config.json -o ./dist
```

## 🎨 Customization

### Templates
Custom templates are located in the `src/templates` directory:
- `blog.html`: Blog listing page template
- `blog-post.html`: Individual blog post template

### Styles
- Custom styles can be added in `src/assets/css/blog-style.css`
- Theme colors and UI settings can be configured in the config file

## 📝 Available Helpers

Handlebars helpers available in templates:
- `formatDate`: Formats dates in French locale
- `truncate`: Truncates text with ellipsis
- `currentYear`: Returns current year
- `eq`: Compares values
- `hasValue`: Checks if value exists and is not empty
- `getConfig`: Gets configuration values
- `socialIcon`: Renders social media icons

## 🔧 Development

To serve the generated site locally:
```bash
npm run serve
```

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