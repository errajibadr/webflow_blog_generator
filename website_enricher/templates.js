const Handlebars = require('handlebars');
const fs = require('fs-extra');
const path = require('path');

function registerHandlebarsHelpers({ formatDate, truncateText, config }) {
  Handlebars.registerHelper('formatDate', formatDate);
  Handlebars.registerHelper('truncate', truncateText);
  Handlebars.registerHelper('currentYear', function() {
    return new Date().getFullYear();
  });
  Handlebars.registerHelper('eq', function(a, b) {
    return a === b;
  });
  Handlebars.registerHelper('hasValue', function(value) {
    return value && value.trim && value.trim() !== '';
  });
  Handlebars.registerHelper('getConfig', function(pathStr) {
    const parts = pathStr.split('.');
    let value = config;
    for (const part of parts) {
      if (value && value[part]) {
        value = value[part];
      } else {
        return '';
      }
    }
    return value;
  });
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
  Handlebars.registerHelper('currentDate', function() {
    return new Date().toISOString().split('T')[0];
  });
  Handlebars.registerHelper('formatSitemapDate', function(dateString) {
    if (!formatDate) return dateString;
    const date = formatDate(dateString);
    return date;
  });
}

async function readTemplate(templatePath) {
  const content = await fs.readFile(templatePath, 'utf-8');
  return Handlebars.compile(content);
}

module.exports = {
  registerHandlebarsHelpers,
  readTemplate,
  Handlebars
}; 