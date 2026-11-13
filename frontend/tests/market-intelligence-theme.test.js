import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';

const css = readFileSync(new URL('../src/market-intelligence.css', import.meta.url), 'utf8');

test('Market Intelligence surfaces use the shared theme token contract', () => {
  for (const token of ['--th-card', '--th-inner', '--th-text', '--th-muted', '--th-border', '--th-accent', '--th-pos', '--th-neg', '--th-warn', '--th-radius', '--th-card-shadow', '--th-font']) {
    assert.ok(css.includes(token), `Market Intelligence must consume ${token}`);
  }
});

test('Market Intelligence has no fixed palette colours that override selected themes', () => {
  assert.doesNotMatch(css, /#[0-9a-f]{3,8}\b|rgba?\(/i);
});

test('Market Intelligence styles all page regions and retain responsive layouts', () => {
  for (const selector of ['.market-intelligence-page', '.mi-page-header', '.mi-market-ribbon', '.mi-workspace-tabs', '.mi-terminal-layout', '.mi-flow-canvas', '.mi-flow-svg', '.mi-flow-stats', '.mi-board-panel', '.mi-flow-table', '.mi-detail-panel', '.mi-unavailable-workspace', '.mi-monitor-workspace', '.mi-monitor-grid', '.mi-flow-path', '.mi-error', ':focus-visible']) {
    assert.ok(css.includes(selector), `Missing themed page selector: ${selector}`);
  }
  assert.match(css, /@media\s*\(max-width:\s*1050px\)/);
  assert.match(css, /@media\s*\(max-width:\s*760px\)/);
});


test('Market Intelligence animation respects reduced-motion preferences and page scoping', () => {
  assert.match(css, /\.market-intelligence-page \.mi-flow-path/);
  assert.match(css, /@media\s*\(prefers-reduced-motion:\s*reduce\)/);
  assert.match(css, /\.market-intelligence-page \.mi-monitor-workspace/);
});
