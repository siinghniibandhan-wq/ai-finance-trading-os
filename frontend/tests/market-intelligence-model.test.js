import test from 'node:test';
import assert from 'node:assert/strict';
import { getMetricDisplay, getCompletionSummary } from '../src/marketIntelligenceModel.js';

test('does not present missing metrics as live values', () => {
  assert.equal(getMetricDisplay(null), 'Not connected');
  assert.equal(getMetricDisplay(undefined), 'Not connected');
});

test('formats finite numeric metrics without inventing a value', () => {
  assert.equal(getMetricDisplay(1.25), '1.25');
  assert.equal(getMetricDisplay(Number.NaN), 'Not connected');
});

test('completion summary counts implemented engines separately from live integrations', () => {
  assert.deepEqual(getCompletionSummary([
    { implementation: 'built', integration: 'pending' },
    { implementation: 'built', integration: 'integrated' },
    { implementation: 'pending', integration: 'pending' },
  ]), { built: 2, integrated: 1, total: 3 });
});
