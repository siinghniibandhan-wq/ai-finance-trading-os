export function getMetricDisplay(value) {
  if (value === null || value === undefined || value === '') return 'Not connected';
  if (typeof value === 'number') return Number.isFinite(value) ? String(value) : 'Not connected';
  if (typeof value === 'string') return value;
  return 'Not connected';
}

export function getCompletionSummary(items) {
  const rows = Array.isArray(items) ? items : [];
  return {
    built: rows.filter((item) => item.implementation === 'built').length,
    integrated: rows.filter((item) => item.integration === 'integrated').length,
    total: rows.length,
  };
}
