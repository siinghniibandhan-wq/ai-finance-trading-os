import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { API_BASE_URL, apiFetch } from './api';
import './market-intelligence.css';
import { filterFlowRows, getFlowRows, getMarketSnapshot } from './marketIntelligenceModel';

const WORKSPACES = [
  { id: 'flow', label: 'Market Flow', ready: true },
  { id: 'board', label: 'Flow Board', ready: true },
  { id: 'futures', label: 'Futures', ready: false },
  { id: 'options', label: 'Options', ready: false },
  { id: 'sectors', label: 'Sectors', ready: false },
  { id: 'replay', label: 'Charts & Replay', ready: false },
];

const fmt = (value, digits = 2) => value === null || value === undefined || !Number.isFinite(Number(value))
  ? '—'
  : Number(value).toLocaleString('en-IN', { maximumFractionDigits: digits });
const signed = (value) => value === null || value === undefined ? '—' : `${value > 0 ? '+' : ''}${fmt(value)}%`;

function Change({ value }) {
  const state = value === null || value === undefined ? 'unknown' : value > 0 ? 'positive' : value < 0 ? 'negative' : 'flat';
  return <span className={`mi-change mi-change-${state}`}>{signed(value)}</span>;
}

function FlowDiagram({ rows, selected, onSelect }) {
  const rising = rows.filter((row) => row.change > 0).slice(0, 7);
  const falling = rows.filter((row) => row.change < 0).slice(0, 7);
  const centerX = 50;
  const positions = (items, x) => items.map((row, index) => ({
    row, x, y: 13 + index * (74 / Math.max(items.length, 1)),
  }));
  const left = positions(rising, 9);
  const right = positions(falling, 91);
  return <div className="mi-flow-canvas">
    <div className="mi-flow-legend"><span><i className="mi-dot-up" /> Advancing snapshot movers</span><span><i className="mi-dot-down" /> Declining snapshot movers</span></div>
    {left.length || right.length ? <svg className="mi-flow-svg" viewBox="0 0 100 100" role="img" aria-label="Directional flow of available market movers">
      <defs>
        <linearGradient id="mi-flow-up" x1="0" x2="1"><stop offset="0%" stopColor="var(--mi-positive)" stopOpacity=".12"/><stop offset="100%" stopColor="var(--mi-positive)" stopOpacity=".8"/></linearGradient>
        <linearGradient id="mi-flow-down" x1="0" x2="1"><stop offset="0%" stopColor="var(--mi-negative)" stopOpacity=".8"/><stop offset="100%" stopColor="var(--mi-negative)" stopOpacity=".12"/></linearGradient>
      </defs>
      {left.map(({ row, x, y }) => <path key={`up-${row.symbol}`} d={`M ${x+10} ${y} C 32 ${y}, 39 50, 49 50`} stroke="url(#mi-flow-up)" strokeWidth={Math.max(0.7, Math.min(2.6, Math.abs(row.change) * .35))} fill="none" />)}
      {right.map(({ row, x, y }) => <path key={`down-${row.symbol}`} d={`M 51 50 C 62 50, 68 ${y}, ${x-10} ${y}`} stroke="url(#mi-flow-down)" strokeWidth={Math.max(0.7, Math.min(2.6, Math.abs(row.change) * .35))} fill="none" />)}
      <circle cx={centerX} cy="50" r="9" className="mi-flow-core" />
      <text x={centerX} y="48.5" textAnchor="middle" className="mi-flow-core-title">MARKET</text>
      <text x={centerX} y="53.5" textAnchor="middle" className="mi-flow-core-sub">SNAPSHOT</text>
      {left.map(({ row, x, y }) => <g key={`node-up-${row.symbol}`} className={`mi-flow-node ${selected === row.symbol ? 'is-selected' : ''}`} onClick={() => onSelect(row.symbol)} role="button" tabIndex="0" aria-label={`${row.symbol}, up ${signed(row.change)}`} onKeyDown={(event) => { if (event.key === 'Enter' || event.key === ' ') onSelect(row.symbol); }}>
        <circle cx={x} cy={y} r="4.5" className="mi-flow-node-up"/><text x={x} y={y+8} textAnchor="middle">{row.symbol.slice(0, 11)}</text>
      </g>)}
      {right.map(({ row, x, y }) => <g key={`node-down-${row.symbol}`} className={`mi-flow-node ${selected === row.symbol ? 'is-selected' : ''}`} onClick={() => onSelect(row.symbol)} role="button" tabIndex="0" aria-label={`${row.symbol}, down ${signed(row.change)}`} onKeyDown={(event) => { if (event.key === 'Enter' || event.key === ' ') onSelect(row.symbol); }}>
        <circle cx={x} cy={y} r="4.5" className="mi-flow-node-down"/><text x={x} y={y+8} textAnchor="middle">{row.symbol.slice(0, 11)}</text>
      </g>)}
    </svg> : <div className="mi-flow-empty"><strong>No directional movers available</strong><span>The connected overview has not returned positive or negative mover changes.</span></div>}
    <div className="mi-flow-columns">
      <div><strong className="mi-positive">{rising.length} advancing</strong><span>Top available positive movers</span></div>
      <div><strong className="mi-negative">{falling.length} declining</strong><span>Top available negative movers</span></div>
    </div>
  </div>;
}

function FlowBoard({ rows, selected, onSelect }) {
  const [query, setQuery] = useState('');
  const [direction, setDirection] = useState('all');
  const [sort, setSort] = useState('change');
  const visible = useMemo(() => filterFlowRows(rows, { query, direction, sort }), [rows, query, direction, sort]);
  return <section className="mi-board-panel">
    <div className="mi-board-toolbar">
      <label className="mi-search"><span>⌕</span><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search symbol or company" aria-label="Search instruments"/></label>
      <select value={direction} onChange={(event) => setDirection(event.target.value)} aria-label="Filter direction"><option value="all">All directions</option><option value="up">Advancing</option><option value="down">Declining</option><option value="flat">Unchanged</option><option value="unknown">Change unavailable</option></select>
      <select value={sort} onChange={(event) => setSort(event.target.value)} aria-label="Sort instruments"><option value="change">Sort: % change</option><option value="price">Sort: price</option><option value="symbol">Sort: symbol</option></select>
    </div>
    <div className="mi-table-wrap"><table className="mi-flow-table">
      <thead><tr><th>Instrument</th><th>Last price</th><th>Change</th><th>Exchange</th><th>Source</th></tr></thead>
      <tbody>{visible.map((row) => <tr key={row.symbol} className={selected === row.symbol ? 'is-selected' : ''} onClick={() => onSelect(row.symbol)} tabIndex="0" onKeyDown={(event) => { if (event.key === 'Enter') onSelect(row.symbol); }}>
        <td><strong>{row.symbol}</strong><small>{row.name}</small></td><td>{row.price === null ? '—' : `₹${fmt(row.price)}`}</td><td><Change value={row.change}/></td><td>{row.exchange || '—'}</td><td><span className="mi-source-tag">Overview snapshot</span></td>
      </tr>)}
      {!visible.length && <tr><td colSpan="5" className="mi-table-empty">No instruments match this filter.</td></tr>}</tbody>
    </table></div>
    <footer className="mi-board-footer"><span>Showing {visible.length} of {rows.length} returned movers</span><span>Not the full F&O universe</span></footer>
  </section>;
}

function InstrumentDetail({ row, onClear }) {
  if (!row) return <aside className="mi-detail-panel"><p className="mi-eyebrow">INSTRUMENT DETAIL</p><strong>Select an instrument</strong><span>Choose a node or row to inspect its available snapshot values.</span></aside>;
  return <aside className="mi-detail-panel">
    <div className="mi-detail-heading"><div><p className="mi-eyebrow">SELECTED INSTRUMENT</p><h3>{row.symbol}</h3><span>{row.name}</span></div><button type="button" onClick={onClear} aria-label="Clear selected instrument">×</button></div>
    <div className="mi-detail-price"><strong>{row.price === null ? '—' : `₹${fmt(row.price)}`}</strong><Change value={row.change}/></div>
    <dl><div><dt>Exchange</dt><dd>{row.exchange || 'Unavailable'}</dd></div><div><dt>Price change</dt><dd>{signed(row.change)}</dd></div><div><dt>Open interest</dt><dd>Not supplied</dd></div><div><dt>Volume profile</dt><dd>Not supplied</dd></div><div><dt>Market depth</dt><dd>Not supplied</dd></div><div><dt>Data type</dt><dd>Market overview snapshot</dd></div></dl>
    <p className="mi-detail-note">Futures positioning, OI and order-book depth require an instrument-level feed. They are not inferred from price movement.</p>
  </aside>;
}

export default function MarketIntelligence() {
  const [snapshot, setSnapshot] = useState({ indices: [], gainers: [], losers: [] });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [retrievedAt, setRetrievedAt] = useState(null);
  const [providerStatus, setProviderStatus] = useState('Checking market overview');
  const [activeWorkspace, setActiveWorkspace] = useState('flow');
  const [selectedSymbol, setSelectedSymbol] = useState('');
  const refreshSnapshot = useCallback(async () => {
    setError('');
    try {
      const response = await apiFetch(`${API_BASE_URL}/api/market-overview/`, { cache: 'no-store' });
      const payload = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(typeof payload?.detail === 'string' ? payload.detail : payload?.detail?.message || `Market overview returned ${response.status}`);
      const next = getMarketSnapshot(payload);
      setSnapshot(next);
      setRetrievedAt(payload.retrieved_at || payload.last_updated || new Date().toISOString());
      setProviderStatus(payload.status === 'error' ? 'Provider error' : payload.status === 'partial' ? 'Partial snapshot' : payload.status || 'Snapshot received');
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
    const timer = window.setInterval(() => { if (document.visibilityState === 'visible') refreshSnapshot(); }, 30000);
    const onVisibility = () => { if (document.visibilityState === 'visible') refreshSnapshot(); };
    document.addEventListener('visibilitychange', onVisibility);
    return () => { window.clearInterval(timer); document.removeEventListener('visibilitychange', onVisibility); };
  }, [refreshSnapshot]);

  const rows = useMemo(() => getFlowRows(snapshot), [snapshot]);
  const selected = rows.find((row) => row.symbol === selectedSymbol) || null;
  const advancing = rows.filter((row) => row.change > 0).length;
  const declining = rows.filter((row) => row.change < 0).length;
  const indices = snapshot.indices;
  return <main className="market-intelligence-page mi-terminal">
    <header className="mi-page-header">
      <div><p className="mi-eyebrow">FINANCIAL OS / MARKET STRUCTURE</p><h1>Order Flow Terminal</h1><p className="mi-subtitle">Directional market map, instrument board and market-data workspace.</p></div>
      <div className="mi-header-actions"><span className="mi-header-status"><span className="mi-status-dot"/>{providerStatus}</span><button className="mi-refresh-button" type="button" onClick={refreshSnapshot} disabled={loading}>{loading ? 'Refreshing…' : '↻ Refresh'}</button></div>
    </header>

    <section className="mi-market-ribbon" aria-label="Market indices">
      {indices.length ? indices.map((item, index) => <div className="mi-ribbon-index" key={`${item.label}-${index}`}><span>{item.label}</span><strong>{fmt(item.value)}</strong><Change value={item.change}/></div>) : <div className="mi-ribbon-empty">{loading ? 'Loading market indices…' : 'Index values not returned by the connected overview.'}</div>}
      <div className="mi-ribbon-meta"><span className="mi-live-indicator"/><strong>{rows.length}</strong><span>movers returned</span><small>{retrievedAt ? new Date(retrievedAt).toLocaleTimeString('en-IN') : 'Awaiting snapshot'}</small></div>
    </section>

    <nav className="mi-workspace-tabs" aria-label="Market workspaces">{WORKSPACES.map((tab) => <button key={tab.id} type="button" className={activeWorkspace === tab.id ? 'active' : ''} onClick={() => tab.ready && setActiveWorkspace(tab.id)} disabled={!tab.ready} aria-current={activeWorkspace === tab.id ? 'page' : undefined}>{tab.label}{!tab.ready && <span>Pending feed</span>}</button>)}</nav>
    {error && <p className="mi-error" role="status">{error}</p>}

    {activeWorkspace === 'flow' && <section className="mi-terminal-layout">
      <div className="mi-primary-workspace">
        <div className="mi-workspace-heading"><div><p className="mi-eyebrow">LIVE SNAPSHOT FLOW</p><h2>Market directional map</h2></div><span className="mi-data-badge">Snapshot · 30s refresh</span></div>
        <div className="mi-flow-stats"><div><span>Advancing</span><strong className="mi-positive">{advancing}</strong></div><div><span>Declining</span><strong className="mi-negative">{declining}</strong></div><div><span>Returned movers</span><strong>{rows.length}</strong></div><div><span>F&O universe</span><strong>Not connected</strong></div></div>
        <FlowDiagram rows={rows} selected={selectedSymbol} onSelect={setSelectedSymbol}/>
        <div className="mi-workspace-subheading"><div><p className="mi-eyebrow">INSTRUMENT UNIVERSE</p><h2>Flow Board</h2></div><button type="button" className="mi-text-button" onClick={() => setActiveWorkspace('board')}>Open full board →</button></div>
        <FlowBoard rows={rows.slice(0, 8)} selected={selectedSymbol} onSelect={setSelectedSymbol}/>
      </div>
      <InstrumentDetail row={selected} onClear={() => setSelectedSymbol('')}/>
    </section>}

    {activeWorkspace === 'board' && <section className="mi-board-workspace"><div className="mi-workspace-heading"><div><p className="mi-eyebrow">PROVIDER RETURNED UNIVERSE</p><h2>Market Flow Board</h2></div><span className="mi-data-badge">Sortable · Filterable</span></div><FlowBoard rows={rows} selected={selectedSymbol} onSelect={setSelectedSymbol}/><InstrumentDetail row={selected} onClear={() => setSelectedSymbol('')}/></section>}

    {['futures','options','sectors','replay'].includes(activeWorkspace) && <section className="mi-unavailable-workspace"><p className="mi-eyebrow">DATA SOURCE REQUIRED</p><h2>{WORKSPACES.find((item) => item.id === activeWorkspace)?.label}</h2><p>This workspace is intentionally not displaying simulated data. The existing backend calculation engines can process normalized inputs, but the connected market overview does not supply the required {activeWorkspace === 'futures' ? 'futures price and open-interest history' : activeWorkspace === 'options' ? 'option-chain strikes and call/put open interest' : activeWorkspace === 'sectors' ? 'constituent-level sector breadth' : 'historical candles and replay data'}.</p><ul><li>Provider adapter and instrument mapping must be verified.</li><li>Source timestamps, freshness and missing-data states must be preserved.</li><li>Workspace will be enabled only after live data is validated.</li></ul></section>}

    <footer className="mi-terminal-footer"><span>Read-only analytics · No order placement from this workspace</span><span>Source: m.Stock via existing Market Overview API · Returned top movers only</span></footer>
  </main>;
}
