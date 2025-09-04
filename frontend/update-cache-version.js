#!/usr/bin/env node

const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const { execSync } = require('child_process');

const swPath = path.join(__dirname, 'public', 'sw.js');

try {
  let swContent = fs.readFileSync(swPath, 'utf8');

  // Try to get git commit hash first
  let newVersion;
  try {
    // Try from current directory first
    newVersion = execSync('git describe --always', { encoding: 'utf8' }).trim();
    console.log('📋 Using git describe for cache version');
  } catch (gitError) {
    try {
      // Check if we're in a container environment with workspace
      const fs = require('fs');
      if (fs.existsSync('/workspace')) {
        // Configure git to allow access to the workspace directory
        try {
          execSync('git config --global --add safe.directory /workspace', { stdio: 'pipe' });
        } catch (configError) {
          console.log('⚠️  Could not configure git safe directory, continuing...');
        }
        // Try from workspace directory (parent directory)
        newVersion = execSync('cd /workspace && git describe --always', { encoding: 'utf8' }).trim();
        console.log('📋 Using git describe from workspace for cache version');
      } else {
        throw new Error('Not in container environment');
      }
    } catch (workspaceError) {
      // Fallback: Use hash of key source files
      console.log('⚠️  Git not available, using file hash for cache version');
      try {
        const srcPath = path.join(__dirname, 'src');
        const files = getAllFiles(srcPath);
        const fileContents = files.map(file => fs.readFileSync(file, 'utf8')).join('');
        newVersion = crypto.createHash('md5').update(fileContents).digest('hex').substring(0, 8);
      } catch (fileError) {
        // Final fallback: Use timestamp
        console.log('⚠️  File hashing failed, using timestamp');
        newVersion = 'v' + Date.now();
      }
    }
  }

  // Check if version has actually changed
  const currentVersionMatch = swContent.match(/const CACHE_VERSION = '([^']+)';/);
  const currentVersion = currentVersionMatch ? currentVersionMatch[1] : null;

  // Create version with build timestamp
  const buildTime = new Date().toISOString();
  const versionWithTime = `${newVersion} (${buildTime})`;

  if (currentVersion === versionWithTime) {
    console.log(`ℹ️  Cache version is already up to date: ${versionWithTime}`);
    return;
  }

  // Replace the cache version
  swContent = swContent.replace(
    /const CACHE_VERSION = '[^']+';/,
    `const CACHE_VERSION = '${versionWithTime}';`
  );

  // Write back to file
  fs.writeFileSync(swPath, swContent, 'utf8');

  console.log(`✅ Updated cache version to: ${versionWithTime}`);

} catch (error) {
  console.error('❌ Failed to update cache version:', error.message);
  process.exit(1);
}

function getAllFiles(dirPath, arrayOfFiles = []) {
  const files = fs.readdirSync(dirPath);

  files.forEach(file => {
    const fullPath = path.join(dirPath, file);
    if (fs.statSync(fullPath).isDirectory()) {
      arrayOfFiles = getAllFiles(fullPath, arrayOfFiles);
    } else if (file.endsWith('.js') || file.endsWith('.jsx') || file.endsWith('.ts') || file.endsWith('.tsx')) {
      arrayOfFiles.push(fullPath);
    }
  });

  return arrayOfFiles;
}