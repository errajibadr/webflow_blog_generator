const fs = require('fs-extra');
const path = require('path');

async function generateHtaccess(outputDir, config, forceOverwrite = false) {
  if (!config.site || !config.site.domain) {
    console.error('Warning: No domain configured in config.site.domain. .htaccess file will not be generated.');
    return;
  }
  try {
    const domain = config.site.domain.replace(/^https?:\/\/(www\.)?/, '').trim();
    const escapedDomain = domain.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    const templatePath = path.join(__dirname, 'src', 'templates', '.htaccess.template');
    const content = await fs.readFile(templatePath, 'utf-8');
    // Simple template replacement (if using Handlebars, import and use it instead)
    const htaccessContent = content
      .replace(/\{\{\s*domain\s*\}\}/g, domain)
      .replace(/\{\{\s*escaped_domain\s*\}\}/g, escapedDomain);
    const htaccessPath = path.join(outputDir, '.htaccess');
    const exists = await fs.pathExists(htaccessPath);
    if (!exists || forceOverwrite) {
      await fs.writeFile(htaccessPath, htaccessContent);
      console.log(exists ? '.htaccess file overwritten' : '.htaccess file created successfully');
    } else {
      console.log('.htaccess file already exists, skipping creation (use --force-hta to overwrite)');
    }
  } catch (error) {
    console.error('Error creating .htaccess file:', error);
  }
}

module.exports = {
  generateHtaccess
}; 