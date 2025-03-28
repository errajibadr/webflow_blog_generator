const fs = require('fs-extra');
const path = require('path');
const glob = require('glob');

class FileManager {
    constructor(sourceDir, outputDir) {
        this.sourceDir = sourceDir;
        this.outputDir = outputDir;
    }

    async initialize() {
        // Créer les répertoires nécessaires
        await fs.ensureDir(this.outputDir);
        await fs.ensureDir(path.join(this.outputDir, 'blog'));
        await fs.ensureDir(path.join(this.outputDir, 'assets'));
        await fs.ensureDir(path.join(this.outputDir, 'css'));
        await fs.ensureDir(path.join(this.outputDir, 'js'));
    }

    async copyWebflowAssets() {
        // Copier les assets du site Webflow
        const assetDirs = ['css', 'js', 'images', 'fonts', 'documents'];
        
        for (const dir of assetDirs) {
            const sourcePath = path.join(this.sourceDir, dir);
            const destPath = path.join(this.outputDir, dir);
            
            if (await fs.pathExists(sourcePath)) {
                await fs.copy(sourcePath, destPath);
            }
        }
    }

    async copyBlogAssets() {
        // Copier les assets spécifiques au blog
        const blogCss = path.join(__dirname, '../assets/css/blog-style.css');
        const destCss = path.join(this.outputDir, 'css/blog-style.css');
        
        await fs.copy(blogCss, destCss);
    }

    async copyTemplates(templatesDir) {
        // Copier les templates dans le répertoire de sortie
        const templates = glob.sync('*.html', { cwd: templatesDir });
        
        for (const template of templates) {
            const sourcePath = path.join(templatesDir, template);
            const destPath = path.join(this.outputDir, 'templates', template);
            await fs.copy(sourcePath, destPath);
        }
    }

    async injectStyles(htmlFile, styles) {
        let content = await fs.readFile(htmlFile, 'utf-8');
        const styleTag = `<style>${styles}</style>`;
        
        // Injecter avant la fermeture de head
        content = content.replace('</head>', `${styleTag}\n</head>`);
        
        await fs.writeFile(htmlFile, content);
    }

    async injectScripts(htmlFile, scripts) {
        let content = await fs.readFile(htmlFile, 'utf-8');
        const scriptTags = scripts.map(script => 
            `<script src="${script}"></script>`
        ).join('\n');
        
        // Injecter avant la fermeture de body
        content = content.replace('</body>', `${scriptTags}\n</body>`);
        
        await fs.writeFile(htmlFile, content);
    }

    async cleanup() {
        // Nettoyer les fichiers temporaires si nécessaire
        const tempDirs = ['templates'];
        
        for (const dir of tempDirs) {
            const tempPath = path.join(this.outputDir, dir);
            if (await fs.pathExists(tempPath)) {
                await fs.remove(tempPath);
            }
        }
    }
}

module.exports = FileManager; 