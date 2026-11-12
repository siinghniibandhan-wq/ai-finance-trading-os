import React, { useCallback, useEffect, useState } from 'react';
import { API_BASE_URL, apiFetch } from './api';
import './market-intelligence.css';
import { getCompletionSummary, getMarketSnapshot } from './marketIntelligenceModel';

const capabilities = [
  { id: 'futures', title: 'Futures positioning', description: 'Long build-up, short build-up, short covering and long unwinding classifications.', implementation: 'built', integration: 'pending', note: 'Calculation engine is implemented. A live futures/OI data source is not connected.' },
  { id: 'options', title: 'Options analytics', description: 'Put-call ratio and highest open-interest support/resistance calculations.', implementation: 'built', integration: 'pending', note: 'Calculation engine is implemented. A live option-chain feed is not connected.' },
  { id: 'conviction', title: 'Market conviction', description: 'Five confirmation checks and a transparent conviction score.', implementation: 'built', integration: 'pending', note: 'Scoring logic is implemented. Confirmation inputs are not yet supplied by a live pipeline.' },
  { id: 'sectors', title: 'Sector strength', description: 'Sector breadth, advancers, decliners and average constituent movement.', implementation: 'built', integration: 'pending', note: 'Aggregation logic is implemented. Live constituent data is not connected.' },
  { id: 'stream', title: 'Market streaming', description: 'm.Stock Type A frame decoder, bounded tick cache and reconnecting worker.', implementation: 'built', integration: 'pending', note: 'Worker and decoder exist in the feature branch. Existing Flask gateway integration and live connection are pending.' },
];

function StatusPill({ status }) {
  const label = status === 'built' ? 'Built' : status === 'integrated' ? 'Integrated' : 'Pending';
  return <span className={`mi-status mi-status-${status}`}>{label}</span>;
}

export default function MarketIntelligence() {
  const [snapshot, setSnapshot] = useState({ indices: [], gainers: [], losers: [] });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [retrievedAt, setRetrievedAt] = useState(null);
  const [providerStatus, setProviderStatus] = useState('Checking market overview');
  const summary = getCompletionSummary(capabilities);
  const refreshSnapshot = useCallback(async () => {
    setError('');
    try {
      const response = await apiFetch(`${API_BASE_URL}/api/market-overview/`, { cache: 'no-store' });
      const payload = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(typeof payload?.detail === 'string' ? payload.detail : payload?.detail?.message || `Market overview returned ${response.status}`);
      const next = getMarketSnapshot(payload);
      setSnapshot(next);
      setRetrievedAt(payload.retrieved_at || payload.last_updated || new Date().toISOString());
      setProviderStatus(payload.status === 'error' ? 'Provider error' : payload.status || 'Snapshot received');
      if (payload.status === 'error') setError('The market provider returned no usable data.');
      else if (Array.isArray(payload.errors) && payload.errors.length) setError('Some market sources are unavailable. Available results are shown.');
    } catch (requestError) {
      setError(requestError?.message || 'Unable to load the market overview.');
      setProviderStatus('Unavailable');
    } finally {
      setLoading(false);
    }
  }, []);
  useEffect(() => {
    refreshSnapshot();
    const timer = window.setInterval(() => {
      if (document.visibilityState === 'visible') refreshSnapshot();
    }, 30000);
    const onVisibility = () => { if (document.visibilityState === 'visible') refreshSnapshot(); };
    document.addEventListener('visibilitychange', onVisibility);
    return () => {
      window.clearInterval(timer);
      document.removeEventListener('visibilitychange', onVisibility);
    };
  }, [refreshSnapshot]);
  const formatNumber = (value, digits = 2) => value === null || value === undefined ? 'Unavailable' : Number(value).toLocaleString('en-IN', { maximumFractionDigits: digits });
  const formatMover = (row) => row.change === null ? 'Change unavailable' : `${row.change > 0 ? '+' : ''}${row.change.toFixed(2)}%`;
  return <main className="market-intelligence-page">
    <header className="mi-page-header">
      <div>
        <p className="mi-eyebrow">MARKETS / INTELLIGENCE</p>
        <h1>Market Intelligence</h1>
        <p className="mi-subtitle">Market structure, positioning and stream readiness in one workspace.</p>
      </div>
      <div className="mi-header-actions"><span className="mi-header-status"><span className="mi-status-dot" /> {providerStatus}</span><button className="mi-refresh-button" type="button" onClick={refreshSnapshot} disabled={loading}>{loading ? 'Refreshing…' : '↻ Refresh'}</button></div>
    </header>

    <section className="mi-summary-grid" aria-label="Implementation overview">
      <article className="mi-summary-card mi-summary-primary">
        <span className="mi-eyebrow">ENGINE IMPLEMENTATION</span>
        <strong>{summary.built} / {summary.total}</strong>
        <span>Calculation and stream components built</span>
      </article>
      <article className="mi-summary-card">
        <span className="mi-eyebrow">INTEGRATED</span>
        <strong>{summary.integrated} / {summary.total}</strong>
        <span>Connected to live data sources</span>
      </article>
      <article className="mi-summary-card">
        <span className="mi-eyebrow">MARKET SNAPSHOT</span>
        <strong>Connected</strong>
        <span>Existing m.Stock overview API · refreshed every 30 seconds</span>
      </article>
    </section>

    <section className="mi-section" aria-labelledby="mi-market-overview-title">
      <div className="mi-section-heading"><div><p className="mi-eyebrow">MARKET SNAPSHOT</p><h2 id="mi-market-overview-title">Executive overview</h2></div><span className="mi-section-note">{retrievedAt ? `Retrieved ${new Date(retrievedAt).toLocaleString('en-IN')}` : 'No successful snapshot yet'} · auto-refresh 30s</span></div>
      {error && <p className="mi-error" role="status">{error}</p>}
      <div className="mi-metric-grid">
        <article className="mi-metric-card"><span className="mi-eyebrow">INDICES RECEIVED</span><strong className="mi-metric-value">{snapshot.indices.length}</strong><span className="mi-muted">From the existing market overview API</span></article>
        <article className="mi-metric-card"><span className="mi-eyebrow">TOP GAINERS</span><strong className="mi-metric-value">{snapshot.gainers.length}</strong><span className="mi-muted">Returned by the provider snapshot</span></article>
        <article className="mi-metric-card"><span className="mi-eyebrow">TOP LOSERS</span><strong className="mi-metric-value">{snapshot.losers.length}</strong><span className="mi-muted">Returned by the provider snapshot</span></article>
        <article className="mi-metric-card"><span className="mi-eyebrow">SNAPSHOT STATUS</span><strong className="mi-metric-value">{loading ? 'Loading' : error ? 'Partial / unavailable' : 'Received'}</strong><span className="mi-muted">Polled every 30 seconds while visible</span></article>
      </div>
      <div className="mi-index-grid" aria-label="Major market indices">{['NIFTY 50', 'SENSEX', 'NIFTY BANK', 'INDIA VIX'].map((name) => {
        const aliases = name === 'NIFTY 50' ? ['NIFTY50', 'NIFTY 50', 'NIFTY'] : name === 'SENSEX' ? ['SENSEX', 'BSE SENSEX'] : name === 'NIFTY BANK' ? ['NIFTY BANK', 'BANK NIFTY', 'BANKNIFTY'] : ['INDIA VIX', 'INDIAVIX', 'VIX'];
        const item = snapshot.indices.find((row) => aliases.includes(String(row.label).toUpperCase().replace(/[^A-Z0-9]/g, '')));
        return <article className="mi-index-card" key={name}><span>{name}</span><strong>{item ? formatNumber(item.value) : loading ? 'Loading…' : 'Unavailable'}</strong><small>{item?.change === null || item?.change === undefined ? (item?.exchange || 'Not returned by API') : `${item.change > 0 ? '+' : ''}${item.change.toFixed(2)}%`}</small></article>;
      })}</div>
      <div className="mi-movers-grid">
        <div className="mi-movers-panel"><h3>Top gainers</h3>{snapshot.gainers.length ? snapshot.gainers.slice(0, 5).map((row) => <div className="mi-mover-row" key={`g-${row.exchange}-${row.symbol}`}><span><strong>{row.symbol}</strong><small>{row.name}</small></span><b className="mi-positive">{formatMover(row)}</b></div>) : <p className="mi-muted">{loading ? 'Loading market movers…' : 'No gainers returned by the market overview API.'}</p>}</div>
        <div className="mi-movers-panel"><h3>Top losers</h3>{snapshot.losers.length ? snapshot.losers.slice(0, 5).map((row) => <div className="mi-mover-row" key={`l-${row.exchange}-${row.symbol}`}><span><strong>{row.symbol}</strong><small>{row.name}</small></span><b className="mi-negative">{formatMover(row)}</b></div>) : <p className="mi-muted">{loading ? 'Loading market movers…' : 'No losers returned by the market overview API.'}</p>}</div>
      </div>
    </section>

    <section className="mi-section" aria-labelledby="mi-capabilities-title">
      <div className="mi-section-heading"><div><p className="mi-eyebrow">CAPABILITY TRACKER</p><h2 id="mi-capabilities-title">Intelligence modules</h2></div><span className="mi-section-note">Build status is separate from live integration</span></div>
      <div className="mi-capability-grid">{capabilities.map((item) => <article className="mi-capability-card" key={item.id}>
        <div className="mi-capability-top"><h3>{item.title}</h3><StatusPill status={item.implementation} /></div>
        <p>{item.description}</p>
        <div className="mi-capability-foot"><span>Data integration</span><StatusPill status={item.integration} /></div>
        <p className="mi-capability-note">{item.note}</p>
      </article>)}</div>
    </section>

    <section className="mi-section" aria-labelledby="mi-connection-title">
      <div className="mi-section-heading"><div><p className="mi-eyebrow">CONNECTIVITY</p><h2 id="mi-connection-title">Streaming & verification</h2></div><span className="mi-status mi-status-pending">Not live</span></div>
      <div className="mi-connection-panel">
        <div className="mi-connection-icon">↗</div>
        <div className="mi-connection-copy"><h3>m.Stock stream gateway integration pending</h3><p>The Type A decoder and worker are present in the backend feature branch. The worker has not yet been connected to the existing Flask gateway, so connection health, last tick time, reconnect count and cached ticks cannot be reported here.</p></div>
      </div>
      <div className="mi-verification-list">
        <div><span>Market overview API</span><StatusPill status="integrated" /><small>Existing m.Stock gateway snapshot supplies indices, gainers and losers.</small></div>
        <div><span>Analysis API</span><StatusPill status="built" /><small>Accepts normalized futures, options, sector and conviction inputs; not yet connected to a live F&O feed.</small></div>
        <div><span>Type A frame decoder</span><StatusPill status="built" /><small>Binary packet parsing is implemented.</small></div>
        <div><span>Existing gateway integration</span><StatusPill status="pending" /><small>Not yet connected to the running Flask gateway.</small></div>
        <div><span>Live feed verification</span><StatusPill status="pending" /><small>No live stream or market snapshot is claimed.</small></div>
      </div>
    </section>
  </main>;
}
