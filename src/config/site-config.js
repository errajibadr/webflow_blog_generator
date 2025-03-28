const defaultConfig = {
    blogTitle: 'Blog',
    blogDescription: 'Articles et actualités',
    postsPerPage: 10,
    dateFormat: 'fr-FR',
    socialLinks: {
        twitter: '',
        facebook: '',
        linkedin: '',
        instagram: ''
    },
    author: {
        name: '',
        bio: '',
        avatar: ''
    },
    seo: {
        defaultTitle: '',
        defaultDescription: '',
        siteName: '',
        language: 'fr'
    }
};

class SiteConfig {
    constructor(userConfig = {}) {
        this.config = { ...defaultConfig, ...userConfig };
    }

    get(key) {
        return key.split('.').reduce((obj, k) => obj && obj[k], this.config);
    }

    set(key, value) {
        const keys = key.split('.');
        const lastKey = keys.pop();
        const target = keys.reduce((obj, k) => {
            if (!(k in obj)) obj[k] = {};
            return obj[k];
        }, this.config);
        target[lastKey] = value;
    }

    getAll() {
        return this.config;
    }

    validate() {
        const required = ['blogTitle', 'seo.siteName'];
        const missing = required.filter(key => !this.get(key));
        
        if (missing.length > 0) {
            throw new Error(`Missing required configuration: ${missing.join(', ')}`);
        }
        
        return true;
    }
}

module.exports = {
    SiteConfig,
    defaultConfig
}; 