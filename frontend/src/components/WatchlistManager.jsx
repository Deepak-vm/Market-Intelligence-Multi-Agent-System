import React, { useState } from 'react';
import { Building2, Plus, Trash2, Globe, Scan } from 'lucide-react';
import axios from 'axios';

export default function WatchlistManager({ companies, onRefreshWatchlist, onTriggerScan, loading }) {
  const [newCompanyName, setNewCompanyName] = useState('');
  const [blogRss, setBlogRss] = useState('');
  const [adding, setAdding] = useState(false);

  const handleAddCompany = async (e) => {
    e.preventDefault();
    if (!newCompanyName.trim()) return;

    setAdding(true);
    try {
      await axios.post('/api/companies', {
        name: newCompanyName.trim(),
        blog_rss: blogRss.trim() || null
      });
      setNewCompanyName('');
      setBlogRss('');
      onRefreshWatchlist();
    } catch (err) {
      alert(err.response?.data?.detail || "Error adding company");
    } finally {
      setAdding(false);
    }
  };

  const handleDelete = async (id, name) => {
    if (!window.confirm(`Remove ${name} from active watchlist?`)) return;
    try {
      await axios.delete(`/api/companies/${id}`);
      onRefreshWatchlist();
    } catch (err) {
      alert("Error deleting company");
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* Add Company Form */}
      <div className="glass-panel" style={{ padding: '24px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '16px' }}>
          <Building2 size={22} color="#00f2fe" />
          <h2 style={{ fontSize: '1.25rem', fontWeight: '700' }}>Dynamic Company Watchlist Management</h2>
        </div>

        <form onSubmit={handleAddCompany} style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
          <input
            type="text"
            className="input-field"
            placeholder="Company Name (e.g., Anthropic, Cohere, Cursor)"
            value={newCompanyName}
            onChange={(e) => setNewCompanyName(e.target.value)}
            style={{ flex: '1', minWidth: '220px' }}
            required
          />
          <input
            type="url"
            className="input-field"
            placeholder="Blog RSS URL (Optional)"
            value={blogRss}
            onChange={(e) => setBlogRss(e.target.value)}
            style={{ flex: '1', minWidth: '220px' }}
          />
          <button type="submit" className="btn-primary" disabled={adding} style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <Plus size={16} /> Add to Watchlist
          </button>
        </form>
      </div>

      {/* Watchlist Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(260px, 1fr))', gap: '16px' }}>
        {companies.map(comp => (
          <div key={comp.id} className="glass-panel" style={{ padding: '18px', display: 'flex', flexDirection: 'column', justifyContent: 'space-between', gap: '12px' }}>
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
                <h3 style={{ fontSize: '1.1rem', fontWeight: '800' }}>{comp.name}</h3>
                <span style={{ fontSize: '0.75rem', background: 'rgba(16, 185, 129, 0.15)', color: '#34d399', padding: '2px 8px', borderRadius: '10px', fontWeight: '700' }}>
                  Active
                </span>
              </div>
              {comp.blog_rss && (
                <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: '4px' }}>
                  <Globe size={12} /> RSS Configured
                </div>
              )}
            </div>

            <div style={{ display: 'flex', gap: '8px', borderTop: '1px solid var(--border-color)', paddingTop: '10px' }}>
              <button
                className="btn-secondary"
                onClick={() => onTriggerScan(comp.name)}
                disabled={loading}
                style={{ flex: 1, fontSize: '0.8rem', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '4px' }}
              >
                <Scan size={14} /> Scan Company
              </button>
              <button
                className="btn-secondary"
                onClick={() => handleDelete(comp.id, comp.name)}
                style={{ color: '#fb7185', borderColor: 'rgba(244,63,94,0.3)', padding: '6px 10px' }}
              >
                <Trash2 size={14} />
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
