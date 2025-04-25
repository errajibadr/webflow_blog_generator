const fs = require('fs-extra');
const path = require('path');
const { SitemapStream, streamToPromise } = require('sitemap');
const { Readable } = require('stream');
const { glob } = require('glob');
const { formatSitemapDate, getLastBlogUpdate } = require('./utils');

async function discoverHtmlFiles(outputDir, excludePatterns = []) {
  try {
    const files = await glob('**/*.html', {
      cwd: outputDir,
      ignore: excludePatterns
    });
    return files;
  } catch (error) {
    console.error('Error discovering HTML files:', error);
    return [];
  }
}

async function generateMainSitemap(outputDir, config) {
  if (!config.site || !config.site.domain) {
    console.error('Warning: No domain configured in config.site.domain. Main sitemap will not be generated.');
    return;
  }
  try {
    const domain = `https://www.${config.site.domain.replace(/^https?:\/\/(www\.)?/, '')}`;
    const files = await discoverHtmlFiles(outputDir, ['blog/**', 'blog.html']);
    const links = files.map(file => ({
      url: `${domain}/${file}`,
      changefreq: 'weekly',
      priority: file === 'index.html' ? 1.0 : 0.7
    }));
    const stream = new SitemapStream({ hostname: domain });
    const data = await streamToPromise(Readable.from(links).pipe(stream));
    await fs.writeFile(path.join(outputDir, 'sitemap-main.xml'), data);
    console.log('Main sitemap generated successfully');
    console.log('Discovered pages:', files.length);
  } catch (error) {
    console.error('Error generating main sitemap:', error);
  }
}

async function generateBlogSitemap(outputDir, config, posts) {
  if (!config.site || !config.site.domain) {
    console.error('Warning: No domain configured in config.site.domain. Blog sitemap will not be generated.');
    return;
  }
  try {
    const domain = `https://www.${config.site.domain.replace(/^https?:\/\/(www\.)?/, '')}`;
    const lastBlogUpdate = getLastBlogUpdate(posts);
    const links = [
      {
        url: `${domain}/blog.html`,
        changefreq: 'daily',
        priority: 0.8,
        lastmod: lastBlogUpdate
      },
      ...posts.map(post => ({
        url: `${domain}/blog/${post.Slug}.html`,
        changefreq: 'monthly',
        priority: 0.6,
        lastmod: formatSitemapDate(post['Date de publication'])
      }))
    ];
    const stream = new SitemapStream({ hostname: domain });
    const data = await streamToPromise(Readable.from(links).pipe(stream));
    await fs.writeFile(path.join(outputDir, 'sitemap-blog.xml'), data);
    console.log('Blog sitemap generated successfully');
    console.log('Total blog URLs:', links.length);
  } catch (error) {
    console.error('Error generating blog sitemap:', error);
  }
}

async function generateSitemapIndex(outputDir, config) {
  if (!config.site || !config.site.domain) {
    console.error('Warning: No domain configured in config.site.domain. Sitemap index will not be generated.');
    return;
  }
  try {
    const domain = `https://www.${config.site.domain.replace(/^https?:\/\/(www\.)?/, '')}`;
    const sitemaps = [
      {
        url: `${domain}/sitemap-main.xml`,
        lastmod: new Date().toISOString()
      },
      {
        url: `${domain}/sitemap-blog.xml`,
        lastmod: new Date().toISOString()
      }
    ];
    const stream = new SitemapStream({ hostname: domain, level: 'index' });
    const data = await streamToPromise(Readable.from(sitemaps).pipe(stream));
    await fs.writeFile(path.join(outputDir, 'sitemap.xml'), data);
    console.log('Sitemap index generated successfully');
  } catch (error) {
    console.error('Error generating sitemap index:', error);
  }
}

async function generateRobotsTxt(outputDir, config) {
  if (!config.site || !config.site.domain) {
    console.error('Warning: No domain configured in config.site.domain. robots.txt file will not be generated.');
    return;
  }
  try {
    const domain = config.site.domain.replace(/^https?:\/\/(www\.)?/, '').trim();
    const templatePath = path.join(__dirname, 'src', 'templates', 'robots.txt.template');
    const content = await fs.readFile(templatePath, 'utf-8');
    const robotsTxtContent = content.replace(/\{\{\s*domain\s*\}\}/g, domain);
    const robotsTxtPath = path.join(outputDir, 'robots.txt');
    await fs.writeFile(robotsTxtPath, robotsTxtContent);
    console.log('robots.txt file created successfully');
  } catch (error) {
    console.error('Error creating robots.txt file:', error);
  }
}

module.exports = {
  discoverHtmlFiles,
  generateMainSitemap,
  generateBlogSitemap,
  generateSitemapIndex,
  generateRobotsTxt
}; 