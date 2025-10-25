#!/usr/bin/env node
import { renderUpgradeScreen } from './runtime/UpgradeScreen.js';

const html = renderUpgradeScreen({ tier: 'free' });
process.stdout.write(html.trim());
