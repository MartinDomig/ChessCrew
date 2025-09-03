#!/usr/bin/env node

const fs = require('fs');
const path = require('path');

const swPath = path.join(__dirname, 'public', 'sw.js');

try {
  let swContent = fs.readFileSync(swPath, 'utf8');
  
  // Generate new cache version with timestamp
  const newVersion = 'v' + Date.now();
  
  // Replace the dynamic cache version with a static one
  swContent = swContent.replace(
    /const CACHE_VERSION = 'v' \+ Date\.now\(\);.*$/m,
    `const CACHE_VERSION = '${newVersion}';`
  );
  
  // Write back to file
  fs.writeFileSync(swPath, swContent, 'utf8');
  
  console.log(`✅ Updated cache version to: ${newVersion}`);
  
} catch (error) {
  console.error('❌ Failed to update cache version:', error.message);
  process.exit(1);
}
