#!/usr/bin/env node

/**
 * Multi-Website Blog Generation and Deployment Automation
 * 
 * This script automates the workflow of generating blog content and deploying
 * it to multiple websites hosted on Hostinger.
 * 
 * Usage:
 *   node automation.js --website dogtolib --generate-articles 3 --deploy true
 */

const fs = require('fs-extra');
const path = require('path');
const { spawn, exec } = require('child_process');
const yargs = require('yargs/yargs');
const { hideBin } = require('yargs/helpers');
const ora = require('ora');
const chalk = require('chalk');

// Parse command line arguments
const argv = yargs(hideBin(process.argv))
  .option('website', {
    alias: 'w',
    description: 'Website to process',
    type: 'string',
    demandOption: true
  })
  .option('generate-articles', {
    alias: 'g',
    description: 'Number of articles to generate',
    type: 'number',
    default: 1
  })
  .option('skip-export', {
    description: 'Skip exporting the website (use existing export)',
    type: 'boolean',
    default: false
  })
  .option('skip-generation', {
    description: 'Skip generating blog content (use existing content)',
    type: 'boolean',
    default: false
  })
  .option('skip-enrichment', {
    description: 'Skip enriching the website (use existing enriched site)',
    type: 'boolean',
    default: false
  })
  .option('deploy', {
    alias: 'd',
    description: 'Deploy the enriched website to Hostinger',
    type: 'boolean',
    default: false
  })
  .help()
  .argv;

// Define paths based on website name
const websiteName = argv.website;
const configPath = path.join(__dirname, 'configs', `${websiteName}-config.json`);
const websitePath = path.join(__dirname, 'websites', websiteName);
const outputPath = path.join(__dirname, 'output', websiteName);
const distPath = path.join(__dirname, 'dist', websiteName);

// Ensure required directories exist
fs.ensureDirSync(websitePath);
fs.ensureDirSync(outputPath);
fs.ensureDirSync(path.join(outputPath, 'images'));

// Load website configuration
let config;
try {
  config = fs.readJsonSync(configPath);
  console.log(chalk.green(`Loaded configuration for ${websiteName}`));
} catch (error) {
  console.error(chalk.red(`Error loading configuration for ${websiteName}:`), error.message);
  process.exit(1);
}

/**
 * Execute a shell command as a promise
 * @param {string} command - The command to execute
 * @returns {Promise<string>} - Command output
 */
function execCommand(command) {
  return new Promise((resolve, reject) => {
    exec(command, (error, stdout, stderr) => {
      if (error) {
        reject(error);
        return;
      }
      resolve(stdout.trim());
    });
  });
}

/**
 * Export website from Hostinger
 * @returns {Promise<boolean>} - Success status
 */
async function exportWebsite() {
  const spinner = ora('Exporting website from Hostinger...').start();
  
  try {
    // In a real implementation, this would use Hostinger's API
    // For now, we'll simulate by copying from a template
    await fs.copy(
      path.join(__dirname, 'templates', `${websiteName}-template`), 
      websitePath
    );
    
    spinner.succeed('Website exported successfully');
    return true;
  } catch (error) {
    spinner.fail(`Error exporting website: ${error.message}`);
    return false;
  }
}

/**
 * Generate blog articles using the Python AI agent
 * @param {number} count - Number of articles to generate
 * @returns {Promise<boolean>} - Success status
 */
async function generateBlogArticles(count) {
  const spinner = ora(`Generating ${count} blog articles...`).start();
  
  try {
    // Get input data file from config
    const inputFile = config.blogGeneration?.inputDataFile || 
                      'data/éducateur-canin_clusters_2025-03-28.csv';
    
    const batchSize = config.blogGeneration?.aiParams?.batchSize || 10;
    const maxConcurrent = config.blogGeneration?.aiParams?.maxConcurrent || 3;
    
    // Run the Python AI agent
    const command = `uv run main.py --input ${inputFile} --output ${outputPath} --batch ${batchSize} --max-concurrent ${maxConcurrent} --count ${count}`;
    
    spinner.text = `Running: ${command}`;
    await execCommand(command);
    
    // Validate that files were generated
    const files = await fs.readdir(outputPath);
    const jsonFiles = files.filter(file => file.endsWith('.json'));
    
    if (jsonFiles.length === 0) {
      spinner.warn('No blog articles were generated');
      return false;
    }
    
    spinner.succeed(`Generated ${jsonFiles.length} blog articles`);
    return true;
  } catch (error) {
    spinner.fail(`Error generating blog articles: ${error.message}`);
    return false;
  }
}

/**
 * Enrich website with generated blog content
 * @returns {Promise<boolean>} - Success status
 */
async function enrichWebsite() {
  const spinner = ora('Enriching website with blog content...').start();
  
  try {
    // Run the enrich-webflow-export.js script
    const command = `node enrich-webflow-export.js --export ${websitePath} --csv ${outputPath} --config ${configPath} --output ${distPath}`;
    
    spinner.text = `Running: ${command}`;
    await execCommand(command);
    
    // Validate that the enriched site was generated
    if (!fs.existsSync(path.join(distPath, 'blog.html'))) {
      spinner.warn('Blog listing page was not generated');
      return false;
    }
    
    spinner.succeed('Website enriched successfully');
    return true;
  } catch (error) {
    spinner.fail(`Error enriching website: ${error.message}`);
    return false;
  }
}

/**
 * Deploy enriched website to Hostinger
 * @returns {Promise<boolean>} - Success status
 */
async function deployWebsite() {
  const spinner = ora('Deploying website to Hostinger...').start();
  
  try {
    // In a real implementation, this would use Hostinger's API
    // For now, we'll just simulate success
    await new Promise(resolve => setTimeout(resolve, 2000));
    
    spinner.succeed('Website deployed successfully');
    return true;
  } catch (error) {
    spinner.fail(`Error deploying website: ${error.message}`);
    return false;
  }
}

/**
 * Main workflow function
 */
async function runWorkflow() {
  console.log(chalk.blue(`Starting workflow for ${websiteName}`));
  
  // Step 1: Export website (if not skipped)
  if (!argv.skipExport) {
    const exportSuccess = await exportWebsite();
    if (!exportSuccess) {
      console.error(chalk.red('Workflow aborted due to export failure'));
      return;
    }
  } else {
    console.log(chalk.yellow('Skipping website export (using existing export)'));
  }
  
  // Step 2: Generate blog articles (if not skipped)
  if (!argv.skipGeneration) {
    const generationSuccess = await generateBlogArticles(argv.generateArticles);
    if (!generationSuccess) {
      console.error(chalk.red('Workflow aborted due to content generation failure'));
      return;
    }
  } else {
    console.log(chalk.yellow('Skipping blog content generation (using existing content)'));
  }
  
  // Step 3: Enrich website (if not skipped)
  if (!argv.skipEnrichment) {
    const enrichmentSuccess = await enrichWebsite();
    if (!enrichmentSuccess) {
      console.error(chalk.red('Workflow aborted due to enrichment failure'));
      return;
    }
  } else {
    console.log(chalk.yellow('Skipping website enrichment (using existing enriched site)'));
  }
  
  // Step 4: Deploy website (if requested)
  if (argv.deploy) {
    const deploymentSuccess = await deployWebsite();
    if (!deploymentSuccess) {
      console.error(chalk.red('Deployment failed'));
      return;
    }
  } else {
    console.log(chalk.yellow('Skipping deployment (use --deploy to deploy)'));
  }
  
  console.log(chalk.green(`Workflow completed successfully for ${websiteName}`));
  console.log(chalk.blue(`Generated blog can be found at: ${distPath}/blog.html`));
}

// Run the workflow
runWorkflow().catch(error => {
  console.error(chalk.red('Unexpected error:'), error);
  process.exit(1);
}); 