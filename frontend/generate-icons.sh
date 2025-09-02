#!/bin/bash

# Script to generate all required icon sizes from chesscrew-1024x1024.png
# Requires ImageMagick to be installed

set -e  # Exit on any error

echo "🎨 Generating icons for ChessCrew..."

# Check if ImageMagick is installed
if ! command -v convert &> /dev/null; then
    echo "❌ ImageMagick is not installed. Please install it first:"
    echo "   Ubuntu/Debian: sudo apt-get install imagemagick"
    echo "   macOS: brew install imagemagick"
    echo "   Arch: sudo pacman -S imagemagick"
    exit 1
fi

# Check if source image exists
SOURCE_IMAGE="public/chesscrew-1024x1024.png"
if [ ! -f "$SOURCE_IMAGE" ]; then
    echo "❌ Source image not found: $SOURCE_IMAGE"
    echo "Please make sure chesscrew-1024x1024.png is in the public/ directory"
    exit 1
fi

echo "📁 Source image: $SOURCE_IMAGE"
echo ""

# Create output directory if it doesn't exist
mkdir -p public

# Generate logo192.png (192x192)
echo "🖼️  Generating logo192.png..."
convert "$SOURCE_IMAGE" -resize 192x192 public/logo192.png
echo "✅ Created public/logo192.png"

# Generate logo512.png (512x512)  
echo "🖼️  Generating logo512.png..."
convert "$SOURCE_IMAGE" -resize 512x512 public/logo512.png
echo "✅ Created public/logo512.png"

# Generate favicon.ico with multiple sizes
echo "🖼️  Generating favicon.ico with multiple sizes..."
# Create temporary files for each size
convert "$SOURCE_IMAGE" -resize 16x16 /tmp/favicon-16.png
convert "$SOURCE_IMAGE" -resize 24x24 /tmp/favicon-24.png
convert "$SOURCE_IMAGE" -resize 32x32 /tmp/favicon-32.png
convert "$SOURCE_IMAGE" -resize 64x64 /tmp/favicon-64.png

# Combine all sizes into a single ICO file
convert /tmp/favicon-16.png /tmp/favicon-24.png /tmp/favicon-32.png /tmp/favicon-64.png public/favicon.ico

# Clean up temporary files
rm -f /tmp/favicon-*.png

echo "✅ Created public/favicon.ico (16x16, 24x24, 32x32, 64x64)"

# Generate additional common sizes that might be useful
echo ""
echo "🖼️  Generating additional useful sizes..."

# Apple touch icon (180x180)
convert "$SOURCE_IMAGE" -resize 180x180 public/apple-touch-icon.png
echo "✅ Created public/apple-touch-icon.png (180x180)"

# PWA icons (common sizes)
convert "$SOURCE_IMAGE" -resize 144x144 public/icon-144x144.png
echo "✅ Created public/icon-144x144.png"

convert "$SOURCE_IMAGE" -resize 256x256 public/icon-256x256.png
echo "✅ Created public/icon-256x256.png"

convert "$SOURCE_IMAGE" -resize 384x384 public/icon-384x384.png
echo "✅ Created public/icon-384x384.png"

echo ""
echo "🎉 All icons generated successfully!"
echo ""
echo "Generated files:"
echo "  • favicon.ico (16x16, 24x24, 32x32, 64x64)"
echo "  • logo192.png (192x192)"
echo "  • logo512.png (512x512)"
echo "  • apple-touch-icon.png (180x180)"
echo "  • icon-144x144.png (144x144)"
echo "  • icon-256x256.png (256x256)"
echo "  • icon-384x384.png (384x384)"
echo ""
echo "💡 Consider updating your manifest.json to include the additional sizes!"
