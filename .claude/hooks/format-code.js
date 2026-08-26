const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

function runCommand(command, cwd) {
  try {
    execSync(command, { cwd, stdio: 'ignore', windowsHide: true });
  } catch (err) {
    // Silently continue if formatter tool is not yet installed or fails
  }
}

const rootDir = path.join(__dirname, '..', '..');

// 1. Format Frontend (Prettier)
const frontendDir = path.join(rootDir, 'frontend');
if (fs.existsSync(frontendDir)) {
  runCommand('npx prettier --write "src/**/*.{js,jsx,json,css}"', frontendDir);
}

// 2. Format Backend (Ruff or Black)
const backendDir = path.join(rootDir, 'backend');
if (fs.existsSync(backendDir)) {
  runCommand('ruff format .', backendDir);
  runCommand('black .', backendDir);
}

process.exit(0);