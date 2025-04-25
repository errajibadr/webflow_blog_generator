const fs = require('fs-extra');
const path = require('path');

let defaultArticleImages = [];
let currentImageIndex = 0;

function getNextDefaultImage() {
  if (defaultArticleImages.length === 0) {
    return null;
  }
  const image = defaultArticleImages[currentImageIndex];
  currentImageIndex = (currentImageIndex + 1) % defaultArticleImages.length;
  return image;
}

async function copyDogPictures(outputDir) {
  const dogPicturesDir = path.join(__dirname, 'src', 'assets', 'images', 'dog_articles');
  const imagesOutputDir = path.join(outputDir, 'images');
  try {
    await fs.ensureDir(imagesOutputDir);
    const files = await fs.readdir(dogPicturesDir);
    const imageFiles = files.filter(file =>
      file.toLowerCase().endsWith('.jpg') ||
      file.toLowerCase().endsWith('.jpeg') ||
      file.toLowerCase().endsWith('.png') ||
      file.toLowerCase().endsWith('.webp')
    );
    defaultArticleImages = [];
    currentImageIndex = 0;
    for (const file of imageFiles) {
      const sourcePath = path.join(dogPicturesDir, file);
      const destPath = path.join(imagesOutputDir, file);
      await fs.copy(sourcePath, destPath);
      defaultArticleImages.push(`/images/${file}`);
    }
    defaultArticleImages = defaultArticleImages.sort(() => Math.random() - 0.5);
  } catch (error) {
    console.error('Error copying default article images:', error);
  }
}

function isValidImageUrl(url, outputDir, csvDir) {
  if (!url) return false;
  if (url.startsWith('http://') || url.startsWith('https://')) {
    return true;
  }
  if (url.startsWith('/images/')) {
    const imagePath = path.join(outputDir, url);
    return fs.existsSync(imagePath);
  }
  try {
    const possiblePaths = [
      url,
      path.join(process.cwd(), url),
      path.join(__dirname, url),
      path.join(__dirname, 'data', url),
      path.join(csvDir, url),
      path.join(csvDir, 'images', path.basename(url))
    ];
    for (const sourcePath of possiblePaths) {
      if (fs.existsSync(sourcePath)) {
        const filename = path.basename(sourcePath);
        const destPath = path.join(outputDir, 'images', filename);
        fs.ensureDirSync(path.join(outputDir, 'images'));
        fs.copySync(sourcePath, destPath);
        return true;
      }
    }
  } catch (error) {
    console.error(`Error processing relative image path ${url}:`, error);
  }
  return false;
}

function getDefaultArticleImages() {
  return defaultArticleImages;
}

module.exports = {
  copyDogPictures,
  getNextDefaultImage,
  isValidImageUrl,
  getDefaultArticleImages
}; 