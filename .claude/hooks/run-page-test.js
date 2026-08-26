const { execSync } = require('child_process');
const path = require('path');
const fs = require('fs');

const rootDir = path.join(__dirname, '..', '..');

function runTest(cmd, cwd) {
  try {
    execSync(cmd, { cwd, stdio: 'inherit' });
    return true;
  } catch (err) {
    return false;
  }
}

// 1. Run Frontend Tests if test script is present
const frontendPkgPath = path.join(rootDir, 'frontend', 'package.json');
if (fs.existsSync(frontendPkgPath)) {
  const pkg = JSON.parse(fs.readFileSync(frontendPkgPath, 'utf-8'));
  if (pkg.scripts && pkg.scripts.test) {
    const success = runTest('npm test -- --run', path.join(rootDir, 'frontend'));
    if (!success) {
      console.error('❌ Frontend test suite failed.');
      process.exit(2);
    }
  }
}

// 2. Run Backend Pytest Suite if tests folder exists
const backendTestsDir = path.join(rootDir, 'backend', 'tests');
if (fs.existsSync(backendTestsDir)) {
  const success = runTest('pytest tests -q', path.join(rootDir, 'backend'));
  if (!success) {
    console.error('❌ Backend pytest suite failed.');
    process.exit(2);
  }
}

process.exit(0);