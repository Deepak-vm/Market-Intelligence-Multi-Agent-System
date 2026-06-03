import React, { useState } from 'react';
import { ExternalLink, CheckCircle, Clock, ShieldCheck, ShieldAlert, Sparkles, Filter } from 'lucide-react';

export default function EventFeed({ events, onTriggerScan, loading }) {
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');

  const filteredEvents = events.filter(e => {
    const matchesCat = selectedCategory === 'all' || e.event_type === selectedCategory;
    const matchesStatus = statusFilter === 'all' || e.status === statusFilter;
    const matchesSearch = e.company.toLowerCase().includes(searchQuery.toLowerCase()) ||
                          e.confidence_rationale.toLowerCase().includes(searchQuery.toLowerCase()) ||
                          JSON.stringify(e.details).toLowerCase().includes(searchQuery.toLowerCase());
    return matchesCat && matchesStatus && matchesSearch;
  });

  const getBadgeClass = (type) => {
    switch (type) {
      case 'funding': return 'badge-funding';
      case 'leadership': return 'badge-leadership';
      case 'product': return 'badge-product';
      case 'layoff': return 'badge-layoff';
      default: return '';
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* Top Controls & Filters */}
      <div className="glass-panel" style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <Sparkles size={22} color="#00f2fe" />
            <h2 style={{ fontSize: '1.25rem', fontWeight: '700' }}>Live Intelligence Event Feed</h2>
          </div>
          <button className="btn-primary" onClick={() => onTriggerScan(null)} disabled={loading}>
            {loading ? 'Running Multi-Agent Scan...' : '⚡ Trigger Global Watchlist Scan'}
          </button>
        </div>

        <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap', alignItems: 'center' }}>
          <input
            type="text"
            className="input-field"
            placeholder="Search events, companies, keywords..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            style={{ flex: 1, minWidth: '220px' }}
          />

          <div style={{ display: 'flex', gap: '8px' }}>
            {['all', 'funding', 'leadership', 'product', 'layoff'].map(cat => (
              <button
                key={cat}
                className={`btn-secondary ${selectedCategory === cat ? 'btn-primary' : ''}`}
                onClick={() => setSelectedCategory(cat)}
                style={{ fontSize: '0.85rem', textTransform: 'capitalize' }}
              >
                {cat}
              </button>
            ))}
          </div>

          <select
            className="input-field"
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            style={{ fontSize: '0.85rem' }}
          >
            <option value="all">All Statuses</option>
            <option value="auto_published">Auto-Published Only</option>
            <option value="pending_review">Pending Review</option>
          </select>
        </div>
      </div>

      {/* Events Feed Grid */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
        {filteredEvents.length === 0 ? (
          <div className="glass-panel" style={{ padding: '40px', textAlign: 'center', color: 'var(--text-muted)' }}>
            No events matching filters. Trigger a scan to discover fresh market intelligence!
          </div>
        ) : (
          filteredEvents.map(evt => (
            <div key={evt.id} className="glass-panel" style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '10px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                  <span style={{ fontSize: '1.2rem', fontWeight: '800', color: '#fff' }}>{evt.company}</span>
                  <span className={`px-2 py-1 rounded-md text-xs font-bold ${getBadgeClass(evt.event_type)}`} style={{ padding: '4px 10px', borderRadius: '6px', fontSize: '0.75rem', fontWeight: '700', textTransform: 'uppercase' }}>
                    {evt.event_type}
                  </span>
                  <span style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>{evt.event_date}</span>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  {evt.status === 'auto_published' ? (
                    <span className="badge-auto" style={{ padding: '4px 10px', borderRadius: '20px', fontSize: '0.75rem', fontWeight: '700', display: 'flex', alignItems: 'center', gap: '4px' }}>
                      <ShieldCheck size={14} /> Corroborated ({evt.sources.length} sources)
                    </span>
                  ) : (
                    <span className="badge-review" style={{ padding: '4px 10px', borderRadius: '20px', fontSize: '0.75rem', fontWeight: '700', display: 'flex', alignItems: 'center', gap: '4px' }}>
                      <ShieldAlert size={14} /> Needs Human Review
                    </span>
                  )}
                  <div style={{ background: 'rgba(255,255,255,0.06)', padding: '4px 10px', borderRadius: '8px', fontSize: '0.8rem', fontWeight: '700' }}>
                    Conf: {(evt.confidence_score * 100).toFixed(0)}%
                  </div>
                </div>
              </div>

              {/* Rationale & Details */}
              <p style={{ fontSize: '0.95rem', color: '#cbd5e1', lineHeight: '1.5' }}>
                {evt.confidence_rationale}
              </p>

              {/* Extracted JSON details preview */}
              {Object.keys(evt.details).length > 0 && (
                <div style={{ background: 'rgba(0,0,0,0.3)', padding: '10px 14px', borderRadius: '8px', fontSize: '0.85rem', color: '#94a3b8', display: 'flex', gap: '16px', flexWrap: 'wrap' }}>
                  {Object.entries(evt.details).map(([k, v]) => (
                    v ? <div key={k}><strong>{k.replace('_', ' ')}:</strong> {String(v)}</div> : null
                  ))}
                </div>
              )}

              {/* Sources footer */}
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flexWrap: 'wrap', paddingTop: '6px', borderTop: '1px solid rgba(255,255,255,0.05)' }}>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: '600' }}>Verified Sources:</span>
                {evt.sources.map((src, idx) => (
                  <a
                    key={idx}
                    href={src.url}
                    target="_blank"
                    rel="noreferrer"
                    style={{ fontSize: '0.8rem', color: 'var(--accent-blue)', textDecoration: 'none', display: 'flex', alignItems: 'center', gap: '4px' }}
                  >
                    {src.source_name || 'Source'} <ExternalLink size={12} />
                  </a>
                ))}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
