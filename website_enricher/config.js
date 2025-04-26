const fs = require('fs-extra');
const path = require('path');
const yaml = require('js-yaml');

/**
 * Load config from either YAML or JSON file
 * @param {string} filePath - Path to config file (.yaml, .yml, or .json)
 * @returns {Object} - Parsed config object
 */
async function loadConfig(filePath) {
  try {
    // Read file content
    const content = await fs.readFile(filePath, 'utf-8');
    
    // Determine file format based on extension
    const extension = path.extname(filePath).toLowerCase();
    
    let config;
    const filename = path.basename(filePath).toLowerCase();
    const isFullSiteYaml = filename.startsWith('@') || filename.includes('dogtolib');
    
    // Parse based on file extension
    if (extension === '.yaml' || extension === '.yml') {
      try {
        let rawConfig = yaml.load(content);
        
        // Handle YAML structure - if full site YAML, extract blog_config
        if (isFullSiteYaml && rawConfig.blog_config) {
          config = rawConfig.blog_config;
          console.log('Loaded blog_config from full site YAML configuration:', filePath);
        } else {
          // If it's a specific blog YAML (not full site), use as is
          config = rawConfig;
          console.log('Loaded YAML blog configuration from:', filePath);
        }
      } catch (yamlError) {
        console.error('Error parsing YAML config:', yamlError.message);
        throw new Error(`Failed to parse YAML config: ${yamlError.message}`);
      }
    } else {
      // Default to JSON for .json or any other extension (backward compatibility)
      try {
        config = JSON.parse(content);
        console.log('Loaded JSON configuration from:', filePath);
      } catch (jsonError) {
        console.error('Error parsing JSON config:', jsonError.message);
        throw new Error(`Failed to parse JSON config: ${jsonError.message}`);
      }
    }
    
    // Validate config structure
    validateConfig(config);
    
    return config;
  } catch (error) {
    if (error.code === 'ENOENT') {
      throw new Error(`Config file not found: ${filePath}`);
    }
    throw error;
  }
}

/**
 * Validate required config fields
 * @param {Object} config - Config object to validate
 * @throws {Error} If required fields are missing
 */
function validateConfig(config) {
  // Check for required fields
  if (!config) {
    throw new Error('Config is empty or invalid');
  }
  
  // Check for site section
  if (!config.site) {
    throw new Error('Missing "site" section in config');
  }
  
  // Check for critical fields
  if (!config.site.title) {
    throw new Error('Missing "site.title" in config');
  }
  
  if (!config.site.domain) {
    throw new Error('Missing "site.domain" in config');
  }
  
  return true;
}

module.exports = {
  loadConfig
}; 