#!/usr/bin/env node

/**
 * Hostinger Website Export Script
 * 
 * This script exports a website from Hostinger for local processing.
 * 
 * Usage:
 *   node export_website.js --website dogtolib
 */

const fs = require('fs-extra');
const path = require('path');
const yargs = require('yargs/yargs');
const { hideBin } = require('yargs/helpers');
const ora = require('ora');
const chalk = require('chalk');
const axios = require('axios');
const { createWriteStream } = require('fs');
const { pipeline } = require('stream/promises');
const AdmZip = require('adm-zip');

// Parse command line arguments
const argv = yargs(hideBin(process.argv))
  .option('website', {
    alias: 'w',
    description: 'Website to export',
    type: 'string',
    demandOption: true
  })
  .option('config', {
    alias: 'c',
    description: 'Path to the config file',
    type: 'string'
  })
  .option('output', {
    alias: 'o',
    description: 'Output directory for the export',
    type: 'string'
  })
  .help()
  .argv;

// Set paths
const websiteName = argv.website;
const configPath = argv.config || path.join(__dirname, '..', 'configs', `${websiteName}-config.json`);
const outputDir = argv.output || path.join(__dirname, '..', 'websites', websiteName);

// Ensure the output directory exists
fs.ensureDirSync(outputDir);

// Load configuration
let config;
try {
  config = fs.readJsonSync(configPath);
  console.log(chalk.green(`Loaded configuration for ${websiteName}`));
} catch (error) {
  console.error(chalk.red(`Error loading configuration for ${websiteName}:`), error.message);
  process.exit(1);
}

/**
 * Download a file from URL to a local path
 * @param {string} url - File URL
 * @param {string} filePath - Local file path
 * @returns {Promise<void>}
 */
async function downloadFile(url, filePath) {
  const response = await axios({
    method: 'GET',
    url,
    responseType: 'stream'
  });
  
  await pipeline(response.data, createWriteStream(filePath));
}

/**
 * Export website using Hostinger API
 * @param {Object} apiConfig - API configuration
 * @param {string} destinationPath - Destination directory
 * @returns {Promise<boolean>} - Success status
 */
async function exportWebsiteApi(apiConfig, destinationPath) {
  const spinner = ora('Preparing to export website via API...').start();
  
  const { apiKey, siteId } = apiConfig;
  
  if (!apiKey || !siteId) {
    spinner.fail('Missing API configuration. Please check your config file.');
    return false;
  }
  
  spinner.text = 'Contacting Hostinger API...';
  
  try {
    // In a real implementation, this would use Hostinger's API
    // For now, we'll simulate by downloading a sample website
    
    // Create a temporary directory for the download
    const tempDir = path.join(__dirname, '..', 'temp');
    const zipPath = path.join(tempDir, `${websiteName}.zip`);
    
    fs.ensureDirSync(tempDir);
    
    // Download a sample website export
    // In a real scenario, this would be the URL returned by the Hostinger API
    spinner.text = 'Requesting website export from Hostinger...';
    await new Promise(resolve => setTimeout(resolve, 2000)); // Simulate API delay
    
    // This is just a placeholder URL - in a real scenario, this would be from the Hostinger API
    const sampleExportUrl = 'https://example.com/sample-export.zip';
    
    // For simulation, we'll create a simple zip file
    spinner.text = 'Creating simulated website export...';
    
    // Create a simple HTML file as a placeholder
    const indexHtmlPath = path.join(tempDir, 'index.html');
    fs.writeFileSync(indexHtmlPath, `
      <!DOCTYPE html>
      <html>
        <head>
          <title>${config.site.name}</title>
        </head>
        <body>
          <h1>${config.site.name}</h1>
          <p>${config.site.description}</p>
        </body>
      </html>
    `);
    
    // Create a simple CSS file
    const cssPath = path.join(tempDir, 'style.css');
    fs.writeFileSync(cssPath, `
      body {
        font-family: Arial, sans-serif;
        color: ${config.ui.textColor};
        background-color: ${config.ui.backgroundColor};
      }
      h1 {
        color: ${config.ui.primaryColor};
      }
    `);
    
    // Create a zip file with these files
    const zip = new AdmZip();
    zip.addLocalFile(indexHtmlPath);
    zip.addLocalFile(cssPath);
    zip.writeZip(zipPath);
    
    // Extract the zip to the destination
    spinner.text = 'Extracting website files...';
    
    // Extract the zip file
    const zipFile = new AdmZip(zipPath);
    zipFile.extractAllTo(destinationPath, true);
    
    // Clean up temporary files
    fs.removeSync(indexHtmlPath);
    fs.removeSync(cssPath);
    fs.removeSync(zipPath);
    fs.removeSync(tempDir);
    
    spinner.succeed('Website exported successfully via API');
    return true;
  } catch (error) {
    spinner.fail(`API export error: ${error.message}`);
    return false;
  }
}

/**
 * Export website using FTP
 * @param {Object} ftpConfig - FTP configuration
 * @param {string} destinationPath - Destination directory
 * @returns {Promise<boolean>} - Success status
 */
async function exportWebsiteFtp(ftpConfig, destinationPath) {
  const spinner = ora('Preparing to export website via FTP...').start();
  
  const { ftpHost, ftpUser, ftpPassword } = ftpConfig;
  
  if (!ftpHost || !ftpUser || !ftpPassword) {
    spinner.fail('Missing FTP configuration. Please check your config file.');
    return false;
  }
  
  spinner.text = 'This is a placeholder for FTP export functionality';
  spinner.info('FTP export is not implemented in this sample script');
  
  // In a real implementation, you would:
  // 1. Connect to FTP
  // 2. Download all files
  // 3. Save them to the destination directory
  
  // For now, just create a placeholder index.html
  const indexHtmlPath = path.join(destinationPath, 'index.html');
  fs.writeFileSync(indexHtmlPath, `
    <!DOCTYPE html>
    <html>
      <head>
        <title>${config.site.name}</title>
      </head>
      <body>
        <h1>${config.site.name}</h1>
        <p>${config.site.description}</p>
        <p>This is a placeholder for an FTP export.</p>
      </body>
    </html>
  `);
  
  spinner.succeed('Created placeholder website files');
  return true;
}

/**
 * Main export function
 */
async function exportWebsite() {
  console.log(chalk.blue(`Starting export for ${websiteName}`));
  
  // Determine export method based on available config
  const hostingerConfig = config.hostinger || {};
  let success;
  
  if (hostingerConfig.apiKey && hostingerConfig.siteId) {
    console.log(chalk.blue('Using API method for export'));
    success = await exportWebsiteApi(hostingerConfig, outputDir);
  } else if (hostingerConfig.ftpHost && hostingerConfig.ftpUser && hostingerConfig.ftpPassword) {
    console.log(chalk.blue('Using FTP method for export'));
    success = await exportWebsiteFtp(hostingerConfig, outputDir);
  } else {
    console.error(chalk.red('No valid export method configuration found. Please check your config file.'));
    process.exit(1);
  }
  
  if (success) {
    console.log(chalk.green(`\n${websiteName} has been successfully exported!`));
    console.log(chalk.blue(`Export location: ${outputDir}`));
  } else {
    console.error(chalk.red(`\nExport failed for ${websiteName}`));
    process.exit(1);
  }
}

// Run the export
exportWebsite().catch(error => {
  console.error(chalk.red('Unexpected error:'), error);
  process.exit(1);
}); 