#!/usr/bin/env node

const fs = require('fs-extra');
const path = require('path');
const { parse } = require('csv-parse/sync');
const Handlebars = require('handlebars');
const yargs = require('yargs/yargs');
const { hideBin } = require('yargs/helpers');

// Parse command line arguments
const argv = yargs(hideBin(process.argv))
  .option('export', {
    alias: 'e',
    description: 'Path to Webflow export directory',
    type: 'string',
    demandOption: true
  })
  .option('csv', {
    alias: 'c',
    description: 'Path to blog posts CSV file',
    type: 'string',
    demandOption: true
  })
  .option('config', {
    alias: 'f',
    description: 'Path to blog config JSON file',
    type: 'string',
    demandOption: true
  })
  .option('output', {
    alias: 'o',
    description: 'Output directory',
    type: 'string',
    default: 'dist'
  })
  .option('port', {
    alias: 'p',
    description: 'Port for local testing',
    type: 'number',
    default: 3000
  })
  .help()
  .argv;

// Helper function to format dates
function formatDate(dateString) {
  if (!dateString) return '';
  const date = new Date(dateString);
  return date.toLocaleDateString('fr-FR', {
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  });
}

// Helper function to truncate text
function truncateText(text, maxLength = 120) {
  if (!text) return '';
  if (text.length <= maxLength) return text;
  return text.substring(0, maxLength).trim() + '...';
}

// Register Handlebars helpers
Handlebars.registerHelper('formatDate', formatDate);
Handlebars.registerHelper('truncate', truncateText);
Handlebars.registerHelper('currentYear', function() {
  return new Date().getFullYear();
});

// Helper for comparing values
Handlebars.registerHelper('eq', function(a, b) {
  return a === b;
});

// Helper to check if value exists and is not empty
Handlebars.registerHelper('hasValue', function(value) {
  return value && value.trim && value.trim() !== '';
});

// Helper to get config value
Handlebars.registerHelper('getConfig', function(path) {
  const parts = path.split('.');
  let value = this.config;
  for (const part of parts) {
    if (value && value[part]) {
      value = value[part];
    } else {
      return '';
    }
  }
  return value;
});

// Helper for social media icons
Handlebars.registerHelper('socialIcon', function(platform) {
  const iconPaths = {
    facebook: path.join(__dirname, 'src', 'assets', 'images', 'social', 'facebook.svg'),
    twitter: path.join(__dirname, 'src', 'assets', 'images', 'social', 'twitter.svg'),
    linkedin: path.join(__dirname, 'src', 'assets', 'images', 'social', 'linkedin.svg'),
    instagram: path.join(__dirname, 'src', 'assets', 'images', 'social', 'instagram.svg'),
    github: path.join(__dirname, 'src', 'assets', 'images', 'social', 'github.svg')
  };

  if (!iconPaths[platform]) {
    return '';
  }

  try {
    const svgContent = fs.readFileSync(iconPaths[platform], 'utf-8');
    return new Handlebars.SafeString(svgContent);
  } catch (error) {
    console.error(`Error loading social icon for ${platform}:`, error);
    return '';
  }
});

// Helper function to read and parse CSV file
async function readCsvFile(filePath) {
  const content = await fs.readFile(filePath, 'utf-8');
  return parse(content, {
    columns: true,
    skip_empty_lines: true,
    delimiter: ';'
  });
}

// Helper function to read and parse JSON config
async function readConfig(filePath) {
  const content = await fs.readFile(filePath, 'utf-8');
  return JSON.parse(content);
}

// Helper function to read template file
async function readTemplate(templatePath) {
  const content = await fs.readFile(templatePath, 'utf-8');
  return Handlebars.compile(content);
}

// Copy assets to output directory
async function copyAssets(outputDir, config) {
  // Create assets directory structure
  await fs.ensureDir(path.join(outputDir, 'css'));
  await fs.ensureDir(path.join(outputDir, 'assets', 'js'));
  await fs.ensureDir(path.join(outputDir, 'assets', 'images', 'social'));
  
  // Copy all CSS files from src/assets/css
  const cssSourceDir = path.join(__dirname, 'src', 'assets', 'css');
  const cssDestDir = path.join(outputDir, 'css');
  
  try {
    // Copy all CSS files
    const cssFiles = await fs.readdir(cssSourceDir);
    for (const file of cssFiles) {
      if (file.endsWith('.css')) {
        await fs.copy(
          path.join(cssSourceDir, file),
          path.join(cssDestDir, file)
        );
        console.log(`Copied CSS file: ${file}`);
      }
    }
  } catch (error) {
    console.error('Error copying CSS files:', error);
  }

  // Copy social icons
  const socialIconsSource = path.join(__dirname, 'src', 'assets', 'images', 'social');
  const socialIconsDest = path.join(outputDir, 'assets', 'images', 'social');
  await fs.copy(socialIconsSource, socialIconsDest);

  // Generate dynamic CSS with theme colors
  const dynamicCss = `
    :root {
      --primary-color: ${config.ui.primaryColor};
      --header-background: ${config.ui.headerBackground};
      --text-color: ${config.ui.textColor};
      --link-color: ${config.ui.linkColor};
      --config-background-color: ${config.ui.backgroundColor};
    }
  `;
  await fs.writeFile(path.join(outputDir, 'css', 'theme.css'), dynamicCss);

  // Copy JS files
  const jsSource = path.join(__dirname, 'src', 'assets', 'js');
  const jsDest = path.join(outputDir, 'assets', 'js');
  await fs.copy(jsSource, jsDest);
}

// Generate blog listing page
async function generateBlogListing(posts, config, outputDir) {
  const template = await readTemplate(path.join(__dirname, 'src', 'templates', 'blog.html'));
  
  // Sort posts by date (most recent first)
  posts.sort((a, b) => new Date(b['Date de publication']) - new Date(a['Date de publication']));
  
  const templateData = {
    config,
    posts: posts.map(post => ({
      titre: post['Titre'],
      resume: post['Résumé de l\'article'],
      auteur: post['auteur'],
      date_publication: formatDate(post['Date de publication']),
      duree_lecture: post['Durée de lecture'],
      photo_article: post['photo article'],
      slug: post['Slug']
    })),
    site: config.site,
    social: config.social
  };

  const html = template(templateData);
  const outputFile = path.join(outputDir, 'blog.html');
  await fs.outputFile(outputFile, html);
  console.log('Generated: blog.html with sorted posts');
}

// Generate individual blog post pages
async function generateBlogPosts(posts, config, outputDir) {
  const template = await readTemplate(path.join(__dirname, 'src', 'templates', 'blog-post.html'));
  
  // Ensure blog directory exists
  const blogDir = path.join(outputDir, 'blog');
  await fs.ensureDir(blogDir);
  
  // Sort posts by date (most recent first)
  posts.sort((a, b) => new Date(b['Date de publication']) - new Date(a['Date de publication']));
  
  for (const post of posts) {
    // Get recent posts (excluding current post)
    const recentPosts = config.blog.showRecentPosts ? 
      posts
        .filter(p => p['Slug'] !== post['Slug'])
        .slice(0, config.blog.recentPostsCount)
        .map(p => ({
          titre: p['Titre'],
          auteur: p['auteur'],
          date_publication: formatDate(p['Date de publication']),
          photo_article: p['photo article'],
          slug: p['Slug'],
          resume: truncateText(p['Résumé de l\'article'], 120)
        })) : [];

    // Prepare template data
    const templateData = {
      config,
      site: config.site,
      social: config.social,
      titre: post['Titre'],
      resume: post['Résumé de l\'article'],
      auteur: post['auteur'],
      photo_auteur: post['Photo auteur'] || config.site.author.photo,
      date_publication: formatDate(post['Date de publication']),
      duree_lecture: post['Durée de lecture'],
      photo_article: post['photo article'],
      contenu: post['Contenu article'],
      balise_title: post['meta title'] || `${post['Titre']} - ${config.site.company_name}`,
      meta_description: post['meta description'] || post['Résumé de l\'article'],
      recent_posts: recentPosts,
      showAuthorBio: config.blog.showAuthorBio,
      showSocialShare: config.blog.showSocialShare
    };
    
    const html = template(templateData);
    const outputFile = path.join(blogDir, `${post['Slug']}.html`);
    await fs.outputFile(outputFile, html);
    console.log(`Generated: ${post['Slug']}.html`);
  }
}

// Main function
async function main() {
  try {
    // Create output directory
    await fs.ensureDir(argv.output);
    
    // Copy Webflow export
    await fs.copy(argv.export, argv.output);
    
    // Read blog data and config
    const posts = await readCsvFile(argv.csv);
    const config = await readConfig(argv.config);
    
    // Copy and generate assets
    await copyAssets(argv.output, config);
    
    // Generate blog pages
    await generateBlogListing(posts, config, argv.output);
    await generateBlogPosts(posts, config, argv.output);
    
    console.log('Blog generation completed successfully!');
    console.log('\nTo test locally, run:');
    console.log('npm install (if you haven\'t already)');
    console.log('npm run serve');
    console.log(`\nThen visit: http://localhost:3000/blog.html`);
    
  } catch (error) {
    console.error('Error generating blog:', error);
    process.exit(1);
  }
}

// Run the script
main(); 