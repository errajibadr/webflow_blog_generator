#!/usr/bin/env node

const fs = require('fs-extra');
const path = require('path');
const yargs = require('yargs/yargs');
const { hideBin } = require('yargs/helpers');
const { copyAssets } = require('./assets');
const { registerHandlebarsHelpers } = require('./templates');
const { generateMainSitemap, generateBlogSitemap, generateSitemapIndex, generateRobotsTxt } = require('./sitemap');
const { generateHtaccess } = require('./htaccess');
const { copyDogPictures } = require('./images');
const { readAllPostFiles } = require('./posts');
const { generateBlogListing, generateBlogPosts } = require('./blog');
const { formatDate, truncateText } = require('./utils');
const { loadConfig } = require('./config');

// Parse command line arguments
const argv = yargs(hideBin(process.argv))
  .option('export', {
    alias: 'e',
    description: 'Path to Webflow export directory',
    type: 'string',
    demandOption: true
  })
  .option('blogs-repo', {
    alias: ['c', 'csv'],
    description: 'Path to directory containing blog posts (CSV, JSON, etc.)',
    type: 'string',
    demandOption: true
  })
  .option('config', {
    alias: 'f',
    description: 'Path to blog config file (JSON or YAML)',
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
  .option('force-hta', {
    description: 'Force overwrite existing .htaccess file',
    type: 'boolean',
    default: false
  })
  .help()
  .example('$0 --export ./webflow-export --blogs-repo ./posts --config ./config.json --output ./dist',
    'Generate blog using JSON config')
  .example('$0 --export ./webflow-export --blogs-repo ./posts --config ./config.yaml --output ./dist',
    'Generate blog using YAML config')
  .argv;

async function main() {
  try {
    // Create output directory
    await fs.ensureDir(argv.output);
    // Copy Webflow export
    await fs.copy(argv.export, argv.output);
    // Read config and inject outputDir/csvDir for downstream modules
    const config = await loadConfig(argv.config);
    config.outputDir = argv.output;
    
    // Use blogs-repo argument (potentially from alias csv)
    const blogsRepo = argv['blogs-repo'];
    config.csvDir = blogsRepo; // Keep the config key as csvDir for backward compatibility
    
    // Register handlebars helpers
    registerHandlebarsHelpers({ formatDate, truncateText, config });
    // Generate .htaccess file
    await generateHtaccess(argv.output, config, argv['force-hta']);
    // Copy default article images before processing files
    await copyDogPictures(argv.output);
    // Read blog data
    console.log('\n=== Starting Post Processing ===');
    const posts = await readAllPostFiles(blogsRepo, config);
    console.log('=== Post Processing Complete ===\n');
    console.log('\n=== Starting Blog Generation ===');
    // Copy and generate assets
    await copyAssets(argv.output, config);
    // Generate blog pages
    console.log('\nGenerating blog listing...');
    await generateBlogListing(posts, config, argv.output);
    console.log('\nGenerating individual blog posts...');
    await generateBlogPosts(posts, config, argv.output);
    // Generate sitemaps and robots.txt
    console.log('\nGenerating sitemaps and robots.txt...');
    await generateMainSitemap(argv.output, config);
    await generateBlogSitemap(argv.output, config, posts);
    await generateSitemapIndex(argv.output, config);
    await generateRobotsTxt(argv.output, config);
    console.log('\nBlog generation completed successfully!');
    console.log(`Total posts processed: ${posts.length}`);
    console.log('Generated posts:', posts.map(post => post['Titre']).join('\n- '));
    console.log('\nTo test locally, run:');
    console.log('npm install (if you haven\'t already)');
    console.log('npm run serve');
    console.log(`\nThen visit: http://localhost:${argv.port}/blog.html`);
  } catch (error) {
    console.error('Error generating blog:', error);
    process.exit(1);
  }
}

main(); 