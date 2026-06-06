import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Sparkles, Activity, ShieldAlert, Building2, BarChart2 } from 'lucide-react';
import EventFeed from './components/EventFeed';
import CompanyTimeline from './components/CompanyTimeline';
import ReviewQueue from './components/ReviewQueue';
import WatchlistManager from './components/WatchlistManager';
import MetricsDashboard from './components/MetricsDashboard';

export default function App() {
  const [activeTab, setActiveTab] = useState('feed');
  const [events, setEvents] = useState([]);
  const [companies, setCompanies] = useState([]);
  const [metrics, setMetrics] = useState(null);
  const [loading, setLoading] = useState(false);

  const fetchData = async () => {
    try {
      const [eventsRes, compRes, metricsRes] = await Promise.all([
        axios.get('/api/events'),
        axios.get('/api/companies'),
        axios.get('/api/metrics')
      ]);
      setEvents(eventsRes.data);
      setCompanies(compRes.data);
      setMetrics(metricsRes.data);
    } catch (err) {
      console.error("Error fetching application data:", err);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleTriggerScan = async (companyName = null) => {
    setLoading(true);
    try {
      await axios.post('/api/scans/trigger', { company: companyName, lookback_days: 30 });
      // Poll after 3 seconds to update UI
      setTimeout(() => {
        fetchData();
        setLoading(false);
      }, 3500);
    } catch (err) {
      alert("Error triggering scan");
      setLoading(false);
    }
  };

  return (
    <div style={{ maxWidth: '1280px', margin: '0 auto', padding: '30px 20px' }}>
      {/* Header Banner */}
      <header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '30px', flexWrap: 'wrap', gap: '20px' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <div style={{ background: 'linear-gradient(135deg, #00f2fe 0%, #4facfe 100%)', padding: '10px', borderRadius: '12px', display: 'flex' }}>
              <Sparkles size={26} color="#0b0f19" />
            </div>
            <div>
              <h1 style={{ fontSize: '1.75rem', fontWeight: '800', tracking: '-0.02em', background: 'linear-gradient(to right, #ffffff, #94a3b8)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
                Market Intelligence Multi-Agent System
              </h1>
              <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>
                Two-agent signal tracking (Searcher + Analyst) with DBSCAN dedup & cross-source verification
              </p>
            </div>
          </div>
        </div>

        {/* Navigation Tabs */}
        <nav className="glass-panel" style={{ padding: '6px', display: 'flex', gap: '6px', borderRadius: '12px' }}>
          {[
            { id: 'feed', label: 'Event Feed', icon: Activity },
            { id: 'timeline', label: 'Timeline', icon: Building2 },
            { id: 'review', label: 'Review Queue', icon: ShieldAlert, badge: metrics?.pending_review_count },
            { id: 'watchlist', label: 'Watchlist', icon: Building2 },
            { id: 'metrics', label: 'Telemetry', icon: BarChart2 }
          ].map(tab => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                style={{
                  background: isActive ? 'linear-gradient(135deg, #00f2fe 0%, #4facfe 100%)' : 'transparent',
                  color: isActive ? '#0b0f19' : 'var(--text-main)',
                  fontWeight: '700',
                  border: 'none',
                  padding: '8px 16px',
                  borderRadius: '8px',
                  cursor: 'pointer',
                  fontSize: '0.85rem',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  transition: 'all 0.15s ease'
                }}
              >
                <Icon size={16} />
                {tab.label}
                {tab.badge > 0 && (
                  <span style={{ background: '#f59e0b', color: '#000', borderRadius: '10px', padding: '1px 6px', fontSize: '0.75rem' }}>
                    {tab.badge}
                  </span>
                )}
              </button>
            );
          })}
        </nav>
      </header>

      {/* Main View Area */}
      <main>
        {activeTab === 'feed' && (
          <EventFeed events={events} onTriggerScan={handleTriggerScan} loading={loading} />
        )}

        {activeTab === 'timeline' && (
          <CompanyTimeline events={events} companies={companies} />
        )}

        {activeTab === 'review' && (
          <ReviewQueue onQueueResolved={fetchData} />
        )}

        {activeTab === 'watchlist' && (
          <WatchlistManager
            companies={companies}
            onRefreshWatchlist={fetchData}
            onTriggerScan={handleTriggerScan}
            loading={loading}
          />
        )}

        {activeTab === 'metrics' && (
          <MetricsDashboard metrics={metrics} />
        )}
      </main>
    </div>
  );
}
