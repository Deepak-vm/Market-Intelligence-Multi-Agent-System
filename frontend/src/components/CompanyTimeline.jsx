import React, { useState } from 'react';
import { Calendar, Building, TrendingUp, Users, Package, AlertTriangle } from 'lucide-react';

export default function CompanyTimeline({ events, companies }) {
  const [selectedCompany, setSelectedCompany] = useState(companies[0]?.name || 'OpenAI');

  const companyEvents = events.filter(e => e.company.toLowerCase() === selectedCompany.toLowerCase())
                              .sort((a, b) => new Date(b.event_date) - new Date(a.event_date));

  const getEventIcon = (type) => {
    switch(type) {
      case 'funding': return <TrendingUp size={16} color="#34d399" />;
      case 'leadership': return <Users size={16} color="#60a5fa" />;
      case 'product': return <Package size={16} color="#c084fc" />;
      case 'layoff': return <AlertTriangle size={16} color="#fb7185" />;
      default: return <Calendar size={16} />;
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      <div className="glass-panel" style={{ padding: '20px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <Building size={22} color="#00f2fe" />
          <h2 style={{ fontSize: '1.25rem', fontWeight: '700' }}>Per-Company Intelligence Timeline</h2>
        </div>

        <select
          className="input-field"
          value={selectedCompany}
          onChange={(e) => setSelectedCompany(e.target.value)}
          style={{ fontSize: '0.95rem', fontWeight: '700', padding: '8px 16px' }}
        >
          {companies.map(c => (
            <option key={c.id} value={c.name}>{c.name}</option>
          ))}
        </select>
      </div>

      <div className="glass-panel" style={{ padding: '30px' }}>
        {companyEvents.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '30px', color: 'var(--text-muted)' }}>
            No timeline events recorded for {selectedCompany} yet. Run a scan to discover history.
          </div>
        ) : (
          <div style={{ position: 'relative', paddingLeft: '30px', borderLeft: '2px solid rgba(255,255,255,0.1)' }}>
            {companyEvents.map((evt, idx) => (
              <div key={evt.id} style={{ position: 'relative', marginBottom: '28px' }}>
                {/* Marker dot */}
                <div style={{
                  position: 'absolute',
                  left: '-41px',
                  top: '0px',
                  width: '20px',
                  height: '20px',
                  borderRadius: '50%',
                  background: '#0b0f19',
                  border: '2px solid var(--accent-blue)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center'
                }}>
                  {getEventIcon(evt.event_type)}
                </div>

                <div style={{ background: 'rgba(255,255,255,0.03)', padding: '16px 20px', borderRadius: '12px', border: '1px solid var(--border-color)' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                      <span style={{ fontWeight: '700', fontSize: '1rem', textTransform: 'capitalize' }}>
                        {evt.event_type} Event
                      </span>
                      <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>{evt.event_date}</span>
                    </div>
                    <span style={{ fontSize: '0.8rem', color: 'var(--accent-blue)', fontWeight: '700' }}>
                      {(evt.confidence_score * 100).toFixed(0)}% Confidence
                    </span>
                  </div>

                  <p style={{ color: '#cbd5e1', fontSize: '0.9rem', lineHeight: '1.5' }}>
                    {evt.confidence_rationale}
                  </p>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
