const { execSync } = require('child_process');
const path = require('path');
const fs = require('fs');

const rootDir = path.join(__dirname, '..', '..');

function runStep(label, cmd, cwd) {
  try {
    console.log(`🔍 [Post-Hook] Running ${label}...`);
    execSync(cmd, { cwd, stdio: 'inherit', windowsHide: true });
    return true;
  } catch (err) {
    console.error(`❌ [Post-Hook Failed] ${label}`);
    return false;
  }
}

// 1. Run formatting
runStep('Code Formatter', 'node .claude/hooks/format-code.js', rootDir);

// 2. Run Backend Tests
const backendDir = path.join(rootDir, 'backend');
if (fs.existsSync(path.join(backendDir, 'tests'))) {
  const venvPython = path.join(backendDir, '.venv', 'Scripts', 'python.exe');
  const pytestCmd = fs.existsSync(venvPython)
    ? `"${venvPython}" -m pytest tests -q`
    : 'pytest tests -q';
  if (!runStep('Backend Pytest Suite', pytestCmd, backendDir)) {
    process.exit(2);
  }
}

// 3. Run Frontend & Playwright Tests
const frontendDir = path.join(rootDir, 'frontend');
if (fs.existsSync(frontendDir)) {
  const pkgPath = path.join(frontendDir, 'package.json');
  if (fs.existsSync(pkgPath)) {
    const pkg = JSON.parse(fs.readFileSync(pkgPath, 'utf-8'));
    if (pkg.scripts && pkg.scripts.test) {
      if (!runStep('Frontend Tests & QA', 'npm test -- --run', frontendDir)) {
        process.exit(2);
      }
    }
  }
}

console.log('✅ [Post-Hook] All verification checks passed.');
process.exit(0);
