import test from 'node:test';
import assert from 'node:assert/strict';
import { getMetricDisplay, getCompletionSummary, getMarketSnapshot } from '../src/marketIntelligenceModel.js';


test('extracts only finite index values and market movers from the existing overview response', () => {
  const snapshot = getMarketSnapshot({
    indices: [{ name: 'NIFTY 50', last_price: 22450.5 }, { name: 'SENSEX', last_price: null }],
    market_movers: { gainers: [{ symbol: 'ABC', ltp: 125.5, percent_change: 2.1 }], losers: [{ symbol: 'XYZ', ltp: 98.4, percent_change: -1.4 }] },
  });
  assert.equal(snapshot.indices[0].value, 22450.5);
  assert.equal(snapshot.indices[1].value, null);
  assert.equal(snapshot.gainers.length, 1);
  assert.equal(snapshot.gainers[0].change, 2.1);
  assert.equal(snapshot.gainers[0].price, 125.5);
  assert.equal(snapshot.losers.length, 1);
  assert.equal(snapshot.losers[0].change, -1.4);
});

test('returns an empty snapshot for missing or malformed overview data', () => {
  assert.deepEqual(getMarketSnapshot(null), { indices: [], gainers: [], losers: [] });
  assert.deepEqual(getMarketSnapshot({ indices: {}, market_movers: null }), { indices: [], gainers: [], losers: [] });
});

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

test('does not convert absent mover changes or prices into fabricated zeroes', () => {
  const snapshot = getMarketSnapshot({
    market_movers: {
      gainers: [{ symbol: 'NO_DATA', change_pct: null, last_price: null }],
      losers: [{ symbol: 'REAL', change_pct: -0.5, last_price: 125.25 }],
    },
  });
  assert.equal(snapshot.gainers[0].change, null);
  assert.equal(snapshot.gainers[0].price, null);
  assert.equal(snapshot.losers[0].change, -0.5);
  assert.equal(snapshot.losers[0].price, 125.25);
});
