import { useState, useEffect, useMemo, useRef } from 'react';
import { Shield, LayoutDashboard, Search, Wifi, WifiOff } from 'lucide-react';
import SummaryCards from './components/SummaryCards';
import Filters from './components/Filters';
import AlertCard from './components/AlertCard';
import InvestigationTable from './components/InvestigationTable';
import InvestigationModal from './components/InvestigationModal';
import Toast from './components/Toast';
import './index.css';

const API_BASE = 'http://localhost:8000/api/v1';

function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [events, setEvents] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [investigations, setInvestigations] = useState([]);
  const [selectedInvestigation, setSelectedInvestigation] = useState(null);
  
  const [runningAlerts, setRunningAlerts] = useState({});
  const [filters, setFilters] = useState({ search: '', severity: 'ALL' });
  const [sseConnected, setSseConnected] = useState(false);
  const [toasts, setToasts] = useState([]);

  // Refs for scrolling
  const eventsRef = useRef(null);
  const alertsRef = useRef(null);

  const showToast = (message, type = 'success') => {
    const id = Date.now();
    setToasts(prev => [...prev, { id, message, type }]);
  };

  const removeToast = (id) => {
    setToasts(prev => prev.filter(t => t.id !== id));
  };

  const fetchEvents = async () => {
    try {
      const res = await fetch(`${API_BASE}/events/`);
      if (res.ok) setEvents(await res.json());
    } catch (err) { console.error('Failed to fetch events', err); }
  };

  const fetchAlerts = async () => {
    try {
      const res = await fetch(`${API_BASE}/alerts/`);
      if (res.ok) setAlerts(await res.json());
    } catch (err) { console.error('Failed to fetch alerts', err); }
  };

  const fetchInvestigations = async () => {
    try {
      const res = await fetch(`${API_BASE}/investigations/`);
      if (res.ok) setInvestigations(await res.json());
    } catch (err) { console.error('Failed to fetch investigations', err); }
  };

  const runInvestigation = async (alertId) => {
    setRunningAlerts(prev => ({ ...prev, [alertId]: true }));
    try {
      const res = await fetch(`${API_BASE}/investigations/run/${alertId}`, { method: 'POST' });
      if (res.ok) {
        showToast(`Investigation #${alertId} started successfully.`, 'success');
        fetchInvestigations();
      } else {
        showToast(`Investigation #${alertId} failed to run.`, 'error');
      }
    } catch (err) {
      console.error(err);
      showToast(`Error triggering investigation #${alertId}.`, 'error');
    } finally {
      setRunningAlerts(prev => ({ ...prev, [alertId]: false }));
    }
  };

  useEffect(() => {
    fetchEvents();
    fetchAlerts();
    fetchInvestigations();

    // Setup SSE
    const eventSource = new EventSource(`${API_BASE}/stream/`);

    eventSource.onopen = () => setSseConnected(true);

    eventSource.addEventListener('new_event', (e) => {
      const payload = JSON.parse(e.data);
      const newEvent = payload.data ? payload.data : payload; 
      setEvents(prev => {
        if (prev.find(p => p.id === newEvent.id)) return prev;
        return [newEvent, ...prev].slice(0, 50); 
      });
    });

    eventSource.addEventListener('new_alert', (e) => {
      const payload = JSON.parse(e.data);
      const newAlert = payload.data ? payload.data : payload;
      setAlerts(prev => {
        if (prev.find(p => p.id === newAlert.id)) return prev;
        return [newAlert, ...prev].slice(0, 50);
      });
    });

    eventSource.addEventListener('investigation_complete', (e) => {
      const payload = JSON.parse(e.data);
      const newInv = payload.data ? payload.data : payload;
      
      setInvestigations(prev => {
        if (prev.find(p => p.id === newInv.id)) return prev;
        return [newInv, ...prev].slice(0, 50);
      });

      showToast(`Investigation Complete - Risk: ${newInv.risk_score}, Action: ${newInv.recommended_action || 'None'}`, 'success');

      setRunningAlerts(prev => {
        const next = { ...prev };
        delete next[newInv.alert_id];
        return next;
      });
    });

    eventSource.addEventListener('ping', () => {
      setSseConnected(true);
    });

    eventSource.onerror = (err) => { 
      console.error('SSE Error:', err); 
      setSseConnected(false);
    };

    return () => eventSource.close();
  }, []);

  // Filtering Logic
  const filteredAlerts = useMemo(() => {
    return alerts.filter(a => {
      const matchesSearch = filters.search === '' || 
                            a.alert_type.toLowerCase().includes(filters.search.toLowerCase()) ||
                            a.id.toString().includes(filters.search);
      const matchesSeverity = filters.severity === 'ALL' || a.severity.toLowerCase() === filters.severity.toLowerCase();
      return matchesSearch && matchesSeverity;
    });
  }, [alerts, filters]);

  const filteredInvestigations = useMemo(() => {
    return investigations.filter(i => {
      const matchesSearch = filters.search === '' || 
                            (i.customer_id && i.customer_id.toLowerCase().includes(filters.search.toLowerCase())) ||
                            i.id.toString().includes(filters.search);
      // Derive risk severity for filtering
      let severity = 'low';
      if (i.risk_score >= 85) severity = 'critical';
      else if (i.risk_score >= 65) severity = 'high';
      else if (i.risk_score >= 35) severity = 'medium';
      
      const matchesSeverity = filters.severity === 'ALL' || severity === filters.severity.toLowerCase();
      return matchesSearch && matchesSeverity;
    });
  }, [investigations, filters]);

  const handleNavigate = (target) => {
    if (target === 'investigations') {
      setActiveTab('investigations');
      window.scrollTo({ top: 0, behavior: 'smooth' });
    } else {
      setActiveTab('dashboard');
      setTimeout(() => {
        if (target === 'events' && eventsRef.current) {
          eventsRef.current.scrollIntoView({ behavior: 'smooth' });
        } else if (target === 'alerts' && alertsRef.current) {
          alertsRef.current.scrollIntoView({ behavior: 'smooth' });
        }
      }, 100);
    }
  };

  return (
    <div className="app-container">
      <header className="top-nav">
        <div className="logo-section">
          <Shield className="logo-icon" size={28} />
          <h1>AI Threat Response</h1>
        </div>
        <nav className="nav-tabs">
          <button 
            className={`nav-btn ${activeTab === 'dashboard' ? 'active' : ''}`}
            onClick={() => setActiveTab('dashboard')}
          >
            <LayoutDashboard size={18} style={{ display: 'inline', marginRight: '6px', verticalAlign: 'text-bottom' }}/> Dashboard
          </button>
          <button 
            className={`nav-btn ${activeTab === 'investigations' ? 'active' : ''}`}
            onClick={() => setActiveTab('investigations')}
          >
            <Search size={18} style={{ display: 'inline', marginRight: '6px', verticalAlign: 'text-bottom' }}/> Investigations
          </button>
        </nav>
        <div className="status-indicator" style={{ color: sseConnected ? 'var(--risk-low)' : 'var(--risk-critical)' }}>
          <span className="pulse" style={{ background: sseConnected ? 'var(--risk-low)' : 'var(--risk-critical)', animation: sseConnected ? 'pulse 2s infinite' : 'none' }}></span> 
          {sseConnected ? <><Wifi size={16}/> Live Stream</> : <><WifiOff size={16}/> Disconnected</>}
        </div>
      </header>

      <main className="main-content">
        <SummaryCards events={events} alerts={alerts} investigations={investigations} onNavigate={handleNavigate} />
        
        {activeTab === 'dashboard' && (
          <>
            <Filters filters={filters} setFilters={setFilters} />
            <div className="dashboard-layout">
              <section className="glass-panel" ref={eventsRef}>
                <div className="panel-header">
                  <h2>Recent Login Activity</h2>
                  <button onClick={fetchEvents} className="btn btn-secondary" style={{ padding: '0.25rem 0.5rem', fontSize: '0.75rem' }}>Refresh</button>
                </div>
                <div className="table-responsive">
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th>ID</th><th>User</th><th>Type</th><th>IP Address</th><th>Time</th>
                      </tr>
                    </thead>
                    <tbody>
                      {events.slice(0, 10).map(evt => (
                        <tr key={evt.id}>
                          <td>#{evt.id}</td>
                          <td style={{ fontFamily: 'monospace' }}>{evt.user_id}</td>
                          <td><span className="badge status-new">{evt.event_type}</span></td>
                          <td style={{ fontFamily: 'monospace' }}>{evt.ip_address}</td>
                          <td style={{ color: 'var(--text-secondary)' }}>{new Date(evt.timestamp).toLocaleString()}</td>
                        </tr>
                      ))}
                      {events.length === 0 && (
                        <tr><td colSpan="5" style={{ textAlign: 'center', color: 'var(--text-muted)', padding: '2rem' }}>No events detected.</td></tr>
                      )}
                    </tbody>
                  </table>
                </div>
              </section>

              <section className="glass-panel" ref={alertsRef}>
                <div className="panel-header">
                  <h2>Active Alerts</h2>
                </div>
                <div className="feed-container">
                  {filteredAlerts.length > 0 ? filteredAlerts.slice(0, 15).map(alert => (
                    <AlertCard 
                      key={alert.id} 
                      alert={alert} 
                      onRunInvestigation={runInvestigation} 
                      isRunning={runningAlerts[alert.id]} 
                    />
                  )) : (
                    <div className="empty-state">No matching alerts.</div>
                  )}
                </div>
              </section>
            </div>
          </>
        )}

        {activeTab === 'investigations' && (
          <>
            <Filters filters={filters} setFilters={setFilters} />
            <section>
              <InvestigationTable 
                investigations={filteredInvestigations} 
                onSelect={setSelectedInvestigation} 
              />
            </section>
          </>
        )}
      </main>

      {selectedInvestigation && (
        <InvestigationModal 
          inv={selectedInvestigation} 
          onClose={() => setSelectedInvestigation(null)} 
        />
      )}

      {/* Toast Notifications container */}
      <div style={{ position: 'fixed', bottom: 0, right: 0, zIndex: 9999, display: 'flex', flexDirection: 'column', gap: '1rem', padding: '2rem' }}>
        {toasts.map(toast => (
          <div key={toast.id} style={{ position: 'relative' }}>
            <Toast message={toast.message} type={toast.type} onClose={() => removeToast(toast.id)} />
          </div>
        ))}
      </div>
    </div>
  );
}

export default App;
