const path = require('path');
const { readTemplate } = require('./templates');
const { parseFrenchDate, formatDate, truncateText, slugify } = require('./utils');

/**
 * Generate blog listing page
 */
async function generateBlogListing(posts, config, outputDir) {
  const template = await readTemplate(path.join(__dirname, 'src', 'templates', 'blog.html'));
  posts.sort((a, b) => {
    const dateA = parseFrenchDate(a['Date de publication']);
    const dateB = parseFrenchDate(b['Date de publication']);
    return dateB - dateA;
  });
  const templateData = {
    config,
    posts: posts.map(post => ({
      titre: post['Titre'],
      resume: post["Résumé de l'article"],
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
  await require('fs-extra').outputFile(outputFile, html);
  console.log('Generated: blog.html with sorted posts');
}

/**
 * Generate individual blog post pages
 */
async function generateBlogPosts(posts, config, outputDir) {
  const template = await readTemplate(path.join(__dirname, 'src', 'templates', 'blog-post.html'));
  const blogDir = path.join(outputDir, 'blog');
  await require('fs-extra').ensureDir(blogDir);
  if (!config.site || !config.site.domain) {
    console.error('Warning: No domain configured in config.site.domain. Canonical URLs will not be generated.');
    return;
  }
  const baseDomain = config.site.domain.trim();
  const wwwDomain = `https://www.${baseDomain.replace(/^https?:\/\/(www\.)?/, '')}`;
  posts.sort((a, b) => {
    const dateA = parseFrenchDate(a['Date de publication']);
    const dateB = parseFrenchDate(b['Date de publication']);
    return dateB - dateA;
  });
  for (const post of posts) {
    const recentPosts = config.blog.showRecentPosts ?
      posts.filter(p => p['Slug'] !== post['Slug'])
        .slice(0, config.blog.recentPostsCount)
        .map(p => ({
          titre: p['Titre'],
          auteur: p['auteur'],
          date_publication: formatDate(p['Date de publication']),
          photo_article: p['photo article'],
          slug: p['Slug'],
          resume: truncateText(p["Résumé de l'article"], 120)
        })) : [];
    const articleTypesSet = new Set();
    for (let i = 1; i <= 8; i++) {
      const typeKey = i === 1 ? "Type d'article" : `Type d'article ${i}`;
      if (post[typeKey] && post[typeKey].trim()) {
        articleTypesSet.add(post[typeKey].trim());
      }
    }
    const secondaryTypeKey = "Type d'article secondaire";
    if (post[secondaryTypeKey] && post[secondaryTypeKey].trim()) {
      const secondaryTypes = post[secondaryTypeKey].split(',');
      secondaryTypes.forEach(type => {
        const trimmedType = type.trim();
        if (trimmedType) {
          articleTypesSet.add(trimmedType);
        }
      });
    }
    const articleTypes = Array.from(articleTypesSet);
    let processedContent = post['Contenu article'];
    if (config.site.cta_link && processedContent) {
      processedContent = processedContent.replace(/\{\{cta_link\}\}/g, config.site.cta_link);
    }
    let jsonLdScript = '';
    if (post['JSON_LD']) {
      try {
        let jsonLdArr = JSON.parse(post['JSON_LD']);
        jsonLdArr = jsonLdArr.map(obj => {
          let str = JSON.stringify(obj);
          str = str.replace(/\{author\}/g, post['auteur'] || config.site.author.name);
          str = str.replace(/\{main_entity_of_page\}/g, `${wwwDomain}/blog/${post['Slug']}.html`);
          return JSON.parse(str);
        });
        jsonLdScript = `<script type=\"application/ld+json\">${JSON.stringify(jsonLdArr, null, 2)}</script>`;
      } catch (e) {
        console.error('Error processing JSON_LD for post', post['Slug'], e);
        jsonLdScript = '';
      }
    }
    const templateData = {
      config,
      site: config.site,
      social: config.social,
      titre: post['Titre'],
      resume: post["Résumé de l'article"],
      auteur: post['auteur'],
      photo_auteur: post['Photo auteur'] || config.site.author.photo,
      date_publication: formatDate(post['Date de publication']),
      duree_lecture: post['Durée de lecture'],
      photo_article: post['photo article'],
      contenu: processedContent,
      balise_title: post['meta title'] || `${post['Titre']} - ${config.site.company_name}`,
      meta_description: post['meta description'] || post["Résumé de l'article"],
      canonical_url: `${wwwDomain}/blog/${post['Slug']}.html`,
      recent_posts: recentPosts,
      showAuthorBio: config.blog.showAuthorBio,
      showSocialShare: config.blog.showSocialShare,
      article_types: articleTypes,
      json_ld_script: jsonLdScript
    };
    const html = template(templateData);
    const outputFile = path.join(blogDir, `${post['Slug']}.html`);
    await require('fs-extra').outputFile(outputFile, html);
    console.log(`Generated: ${post['Slug']}.html`);
  }
}

module.exports = {
  generateBlogListing,
  generateBlogPosts
}; 