#!/usr/bin/env node
import fs from 'node:fs/promises';
import path from 'node:path';

function log(message) {
  process.stdout.write(`[vite-shim] ${message}\n`);
}

async function pathExists(target) {
  try {
    await fs.stat(target);
    return true;
  } catch {
    return false;
  }
}

async function copyDir(from, to) {
  await fs.mkdir(to, { recursive: true });
  const entries = await fs.readdir(from, { withFileTypes: true });
  for (const entry of entries) {
    const sourcePath = path.join(from, entry.name);
    const targetPath = path.join(to, entry.name);
    if (entry.isDirectory()) {
      await copyDir(sourcePath, targetPath);
    } else if (entry.isFile()) {
      await fs.copyFile(sourcePath, targetPath);
    }
  }
}

async function build() {
  const projectRoot = process.cwd();
  const distDir = path.join(projectRoot, 'dist');
  await fs.rm(distDir, { recursive: true, force: true });
  await fs.mkdir(distDir, { recursive: true });

  const entries = ['index.html', 'app.js', 'styles.css'];
  for (const entry of entries) {
    const sourcePath = path.join(projectRoot, entry);
    if (await pathExists(sourcePath)) {
      const targetPath = path.join(distDir, entry);
      await fs.mkdir(path.dirname(targetPath), { recursive: true });
      await fs.copyFile(sourcePath, targetPath);
    }
  }

  const srcDir = path.join(projectRoot, 'src');
  if (await pathExists(srcDir)) {
    await copyDir(srcDir, path.join(distDir, 'src'));
  }

  log(`Build output available at ${distDir}`);
}

async function main() {
  const [command] = process.argv.slice(2);
  if (!command || command === 'build') {
    await build();
    return;
  }
  if (command === '--help' || command === '-h') {
    log('Supported commands: build');
    return;
  }
  log(`Unknown command: ${command}`);
  process.exit(1);
}

await main();
