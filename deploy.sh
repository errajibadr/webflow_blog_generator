#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
DIST_DIR="dist"
TEMP_DIR="temp_deploy"
CONFIG_FILE="config/config.json"

# Print with color
print_status() {
    echo -e "${2}$1${NC}"
}

# Check if required directories exist
check_requirements() {
    print_status "Checking requirements..." "${YELLOW}"
    
    if [ ! -d "$DIST_DIR" ]; then
        print_status "Error: $DIST_DIR directory not found!" "${RED}"
        exit 1
    fi
    
    if [ ! -f "$CONFIG_FILE" ]; then
        print_status "Error: $CONFIG_FILE not found!" "${RED}"
        exit 1
    fi
}

# Create temporary directory for deployment
create_temp_dir() {
    print_status "Creating temporary directory..." "${YELLOW}"
    rm -rf "$TEMP_DIR"
    mkdir -p "$TEMP_DIR"
}

# Optimize and copy assets
process_assets() {
    print_status "Processing assets..." "${YELLOW}"
    
    # Create required directories
    mkdir -p "$TEMP_DIR/assets"
    mkdir -p "$TEMP_DIR/css"
    mkdir -p "$TEMP_DIR/js"
    mkdir -p "$TEMP_DIR/fonts"
    
    # Copy and optimize images
    if [ -d "$DIST_DIR/assets" ]; then
        cp -r "$DIST_DIR/assets"/* "$TEMP_DIR/assets/"
        print_status "Assets copied successfully" "${GREEN}"
    fi
    
    # Copy CSS files
    if [ -d "$DIST_DIR/css" ]; then
        cp -r "$DIST_DIR/css"/* "$TEMP_DIR/css/"
        print_status "CSS files copied successfully" "${GREEN}"
    fi
    
    # Copy JavaScript files
    if [ -d "$DIST_DIR/js" ]; then
        cp -r "$DIST_DIR/js"/* "$TEMP_DIR/js/"
        print_status "JavaScript files copied successfully" "${GREEN}"
    fi
    
    # Copy fonts
    if [ -d "$DIST_DIR/fonts" ]; then
        cp -r "$DIST_DIR/fonts"/* "$TEMP_DIR/fonts/"
        print_status "Fonts copied successfully" "${GREEN}"
    fi
}

# Copy HTML files and ensure proper linking
process_html() {
    print_status "Processing HTML files..." "${YELLOW}"
    
    # Copy all HTML files
    find "$DIST_DIR" -name "*.html" -exec cp {} "$TEMP_DIR/" \;
    print_status "HTML files copied successfully" "${GREEN}"
}

# Create deployment package
create_package() {
    print_status "Creating deployment package..." "${YELLOW}"
    
    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    PACKAGE_NAME="deploy_$TIMESTAMP.zip"
    
    cd "$TEMP_DIR" || exit
    zip -r "../$PACKAGE_NAME" ./*
    cd ..
    
    print_status "Deployment package created: $PACKAGE_NAME" "${GREEN}"
}

# Cleanup temporary files
cleanup() {
    print_status "Cleaning up..." "${YELLOW}"
    rm -rf "$TEMP_DIR"
    print_status "Cleanup completed" "${GREEN}"
}

# Main deployment process
main() {
    print_status "Starting deployment process..." "${YELLOW}"
    
    check_requirements
    create_temp_dir
    process_assets
    process_html
    create_package
    cleanup
    
    print_status "Deployment process completed successfully!" "${GREEN}"
    print_status "You can now upload the deployment package to Hostinger" "${GREEN}"
}

# Run the deployment process
main 