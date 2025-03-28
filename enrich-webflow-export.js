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
    description: 'Path to directory containing blog posts CSV files',
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

// Global variable to store available default article images
let defaultArticleImages = [];
let currentImageIndex = 0;

// Helper function to format dates
function formatDate(dateString) {
  if (!dateString) {
    // Generate a random date from the last 4 days
    const date = new Date();
    const daysAgo = Math.floor(Math.random() * 4); // 0 to 3 days ago
    date.setDate(date.getDate() - daysAgo);
    return date.toLocaleDateString('fr-FR', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  }
  
  const date = new Date(dateString);
  if (isNaN(date.getTime())) {
    // If date is invalid, also generate random date
    const fallbackDate = new Date();
    const daysAgo = Math.floor(Math.random() * 4);
    fallbackDate.setDate(fallbackDate.getDate() - daysAgo);
    return fallbackDate.toLocaleDateString('fr-FR', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  }
  
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

// Helper function to get the next default article image (round-robin)
function getNextDefaultImage() {
  if (defaultArticleImages.length === 0) {
    return null;
  }
  // Get current image and increment index
  const image = defaultArticleImages[currentImageIndex];
  // Move to next image, wrap around if at end
  currentImageIndex = (currentImageIndex + 1) % defaultArticleImages.length;
  return image;
}

// Helper function to copy dog pictures and return their relative paths
async function copyDogPictures(outputDir) {
  const dogPicturesDir = path.join(__dirname, 'src', 'assets', 'images', 'dog_articles');
  const imagesOutputDir = path.join(outputDir, 'images');
  
  try {
    // Ensure the output directory exists
    await fs.ensureDir(imagesOutputDir);
    
    // Read all files from the dog pictures directory
    const files = await fs.readdir(dogPicturesDir);
    const imageFiles = files.filter(file => 
      file.toLowerCase().endsWith('.jpg') || 
      file.toLowerCase().endsWith('.jpeg') || 
      file.toLowerCase().endsWith('.png') ||
      file.toLowerCase().endsWith('.webp')
    );
    
    console.log(`Found ${imageFiles.length} default article images`);
    
    // Copy each image and store its web path
    defaultArticleImages = []; // Reset the array
    currentImageIndex = 0; // Reset the index
    
    for (const file of imageFiles) {
      const sourcePath = path.join(dogPicturesDir, file);
      const destPath = path.join(imagesOutputDir, file);
      await fs.copy(sourcePath, destPath);
      defaultArticleImages.push(`/images/${file}`);
    }
    
    // Shuffle the array to randomize initial order
    defaultArticleImages = defaultArticleImages.sort(() => Math.random() - 0.5);
    
    console.log('Default article images copied successfully');
    console.log('Available images:', defaultArticleImages);
  } catch (error) {
    console.error('Error copying default article images:', error);
  }
}

// Helper function to read and parse CSV file
async function readCsvFile(filePath, config) {
  console.log(`\nReading CSV file: ${filePath}`);
  const content = await fs.readFile(filePath, 'utf-8');
  
  const posts = parse(content, {
    columns: true,
    skip_empty_lines: true,
    delimiter: ';'
  });
  
  // Validate required fields and filter out invalid posts
  const validPosts = posts.filter((post, index) => {
    if (!post['Titre'] || !post['Slug']) {
      console.error(`Warning: Post #${index + 1} in ${path.basename(filePath)} is missing required Titre or Slug`);
      return false;
    }
    return true;
  }).map(post => ({
    ...post,
    // Use default author from config if none provided
    auteur: post['auteur'] || config.site.author.name,
    // Use next available dog picture if no article photo provided
    'photo article': post['photo article'] || getNextDefaultImage()
  }));

  if (validPosts.length !== posts.length) {
    console.warn(`Warning: ${posts.length - validPosts.length} posts were skipped due to missing Titre or Slug`);
  }
  
  console.log(`Found ${validPosts.length} valid posts in file ${path.basename(filePath)}`);
  // Log the distribution of images
  console.log('Image distribution:', validPosts.map(post => path.basename(post['photo article'] || 'no-image')));
  return validPosts;
}

// New helper function to read all CSV files from a directory
async function readAllCsvFiles(directoryPath, config) {
  try {
    console.log(`\n=== Reading CSV files from directory: ${directoryPath} ===`);
    const files = await fs.readdir(directoryPath);
    console.log('Found files:', files.filter(file => file.toLowerCase().endsWith('.csv')));
    
    const csvFiles = files.filter(file => file.toLowerCase().endsWith('.csv'));
    
    if (csvFiles.length === 0) {
      throw new Error('No CSV files found in the specified directory');
    }

    const allPosts = [];
    let processedFiles = 0;
    
    for (const file of csvFiles) {
      try {
        const filePath = path.join(directoryPath, file);
        console.log(`\n=== Processing file ${++processedFiles}/${csvFiles.length}: ${file} ===`);
        const posts = await readCsvFile(filePath, config);
        
        if (posts.length > 0) {
          console.log(`Adding ${posts.length} posts from ${file} to collection`);
          allPosts.push(...posts);
          console.log(`Current total posts in collection: ${allPosts.length}`);
        }
        
        console.log(`Successfully processed: ${file}`);
      } catch (error) {
        console.error(`Error processing ${file}:`, error.message);
      }
    }

    if (allPosts.length === 0) {
      throw new Error('No posts found in any CSV file');
    }

    console.log('\n=== Final post collection summary ===');
    console.log(`Total posts: ${allPosts.length}`);

    return allPosts;
  } catch (error) {
    throw new Error(`Error reading CSV directory: ${error.message}`);
  }
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
  await fs.ensureDir(path.join(outputDir, 'images')); // Add images directory

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

  // Copy default author image if it exists in config
  if (config.site.author.photo) {
    const authorPhotoSource = path.join(__dirname, config.site.author.photo);
    const authorPhotoFilename = path.basename(config.site.author.photo);
    const authorPhotoDest = path.join(outputDir, 'images', authorPhotoFilename);
    
    try {
      await fs.copy(authorPhotoSource, authorPhotoDest);
      console.log('Copied default author photo:', authorPhotoFilename);
      
      // Update the config to use the new path
      config.site.author.photo = `/images/${authorPhotoFilename}`;
    } catch (error) {
      console.error('Error copying default author photo:', error);
    }
  }

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
    
    // Read config first so we can use it during CSV processing
    const config = await readConfig(argv.config);
    
    // Copy default article images before processing CSVs
    await copyDogPictures(argv.output);
    
    // Read blog data and config
    console.log('\n=== Starting CSV Processing ===');
    const posts = await readAllCsvFiles(argv.csv, config);
    console.log('=== CSV Processing Complete ===\n');
    
    console.log('\n=== Starting Blog Generation ===');
    // Copy and generate assets
    await copyAssets(argv.output, config);
    
    // Generate blog pages
    console.log('\nGenerating blog listing...');
    await generateBlogListing(posts, config, argv.output);
    
    console.log('\nGenerating individual blog posts...');
    await generateBlogPosts(posts, config, argv.output);
    
    console.log('\nBlog generation completed successfully!');
    console.log(`Total posts processed: ${posts.length}`);
    console.log('Generated posts:', posts.map(post => post['Titre']).join('\n- '));
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