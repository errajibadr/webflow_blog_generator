const path = require('path');
const { parse } = require('csv-parse/sync');
const Handlebars = require('handlebars');
const fs = require('fs-extra');
const FileManager = require('./utils/file-manager');
const { SiteConfig } = require('./config/site-config');

class BlogGenerator {
    constructor(options) {
        this.sourceDir = options.sourceDir;
        this.outputDir = options.outputDir;
        this.config = new SiteConfig(options.config);
        this.fileManager = new FileManager(this.sourceDir, this.outputDir);
    }

    async initialize() {
        // Valider la configuration
        this.config.validate();

        // Initialiser la structure des dossiers
        await this.fileManager.initialize();

        // Copier les assets du site Webflow
        await this.fileManager.copyWebflowAssets();

        // Copier les assets du blog
        await this.fileManager.copyBlogAssets();
    }

    formatDate(dateString) {
        if (!dateString) return '';
        const date = new Date(dateString);
        return date.toLocaleDateString(this.config.get('dateFormat'), {
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        });
    }

    truncateText(text, maxLength = 120) {
        if (!text) return '';
        if (text.length <= maxLength) return text;
        return text.substring(0, maxLength).trim() + '...';
    }

    async loadPosts() {
        const csvFile = await fs.readFile(path.join(this.sourceDir, 'data', 'blog_posts.csv'));
        const posts = parse(csvFile, {
            delimiter: ';',
            columns: true,
            skip_empty_lines: true
        });

        // Trier les articles par date
        return posts.sort((a, b) => new Date(b['Date de publication']) - new Date(a['Date de publication']));
    }

    async generateBlogPosts(posts) {
        const templatesDir = path.join(__dirname, 'templates');
        const postTemplateContent = await fs.readFile(path.join(templatesDir, 'blog-post.html'), 'utf-8');
        const postTemplate = Handlebars.compile(postTemplateContent);

        for (const post of posts) {
            // Obtenir les articles récents (excluant l'article courant)
            const recentPosts = posts
                .filter(p => p['Slug'] !== post['Slug'])
                .slice(0, 3)
                .map(p => ({
                    titre: p['Titre'],
                    auteur: p['auteur'],
                    date_publication: this.formatDate(p['Date de publication']),
                    photo_article: p['photo article'],
                    slug: p['Slug'],
                    resume: this.truncateText(p['Résumé de l\'article'], 120)
                }));

            // Préparer les données pour le template
            const templateData = {
                ...post,
                config: this.config.getAll(),
                date_publication: this.formatDate(post['Date de publication']),
                recent_posts: recentPosts
            };

            // Générer le HTML
            const html = postTemplate(templateData);

            // Écrire le fichier
            const fileName = `${post['Slug']}.html`;
            await fs.writeFile(path.join(this.outputDir, 'blog', fileName), html);
        }
    }

    async generateBlogIndex(posts) {
        const templatesDir = path.join(__dirname, 'templates');
        const indexTemplateContent = await fs.readFile(path.join(templatesDir, 'blog.html'), 'utf-8');
        const indexTemplate = Handlebars.compile(indexTemplateContent);

        const indexData = {
            config: this.config.getAll(),
            posts: posts.map(post => ({
                titre: post['Titre'],
                resume: post['Résumé de l\'article'],
                auteur: post['auteur'],
                date_publication: this.formatDate(post['Date de publication']),
                duree_lecture: post['Durée de lecture'],
                photo_article: post['photo article'],
                slug: post['Slug']
            }))
        };

        const indexHtml = indexTemplate(indexData);
        await fs.writeFile(path.join(this.outputDir, 'blog.html'), indexHtml);
    }

    async generate() {
        try {
            // Initialiser
            await this.initialize();

            // Charger les articles
            const posts = await this.loadPosts();

            // Générer les pages de blog
            await this.generateBlogPosts(posts);

            // Générer l'index du blog
            await this.generateBlogIndex(posts);

            // Nettoyage final
            await this.fileManager.cleanup();

            console.log('Blog généré avec succès!');
            return true;
        } catch (error) {
            console.error('Erreur lors de la génération du blog:', error);
            throw error;
        }
    }
}

module.exports = BlogGenerator; 