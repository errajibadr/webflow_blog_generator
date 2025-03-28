# Générateur de Blog pour Webflow

Ce générateur permet d'ajouter facilement un blog à votre site Webflow en générant les pages nécessaires à partir d'un fichier CSV.

## Prérequis

- Node.js 14 ou supérieur
- Un export de site Webflow
- Un fichier CSV contenant les articles de blog

## Installation

1. Clonez ce dépôt
2. Installez les dépendances :
```bash
npm install
```

## Structure des fichiers

```
src/
├── data/
│   └── blog_posts.csv     # Articles de blog au format CSV
├── templates/
│   ├── blog.html         # Template de la page d'index du blog
│   └── blog-post.html    # Template des pages d'articles
└── blog-config.json      # Configuration du blog
```

## Format du fichier CSV

Le fichier `blog_posts.csv` doit contenir les colonnes suivantes (séparées par des points-virgules) :

- Titre : Titre de l'article
- Slug : URL de l'article (sans espaces ni caractères spéciaux)
- Résumé de l'article : Court résumé
- Contenu : Contenu HTML de l'article
- Date de publication : Format YYYY-MM-DD
- auteur : Nom de l'auteur
- Durée de lecture : Temps de lecture estimé
- photo article : Chemin de l'image principale
- meta title : Titre SEO
- meta description : Description SEO

## Configuration

Créez un fichier `blog-config.json` basé sur l'exemple fourni (`blog-config.example.json`) :

```json
{
    "site": {
        "title": "Mon Blog",
        "description": "Description de mon blog",
        "logo": "/images/logo.png",
        "favicon": "/images/favicon.ico"
    },
    "social": {
        "facebook": "https://facebook.com/monblog",
        "twitter": "https://twitter.com/monblog",
        "linkedin": "https://linkedin.com/company/monblog"
    },
    "contact": {
        "email": "contact@monblog.com",
        "phone": "+33 1 23 45 67 89"
    },
    "seo": {
        "defaultTitle": "Mon Blog - Articles et actualités",
        "defaultDescription": "Découvrez nos articles sur [votre thématique]",
        "defaultImage": "/images/default-share.jpg",
        "googleAnalyticsId": "UA-XXXXXXXX-X"
    }
}
```

## Utilisation

1. Exportez votre site Webflow
2. Préparez votre fichier CSV avec vos articles
3. Configurez votre blog dans `blog-config.json`
4. Générez le blog :

```bash
node generate.js -s chemin/vers/export/webflow -c blog-config.json -o dossier/sortie
```

Options :
- `-s, --source` : Dossier contenant l'export Webflow (requis)
- `-c, --config` : Fichier de configuration du blog (requis)
- `-o, --output` : Dossier de sortie (par défaut: "dist")

## Résultat

Le générateur va :
1. Copier l'intégralité de l'export Webflow dans le dossier de sortie
2. Générer une page `blog.html` à la racine
3. Créer un dossier `blog/` contenant les pages individuelles des articles

Vous pouvez ensuite déployer le contenu du dossier de sortie sur Hostinger.

## Structure Générée

```
dist/
├── blog/           # Pages de blog individuelles
├── css/           # Fichiers CSS
├── js/            # Fichiers JavaScript
├── images/        # Images
├── fonts/         # Polices
└── blog.html      # Page d'index du blog
```

## Déploiement sur Hostinger

1. Compressez le contenu du dossier `dist`
2. Uploadez le fichier ZIP sur Hostinger
3. Extrayez les fichiers dans le répertoire souhaité

## Personnalisation

### Templates

Les templates se trouvent dans `src/templates/` :
- `blog.html` : Template de la page d'index
- `blog-post.html` : Template des articles

### Styles

Les styles spécifiques au blog se trouvent dans `src/assets/css/blog-style.css`

## Dépannage

### Problèmes courants

1. **Les images ne s'affichent pas**
   - Vérifiez que les chemins sont relatifs
   - Vérifiez que les images sont bien copiées dans le dossier de sortie

2. **Erreurs de génération**
   - Vérifiez le format du CSV
   - Vérifiez que tous les fichiers requis sont présents

## Contribution

Les contributions sont les bienvenues ! N'hésitez pas à :
1. Fork le projet
2. Créer une branche pour votre fonctionnalité
3. Commiter vos changements
4. Pousser vers la branche
5. Créer une Pull Request

## Licence

ISC 