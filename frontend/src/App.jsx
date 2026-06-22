import { useState, useEffect } from 'react';
import './index.css';

const API_BASE = 'http://localhost:8000/api/v1';

function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [events, setEvents] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [investigations, setInvestigations] = useState([]);
  const [selectedInvestigation, setSelectedInvestigation] = useState(null);

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
    try {
      const res = await fetch(`${API_BASE}/investigations/run/${alertId}`, { method: 'POST' });
      if (res.ok) {
        alert('Investigation completed successfully!');
        fetchInvestigations();
      } else {
        alert('Investigation failed to run.');
      }
    } catch (err) {
      console.error(err);
      alert('Error triggering investigation.');
    }
  };

  useEffect(() => {
    fetchEvents();
    fetchAlerts();
    fetchInvestigations();

    // Setup SSE
    const eventSource = new EventSource(`${API_BASE}/stream/`);

    eventSource.addEventListener('new_event', (e) => {
      const payload = JSON.parse(e.data);
      const newEvent = payload.data ? payload.data : payload; // handle double wrapping
      setEvents(prev => {
        if (prev.find(p => p.id === newEvent.id)) return prev;
        return [newEvent, ...prev].slice(0, 50); // keep max 50 in state
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
    });

    eventSource.addEventListener('ping', () => {
      console.log('SSE ping received');
    });

    eventSource.onerror = (err) => {
      console.error('SSE Error:', err);
      // EventSource automatically reconnects
    };

    return () => {
      eventSource.close();
    };
  }, []);

  return (
    <div className="app-container">
      <header className="glass-panel">
        <div className="logo">
          <div className="logo-icon"></div>
          <h1>AI Banking Threat Response</h1>
        </div>
        <nav>
          <button 
            className={`nav-item ${activeTab === 'dashboard' ? 'active' : ''}`}
            onClick={() => setActiveTab('dashboard')}
          >
            Dashboard
          </button>
          <button 
            className={`nav-item ${activeTab === 'investigations' ? 'active' : ''}`}
            onClick={() => setActiveTab('investigations')}
          >
            Investigations
          </button>
        </nav>
        <div className="status-indicator">
          <span className="pulse"></span> System Active
        </div>
      </header>

      <main className="content">
        {activeTab === 'dashboard' && (
          <div className="dashboard-grid tab-content active">
            <section className="panel glass-panel">
              <div className="panel-header">
                <h2>Recent Logins & Events</h2>
                <button onClick={fetchEvents} className="icon-btn">↻</button>
              </div>
              <div className="table-container">
                <table>
                  <thead>
                    <tr>
                      <th>ID</th><th>User</th><th>Type</th><th>IP Address</th><th>Time</th>
                    </tr>
                  </thead>
                  <tbody>
                    {events.slice(0, 10).map(evt => (
                      <tr key={evt.id}>
                        <td>#{evt.id}</td>
                        <td>{evt.user_id}</td>
                        <td>{evt.event_type}</td>
                        <td>{evt.ip_address}</td>
                        <td>{new Date(evt.timestamp).toLocaleString()}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </section>

            <section className="panel glass-panel">
              <div className="panel-header">
                <h2>Active Alerts</h2>
                <button onClick={fetchAlerts} className="icon-btn">↻</button>
              </div>
              <div className="alerts-feed">
                {alerts.slice(0, 10).map(alert => (
                  <div key={alert.id} className="alert-card">
                    <div className="alert-header">
                      <strong>Alert #{alert.id} - {alert.alert_type}</strong>
                      <span className={`badge ${alert.severity.toLowerCase()}`}>{alert.severity}</span>
                    </div>
                    <div style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }}>
                      Status: {alert.status} | Created: {new Date(alert.created_at).toLocaleString()}
                    </div>
                    <button 
                      style={{ marginTop: '0.5rem', background: 'var(--bg-base)', border: '1px solid var(--border-glass)', color: 'var(--text-primary)', padding: '0.5rem', borderRadius: '6px', cursor: 'pointer' }}
                      onClick={() => runInvestigation(alert.id)}
                    >
                      Run Investigation
                    </button>
                  </div>
                ))}
              </div>
            </section>
          </div>
        )}

        {activeTab === 'investigations' && (
          <div className="tab-content active">
            <section className="panel glass-panel full-width">
              <div className="panel-header">
                <h2>Investigation History</h2>
                <button onClick={fetchInvestigations} className="icon-btn">↻</button>
              </div>
              <div className="investigations-grid">
                {investigations.map(inv => {
                  let badgeClass = 'low';
                  if (inv.risk_score >= 85) badgeClass = 'critical';
                  else if (inv.risk_score >= 65) badgeClass = 'high';
                  else if (inv.risk_score >= 35) badgeClass = 'medium';

                  return (
                    <div key={inv.id} className="investigation-card" onClick={() => setSelectedInvestigation(inv)}>
                      <div className="alert-header">
                        <strong>Inv #{inv.id} (Alert #{inv.alert_id})</strong>
                        <span className={`badge ${badgeClass}`}>Risk: {inv.risk_score}</span>
                      </div>
                      <div style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }}>
                        Customer: {inv.customer_id}
                      </div>
                      <div className="action">
                        Action: {inv.recommended_action}
                      </div>
                    </div>
                  );
                })}
              </div>
            </section>
          </div>
        )}
      </main>

      {selectedInvestigation && (
        <InvestigationModal 
          inv={selectedInvestigation} 
          onClose={() => setSelectedInvestigation(null)} 
        />
      )}
    </div>
  );
}

function InvestigationModal({ inv, onClose }) {
  let badgeClass = 'low';
  let riskLevel = 'LOW';
  if (inv.risk_score >= 85) { badgeClass = 'critical'; riskLevel = 'CRITICAL'; }
  else if (inv.risk_score >= 65) { badgeClass = 'high'; riskLevel = 'HIGH'; }
  else if (inv.risk_score >= 35) { badgeClass = 'medium'; riskLevel = 'MEDIUM'; }

  let reasoning = "No reasoning provided.";
  if (inv.reasoning_trace) {
    const llmTrace = inv.reasoning_trace.find(t => t.includes("LLM Reasoning:"));
    if (llmTrace) reasoning = llmTrace.replace("LLM Reasoning: ", "");
  }

  return (
    <div className="modal" onClick={onClose}>
      <div className="modal-content glass-panel" onClick={e => e.stopPropagation()}>
        <span className="close-modal" onClick={onClose}>&times;</span>
        <div className="modal-header">
          <h2>Investigation Details <span className={`badge ${badgeClass}`}>{riskLevel}</span></h2>
          <div className="modal-scores">
            <div className="score-card">
              <span className="label">Risk Score</span>
              <span className="value">{inv.risk_score}</span>
            </div>
            <div className="score-card">
              <span className="label">Confidence</span>
              <span className="value">{inv.confidence_score}%</span>
            </div>
          </div>
        </div>
        
        <div className="modal-body">
          <div className="section-block" style={{ marginBottom: '1.5rem' }}>
            <h3>Action Recommended</h3>
            <div className="action-block">{inv.recommended_action}</div>
          </div>
          
          <div className="section-block" style={{ marginBottom: '1.5rem' }}>
            <h3>Analyst Reasoning</h3>
            <p className="reasoning-text">{reasoning}</p>
          </div>
          
          <div className="section-block">
            <h3>Reasoning Trace</h3>
            <ul className="trace-list">
              {inv.reasoning_trace && inv.reasoning_trace.map((trace, i) => (
                <li key={i}>{trace}</li>
              ))}
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;
