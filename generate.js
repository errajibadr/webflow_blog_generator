#!/usr/bin/env node

const path = require('path');
const fs = require('fs-extra');
const { parse } = require('csv-parse/sync');
const Handlebars = require('handlebars');
const { program } = require('commander');

program
    .version('1.0.0')
    .description('Générateur de blog à partir d\'exports Webflow')
    .requiredOption('-s, --source <directory>', 'Dossier source contenant l\'export Webflow')
    .requiredOption('-c, --config <file>', 'Fichier de configuration du blog (JSON)')
    .option('-o, --output <directory>', 'Dossier de sortie', 'dist')
    .parse(process.argv);

const options = program.opts();

async function loadConfig(configPath) {
    try {
        const configContent = await fs.readFile(configPath, 'utf-8');
        return JSON.parse(configContent);
    } catch (error) {
        console.error('Erreur lors de la lecture du fichier de configuration:', error);
        process.exit(1);
    }
}

function formatDate(dateString, locale = 'fr-FR') {
    if (!dateString) return '';
    const date = new Date(dateString);
    return date.toLocaleDateString(locale, {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
    });
}

function truncateText(text, maxLength = 120) {
    if (!text) return '';
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength).trim() + '...';
}

async function loadPosts(sourceDir) {
    try {
        const csvFile = await fs.readFile(path.join(sourceDir, 'data', 'blog_posts.csv'));
        const posts = parse(csvFile, {
            delimiter: ';',
            columns: true,
            skip_empty_lines: true
        });

        return posts.sort((a, b) => new Date(b['Date de publication']) - new Date(a['Date de publication']));
    } catch (error) {
        console.error('Erreur lors de la lecture du fichier CSV:', error);
        process.exit(1);
    }
}

async function generateBlog(posts, config, outputDir) {
    // Lire les templates
    const templatesDir = path.join(__dirname, 'src', 'templates');
    const postTemplate = Handlebars.compile(
        await fs.readFile(path.join(templatesDir, 'blog-post.html'), 'utf-8')
    );
    const indexTemplate = Handlebars.compile(
        await fs.readFile(path.join(templatesDir, 'blog.html'), 'utf-8')
    );

    // Créer le dossier blog s'il n'existe pas
    await fs.ensureDir(path.join(outputDir, 'blog'));

    // Générer les pages de blog individuelles
    for (const post of posts) {
        const recentPosts = posts
            .filter(p => p['Slug'] !== post['Slug'])
            .slice(0, 3)
            .map(p => ({
                titre: p['Titre'],
                auteur: p['auteur'],
                date_publication: formatDate(p['Date de publication']),
                photo_article: p['photo article'],
                slug: p['Slug'],
                resume: truncateText(p['Résumé de l\'article'])
            }));

        const html = postTemplate({
            ...post,
            config,
            date_publication: formatDate(post['Date de publication']),
            recent_posts: recentPosts
        });

        await fs.writeFile(
            path.join(outputDir, 'blog', `${post['Slug']}.html`),
            html
        );
    }

    // Générer la page d'index du blog
    const indexHtml = indexTemplate({
        config,
        posts: posts.map(post => ({
            titre: post['Titre'],
            resume: post['Résumé de l\'article'],
            auteur: post['auteur'],
            date_publication: formatDate(post['Date de publication']),
            duree_lecture: post['Durée de lecture'],
            photo_article: post['photo article'],
            slug: post['Slug']
        }))
    });

    await fs.writeFile(path.join(outputDir, 'blog.html'), indexHtml);
}

async function main() {
    try {
        // Charger la configuration
        const config = await loadConfig(options.config);

        // Créer le dossier de sortie
        await fs.ensureDir(options.output);

        // Copier tout le contenu de l'export Webflow
        await fs.copy(options.source, options.output, {
            filter: (src) => {
                // Exclure les fichiers blog.html et le dossier blog s'ils existent
                const relativePath = path.relative(options.source, src);
                return !relativePath.startsWith('blog') && 
                       relativePath !== 'blog.html';
            }
        });

        // Charger et générer les articles
        const posts = await loadPosts(options.source);
        await generateBlog(posts, config, options.output);

        console.log(`
Blog généré avec succès!

Les fichiers ont été générés dans: ${options.output}
- blog.html : Page d'index du blog
- blog/*.html : Pages individuelles des articles

Vous pouvez maintenant déployer le contenu sur Hostinger.
`);
    } catch (error) {
        console.error('Erreur:', error);
        process.exit(1);
    }
}

main(); 