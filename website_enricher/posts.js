const fs = require('fs-extra');
const path = require('path');
const { parse } = require('csv-parse/sync');
const { slugify, processArticleContent } = require('./utils');
const { getNextDefaultImage } = require('./images');

/**
 * Read and parse a CSV file for blog posts.
 * @param {string} filePath
 * @param {object} config
 * @returns {Promise<Array<object>>}
 */
async function readCsvFile(filePath, config) {
  const content = await fs.readFile(filePath, 'utf-8');
  const posts = parse(content, {
    columns: true,
    skip_empty_lines: true,
    delimiter: ';'
  });
  const validPosts = posts.filter((post) => post['Titre'] && post['Slug']).map(post => ({
    ...post,
    auteur: post['auteur'] || config.site.author.name,
    'photo article': post['photo article'] || getNextDefaultImage(),
    'Contenu article': processArticleContent(post['Contenu article'], config.outputDir, config.csvDir),
    'Slug': slugify(post['Slug'])
  }));
  return validPosts;
}

/**
 * Read and parse a JSON file for blog posts.
 * @param {string} filePath
 * @param {object} config
 * @returns {Promise<Array<object>>}
 */
async function readJsonFile(filePath, config) {
  const content = await fs.readFile(filePath, 'utf-8');
  const posts = JSON.parse(content);
  const postsArray = Array.isArray(posts) ? posts : [posts];
  const validPosts = postsArray.filter((post) => post['Titre'] && post['Slug']).map(post => ({
    ...post,
    auteur: post['auteur'] || config.site.author.name,
    'photo article': post['photo article'] || getNextDefaultImage(),
    'Contenu article': processArticleContent(post['Contenu article'], config.outputDir, config.csvDir),
    'Slug': slugify(post['Slug'])
  }));
  return validPosts;
}

/**
 * Read and parse any supported file (CSV or JSON) for blog posts.
 * @param {string} filePath
 * @param {object} config
 * @returns {Promise<Array<object>>}
 */
async function readPostsFile(filePath, config) {
  const extension = path.extname(filePath).toLowerCase();
  switch (extension) {
    case '.csv':
      return readCsvFile(filePath, config);
    case '.json':
      return readJsonFile(filePath, config);
    default:
      throw new Error(`Unsupported file type: ${extension}`);
  }
}

/**
 * Read and parse all post files from a directory.
 * @param {string} directoryPath
 * @param {object} config
 * @returns {Promise<Array<object>>}
 */
async function readAllPostFiles(directoryPath, config) {
  const files = await fs.readdir(directoryPath);
  const supportedFiles = files.filter(file => file.toLowerCase().endsWith('.csv') || file.toLowerCase().endsWith('.json'));
  if (supportedFiles.length === 0) {
    throw new Error('No CSV or JSON files found in the specified directory');
  }
  const allPosts = [];
  for (const file of supportedFiles) {
    const filePath = path.join(directoryPath, file);
    const posts = await readPostsFile(filePath, config);
    if (posts.length > 0) {
      allPosts.push(...posts);
    }
  }
  if (allPosts.length === 0) {
    throw new Error('No posts found in any file');
  }
  return allPosts;
}

module.exports = {
  readCsvFile,
  readJsonFile,
  readPostsFile,
  readAllPostFiles
}; 