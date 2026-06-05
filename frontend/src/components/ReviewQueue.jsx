import React, { useState, useEffect } from 'react';
import { ShieldAlert, CheckCircle, XCircle, ExternalLink, RefreshCw } from 'lucide-react';
import axios from 'axios';

export default function ReviewQueue({ onQueueResolved }) {
  const [queueItems, setQueueItems] = useState([]);
  const [loading, setLoading] = useState(false);
  const [rejectReason, setRejectReason] = useState({});

  const fetchQueue = async () => {
    setLoading(true);
    try:
      const resp = await axios.get('/api/review');
      setQueueItems(resp.data);
    } catch (e) {
      console.error("Error fetching review queue", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchQueue();
  }, []);

  const handleApprove = async (eventId) => {
    try {
      await axios.post(`/api/review/${eventId}/approve`);
      fetchQueue();
      if (onQueueResolved) onQueueResolved();
    } catch (e) {
      alert("Error approving event");
    }
  };

  const handleReject = async (eventId) => {
    const reason = rejectReason[eventId] || 'Low signal quality';
    try {
      await axios.post(`/api/review/${eventId}/reject`, { reason });
      fetchQueue();
      if (onQueueResolved) onQueueResolved();
    } catch (e) {
      alert("Error rejecting event");
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      <div className="glass-panel" style={{ padding: '20px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <ShieldAlert size={22} color="#f59e0b" />
          <h2 style={{ fontSize: '1.25rem', fontWeight: '700' }}>Human Verification Queue</h2>
          <span style={{ background: 'rgba(245, 158, 11, 0.2)', color: '#fbbf24', padding: '2px 8px', borderRadius: '12px', fontSize: '0.8rem', fontWeight: '700' }}>
            {queueItems.length} Pending
          </span>
        </div>

        <button className="btn-secondary" onClick={fetchQueue} disabled={loading} style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <RefreshCw size={14} /> Refresh Queue
        </button>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
        {queueItems.length === 0 ? (
          <div className="glass-panel" style={{ padding: '40px', textAlign: 'center', color: 'var(--text-muted)' }}>
            🎉 Verification queue is empty! All current market events are corroborating and auto-published.
          </div>
        ) : (
          queueItems.map(item => (
            <div key={item.review_id} className="glass-panel" style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '14px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '10px' }}>
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '4px' }}>
                    <span style={{ fontSize: '1.1rem', fontWeight: '800' }}>{item.company}</span>
                    <span style={{ background: 'rgba(255,255,255,0.08)', padding: '2px 8px', borderRadius: '4px', fontSize: '0.75rem', fontWeight: '700', textTransform: 'uppercase' }}>
                      {item.event_type}
                    </span>
                    <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>{item.event_date}</span>
                  </div>
                  <div style={{ fontSize: '0.85rem', color: '#f59e0b', fontWeight: '600' }}>
                    Flagged Reason: {item.reason_flagged}
                  </div>
                </div>

                <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
                  <button
                    className="btn-primary"
                    onClick={() => handleApprove(item.event_id)}
                    style={{ background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)', color: '#fff', display: 'flex', alignItems: 'center', gap: '6px' }}
                  >
                    <CheckCircle size={16} /> Approve & Publish
                  </button>
                  <button
                    className="btn-secondary"
                    onClick={() => handleReject(item.event_id)}
                    style={{ background: 'rgba(244,63,94,0.15)', color: '#fb7185', borderColor: 'rgba(244,63,94,0.3)', display: 'flex', alignItems: 'center', gap: '6px' }}
                  >
                    <XCircle size={16} /> Reject Event
                  </button>
                </div>
              </div>

              <p style={{ color: '#cbd5e1', fontSize: '0.9rem' }}>
                {item.confidence_rationale}
              </p>

              {/* Source list */}
              <div style={{ display: 'flex', gap: '12px', alignItems: 'center', flexWrap: 'wrap' }}>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Source:</span>
                {item.sources.map((src, idx) => (
                  <a key={idx} href={src.url} target="_blank" rel="noreferrer" style={{ fontSize: '0.8rem', color: 'var(--accent-blue)', textDecoration: 'none' }}>
                    {src.headline.substring(0, 50)}... <ExternalLink size={10} />
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
