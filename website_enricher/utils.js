// Utility functions for website_enricher
const path = require('path');
const cheerio = require('cheerio');
const { isValidImageUrl, getNextDefaultImage } = require('./images');

/**
 * Parse a date string in French format (DD/MM/YYYY) or standard format.
 * @param {string} dateString
 * @returns {Date}
 */
function parseFrenchDate(dateString) {
  if (!dateString) return new Date();
  const parts = dateString.split('/');
  if (parts.length === 3) {
    return new Date(parts[2], parts[1] - 1, parts[0]);
  }
  const date = new Date(dateString);
  if (isNaN(date.getTime())) return new Date();
  return date;
}

/**
 * Format a date string to French locale (long format).
 * @param {string} dateString
 * @returns {string}
 */
function formatDate(dateString) {
  const date = parseFrenchDate(dateString);
  return date.toLocaleDateString('fr-FR', {
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  });
}

/**
 * Truncate text to a maximum length, adding ellipsis if needed.
 * @param {string} text
 * @param {number} maxLength
 * @returns {string}
 */
function truncateText(text, maxLength = 120) {
  if (!text) return '';
  if (text.length <= maxLength) return text;
  return text.substring(0, maxLength).trim() + '...';
}

/**
 * Normalize a string to a URL-friendly slug.
 * @param {string} text
 * @returns {string}
 */
function slugify(text) {
  if (!text) return '';
  return text
    .toLowerCase()
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '')
    .replace(/-+/g, '-');
}

/**
 * Escape a string for use in a RegExp.
 * @param {string} string
 * @returns {string}
 */
function escapeRegExp(string) {
  return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

/**
 * Format a date string for sitemap (YYYY-MM-DD).
 * @param {string} dateString
 * @returns {string}
 */
function formatSitemapDate(dateString) {
  const date = parseFrenchDate(dateString);
  return date.toISOString().split('T')[0];
}

/**
 * Get the latest blog update date from an array of posts.
 * @param {Array} posts
 * @returns {string} YYYY-MM-DD
 */
function getLastBlogUpdate(posts) {
  if (!posts || posts.length === 0) return new Date().toISOString().split('T')[0];
  const dates = posts.map(post => parseFrenchDate(post['Date de publication']));
  const latestDate = new Date(Math.max(...dates));
  return latestDate.toISOString().split('T')[0];
}

/**
 * Increment heading levels in HTML content (convert <h1> to <h2> only).
 * @param {string} content
 * @returns {string}
 */
function incrementHeadingLevels(content) {
  if (!content) return content;
  const $ = cheerio.load(content);
  $('h1').each((_, elem) => {
    const $elem = $(elem);
    const $newHeading = $('<h2>').html($elem.html());
    Object.keys(elem.attribs).forEach(attr => {
      $newHeading.attr(attr, elem.attribs[attr]);
    });
    $elem.replaceWith($newHeading);
  });
  return $.html();
}

/**
 * Process article content and fix invalid image sources.
 * @param {string} content
 * @param {string} outputDir
 * @param {string} csvDir
 * @returns {string}
 */
function processArticleContent(content, outputDir, csvDir) {
  if (!content) return content;
  const $ = cheerio.load(content);
  $('img').each((index, element) => {
    const img = $(element);
    const currentSrc = img.attr('src');
    if (!isValidImageUrl(currentSrc, outputDir, csvDir)) {
      // Get next default image
      const newSrc = getNextDefaultImage(outputDir);
      if (newSrc) {
        img.attr('src', newSrc);
      }
    } else if (currentSrc && !currentSrc.startsWith('http') && !currentSrc.startsWith('/images/')) {
      // If the image was found as a relative path, update the src to point to the copied image
      const filename = require('path').basename(currentSrc);
      const newSrc = `/images/${filename}`;
      img.attr('src', newSrc);
    }
  });
  const processedHtml = $.html();
  return incrementHeadingLevels(processedHtml);
}

module.exports = {
  parseFrenchDate,
  formatDate,
  truncateText,
  slugify,
  escapeRegExp,
  formatSitemapDate,
  getLastBlogUpdate,
  incrementHeadingLevels,
  processArticleContent
}; 