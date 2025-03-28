// Fonction pour charger et afficher les articles du blog
async function loadBlogPosts() {
    try {
        const response = await fetch('/data/blog_posts.csv');
        const csvText = await response.text();
        
        // Utiliser ; comme séparateur et gérer les guillemets
        const rows = csvText.split('\n').filter(row => row.trim());
        const headers = rows[0].split(';').map(header => header.trim().replace(/^"|"$/g, ''));
        
        const posts = rows.slice(1).map(row => {
            const values = row.split(';').map(value => value.trim().replace(/^"|"$/g, ''));
            const post = {};
            headers.forEach((header, index) => {
                post[header] = values[index] || '';
            });
            return post;
        });

        const blogContainer = document.querySelector('.blog-list');
        if (!blogContainer) return;

        blogContainer.innerHTML = posts.map(post => `
            <article class="blog-post-preview">
                <h2 class="preview-title">
                    <a href="/blog/${post.Slug}">${post.Titre}</a>
                </h2>
                <div class="post-meta">
                    <span class="author-name">${post.auteur}</span>
                    <span class="post-date">${new Date(post["Date de publication"]).toLocaleDateString('fr-FR')}</span>
                    <span class="read-time">${post["Durée de lecture"]} de lecture</span>
                </div>
                ${post["photo article"] ? `
                    <img src="${post["photo article"]}" alt="${post.Titre}" class="preview-image" loading="lazy">
                ` : ''}
                <p class="preview-excerpt">${post["Résumé de l'article"]}</p>
                <a href="/blog/${post.Slug}" class="read-more">Lire la suite →</a>
            </article>
        `).join('');

    } catch (error) {
        console.error('Erreur lors du chargement des articles:', error);
    }
}

// Charger les articles au chargement de la page
document.addEventListener('DOMContentLoaded', loadBlogPosts);

// Function to render blog posts
function renderBlogPosts(posts) {
    const container = document.querySelector('.w-dyn-items');
    if (!container) {
        console.error('Blog posts container not found');
        return;
    }

    // Clear the container
    container.innerHTML = '';

    // Sort posts by date (most recent first)
    posts.sort((a, b) => new Date(b['Date de publication']) - new Date(a['Date de publication']));

    posts.forEach(post => {
        const postElement = createPostElement(post);
        container.appendChild(postElement);
    });

    // Hide the "No items found" message if we have posts
    const emptyMessage = document.querySelector('.w-dyn-empty');
    if (emptyMessage) {
        emptyMessage.style.display = posts.length > 0 ? 'none' : 'block';
    }
}

// Function to create a blog post element
function createPostElement(post) {
    const template = document.createElement('div');
    template.className = 'w-dyn-item';
    
    template.innerHTML = `
        <article class="blog-post">
            <div class="post-image-wrapper">
                ${post['photo article'] ? `<img src="${post['photo article']}" alt="${post.Titre}" class="post-image"/>` : ''}
            </div>
            <div class="post-content-wrapper">
                <h2 class="post-title">${post.Titre || 'Sans titre'}</h2>
                <div class="post-meta">
                    ${post.auteur ? `<span class="author">Par ${post.auteur}</span>` : ''}
                    ${post['Durée de lecture'] ? `<span class="reading-time">${post['Durée de lecture']} min de lecture</span>` : ''}
                    ${post['Date de publication'] ? `<span class="publication-date">${formatDate(post['Date de publication'])}</span>` : ''}
                </div>
                ${post['Résumé de l\'article'] ? `<p class="post-summary">${post['Résumé de l\'article']}</p>` : ''}
                <a href="/blog/${post.Slug}" class="read-more-link">Lire l'article</a>
            </div>
        </article>
    `;
    
    return template;
}

// Helper function to format dates
function formatDate(dateString) {
    if (!dateString) return '';
    const date = new Date(dateString);
    return date.toLocaleDateString('fr-FR', {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
    });
} 