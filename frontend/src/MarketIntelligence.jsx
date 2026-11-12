import React from 'react';
import './market-intelligence.css';
import { getCompletionSummary, getMetricDisplay } from './marketIntelligenceModel';

const capabilities = [
  { id: 'futures', title: 'Futures positioning', description: 'Long build-up, short build-up, short covering and long unwinding classifications.', implementation: 'built', integration: 'pending', note: 'Calculation engine is implemented. A live futures/OI data source is not connected.' },
  { id: 'options', title: 'Options analytics', description: 'Put-call ratio and highest open-interest support/resistance calculations.', implementation: 'built', integration: 'pending', note: 'Calculation engine is implemented. A live option-chain feed is not connected.' },
  { id: 'conviction', title: 'Market conviction', description: 'Five confirmation checks and a transparent conviction score.', implementation: 'built', integration: 'pending', note: 'Scoring logic is implemented. Confirmation inputs are not yet supplied by a live pipeline.' },
  { id: 'sectors', title: 'Sector strength', description: 'Sector breadth, advancers, decliners and average constituent movement.', implementation: 'built', integration: 'pending', note: 'Aggregation logic is implemented. Live constituent data is not connected.' },
  { id: 'stream', title: 'Market streaming', description: 'm.Stock Type A frame decoder, bounded tick cache and reconnecting worker.', implementation: 'built', integration: 'pending', note: 'Worker and decoder exist in the feature branch. Existing Flask gateway integration and live connection are pending.' },
];

const overviewMetrics = [
  { label: 'Futures positioning', value: null, detail: 'Waiting for futures + OI feed' },
  { label: 'Options PCR', value: null, detail: 'Waiting for option-chain feed' },
  { label: 'Conviction score', value: null, detail: 'Waiting for five confirmation inputs' },
  { label: 'Sector breadth', value: null, detail: 'Waiting for constituent feed' },
];

function StatusPill({ status }) {
  const label = status === 'built' ? 'Built' : status === 'integrated' ? 'Integrated' : 'Pending';
  return <span className={`mi-status mi-status-${status}`}>{label}</span>;
}

function MetricCard({ metric }) {
  return <article className="mi-metric-card">
    <span className="mi-eyebrow">{metric.label}</span>
    <strong className="mi-metric-value">{getMetricDisplay(metric.value)}</strong>
    <span className="mi-muted">{metric.detail}</span>
  </article>;
}

export default function MarketIntelligence() {
  const summary = getCompletionSummary(capabilities);
  return <main className="market-intelligence-page">
    <header className="mi-page-header">
      <div>
        <p className="mi-eyebrow">MARKETS / INTELLIGENCE</p>
        <h1>Market Intelligence</h1>
        <p className="mi-subtitle">Market structure, positioning and stream readiness in one workspace.</p>
      </div>
      <div className="mi-header-status"><span className="mi-status-dot" /> Live feed not connected</div>
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
        <span className="mi-eyebrow">LIVE DATA</span>
        <strong>Pending</strong>
        <span>Gateway integration and feed verification remain</span>
      </article>
    </section>

    <section className="mi-section" aria-labelledby="mi-market-overview-title">
      <div className="mi-section-heading"><div><p className="mi-eyebrow">MARKET SNAPSHOT</p><h2 id="mi-market-overview-title">Executive overview</h2></div><span className="mi-section-note">No live values are being simulated</span></div>
      <div className="mi-metric-grid">{overviewMetrics.map((metric) => <MetricCard key={metric.label} metric={metric} />)}</div>
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
        <div><span>Analysis API</span><StatusPill status="built" /><small>Accepts normalized futures, options, sector and conviction inputs.</small></div>
        <div><span>Type A frame decoder</span><StatusPill status="built" /><small>Binary packet parsing is implemented.</small></div>
        <div><span>Existing gateway integration</span><StatusPill status="pending" /><small>Not yet connected to the running Flask gateway.</small></div>
        <div><span>Live feed verification</span><StatusPill status="pending" /><small>No live stream or market snapshot is claimed.</small></div>
      </div>
    </section>
  </main>;
}
