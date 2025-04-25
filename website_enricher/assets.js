const fs = require('fs-extra');
const path = require('path');
const CleanCSS = require('clean-css');
const Terser = require('terser');

/**
 * Minify CSS content.
 * @param {string} cssContent
 * @returns {Promise<string>}
 */
async function minifyCSS(cssContent) {
  const cleanCSS = new CleanCSS({
    compatibility: '*',
    level: 2,
    sourceMap: false
  });
  const output = cleanCSS.minify(cssContent);
  if (output.errors.length > 0) {
    console.error('CSS minification errors:', output.errors);
    return cssContent;
  }
  return output.styles;
}

/**
 * Minify JS content.
 * @param {string} jsContent
 * @returns {Promise<string>}
 */
async function minifyJS(jsContent) {
  try {
    const result = await Terser.minify(jsContent, {
      compress: true,
      mangle: true
    });
    return result.code;
  } catch (error) {
    console.error('JS minification error:', error);
    return jsContent;
  }
}

/**
 * Minify a file in place (CSS or JS).
 * @param {string} filePath
 * @param {'css'|'js'} type
 */
async function minifyFile(filePath, type) {
  try {
    const content = await fs.readFile(filePath, 'utf-8');
    let minified;
    if (type === 'css') {
      minified = await minifyCSS(content);
    } else if (type === 'js') {
      minified = await minifyJS(content);
    }
    await fs.writeFile(filePath, minified);
    const savings = ((content.length - minified.length) / content.length * 100).toFixed(2);
    console.log(`Minified ${path.basename(filePath)} - Reduced by ${savings}%`);
  } catch (error) {
    console.error(`Error minifying ${filePath}:`, error);
  }
}

/**
 * Copy and minify all assets (CSS, JS, images, social icons, author photo, blog background, theme CSS).
 * @param {string} outputDir
 * @param {object} config
 */
async function copyAssets(outputDir, config) {
  // Create assets directory structure
  await fs.ensureDir(path.join(outputDir, 'css'));
  await fs.ensureDir(path.join(outputDir, 'assets', 'js'));
  await fs.ensureDir(path.join(outputDir, 'assets', 'images', 'social'));
  await fs.ensureDir(path.join(outputDir, 'images'));
  await fs.ensureDir(path.join(outputDir, 'js'));

  // Minify Webflow exported CSS files
  console.log('\nProcessing Webflow exported CSS files...');
  const cssDir = path.join(outputDir, 'css');
  const cssFiles = await fs.readdir(cssDir);
  const staticCssFiles = [
    'normalize.css',
    'webflow.css',
    'blog-index.css',
    'social-icons.css',
    'blog-style.css'
  ];
  for (const cssFile of cssFiles) {
    if (cssFile.endsWith('.css')) {
      const isWebflowGenerated = cssFile.match(/.*\.webflow\.css$/);
      if (isWebflowGenerated || staticCssFiles.includes(cssFile)) {
        const cssPath = path.join(cssDir, cssFile);
        console.log(`Processing CSS file: ${cssFile}`);
        await minifyFile(cssPath, 'css');
      }
    }
  }

  // Copy and minify all CSS files from src/assets/css
  const cssSourceDir = path.join(__dirname, 'src', 'assets', 'css');
  const cssDestDir = path.join(outputDir, 'css');
  try {
    const cssFiles = await fs.readdir(cssSourceDir);
    for (const file of cssFiles) {
      if (file.endsWith('.css')) {
        const destPath = path.join(cssDestDir, file);
        await fs.copy(path.join(cssSourceDir, file), destPath);
        console.log(`Copied CSS file: ${file}`);
        await minifyFile(destPath, 'css');
      }
    }
  } catch (error) {
    console.error('Error processing CSS files:', error);
  }

  // Copy and minify JS files
  const jsSource = path.join(__dirname, 'src', 'assets', 'js');
  const jsDest = path.join(outputDir, 'js');
  try {
    const jsFiles = await fs.readdir(jsSource);
    for (const file of jsFiles) {
      if (file.endsWith('.js')) {
        const destPath = path.join(jsDest, file);
        await fs.copy(path.join(jsSource, file), destPath);
        console.log(`Copied JS file: ${file}`);
        await minifyFile(destPath, 'js');
      }
    }
  } catch (error) {
    console.error('Error processing JS files:', error);
  }

  // Copy social icons
  const socialIconsSource = path.join(__dirname, 'src', 'assets', 'images', 'social');
  const socialIconsDest = path.join(outputDir, 'assets', 'images', 'social');
  await fs.copy(socialIconsSource, socialIconsDest);

  // Copy default author image if it exists in config
  if (config.site.author.photo) {
    const authorPhotoSource = path.join(__dirname, config.site.author.photo);
    const authorPhotoFilename = path.basename(config.site.author.photo);
    const authorPhotoDest = path.join(outputDir, 'images', authorPhotoFilename);
    try {
      await fs.copy(authorPhotoSource, authorPhotoDest);
      console.log('Copied default author photo:', authorPhotoFilename);
      config.site.author.photo = `/images/${authorPhotoFilename}`;
    } catch (error) {
      console.error('Error copying default author photo:', error);
    }
  }

  // Ensure config.blog exists
  if (!config.blog) {
    config.blog = {};
  }

  // Set default value for blogIndexBackground if not specified
  if (!config.blog.blogIndexBackground) {
    config.blog.blogIndexBackground = 'src/assets/images/background/waterfall.jpg';
    console.log('Using default blog index background image: src/assets/images/background/waterfall.jpg');
  }

  // Copy blog index background image
  let blogIndexBackgroundPath = '';
  const blogIndexBackgroundSource = path.join(__dirname, config.blog.blogIndexBackground);
  const blogIndexBackgroundFilename = path.basename(config.blog.blogIndexBackground);
  const blogIndexBackgroundDest = path.join(outputDir, 'images', blogIndexBackgroundFilename);
  try {
    if (fs.existsSync(blogIndexBackgroundSource)) {
      await fs.copy(blogIndexBackgroundSource, blogIndexBackgroundDest);
      console.log('Copied blog index background image:', blogIndexBackgroundFilename);
      blogIndexBackgroundPath = `/images/${blogIndexBackgroundFilename}`;
      config.blog.blogIndexBackground = blogIndexBackgroundPath;
    } else {
      console.error(`Blog index background image not found at: ${blogIndexBackgroundSource}`);
    }
  } catch (error) {
    console.error('Error copying blog index background image:', error);
  }

  // Generate dynamic CSS with theme colors
  const dynamicCss = `
    :root {
      --primary-color: ${config.ui.primaryColor};
      --header-background: ${config.ui.headerBackground};
      --text-color: ${config.ui.textColor};
      --link-color: ${config.ui.linkColor};
      --background-color: ${config.ui.backgroundColor};
    }
    ${blogIndexBackgroundPath ? `.main-column.header {\n  background-image: url('${blogIndexBackgroundPath}');\n}` : ''}
  `;
  const minifiedDynamicCss = await minifyCSS(dynamicCss);
  await fs.writeFile(path.join(outputDir, 'css', 'theme.css'), minifiedDynamicCss);
}

module.exports = {
  minifyCSS,
  minifyJS,
  minifyFile,
  copyAssets
}; 