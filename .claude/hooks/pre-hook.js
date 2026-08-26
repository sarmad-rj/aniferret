const fs = require('fs');
const path = require('path');

console.log('⚡ [Pre-Hook] Checking MCP server status & architectural rules...');

// 1. Check MCP configuration existence
const mcpConfig = path.join(__dirname, '..', 'mcp.json');
if (!fs.existsSync(mcpConfig)) {
  console.warn('⚠️ [Pre-Hook Warning] .claude/mcp.json not found.');
}

// 2. Ensure SPEC.md exists before implementing features
const specPath = path.join(__dirname, '..', '..', 'SPEC.md');
if (!fs.existsSync(specPath)) {
  console.warn('⚠️ [Pre-Hook Warning] SPEC.md is missing. Generate product spec first.');
}

process.exit(0);
