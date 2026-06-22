import React from 'react';
import { Activity, AlertTriangle, ShieldAlert, BarChart3 } from 'lucide-react';

const SummaryCards = ({ events, alerts, investigations, onNavigate }) => {
  const activeAlerts = alerts.filter(a => a.status === 'new' || a.status === 'investigating').length;
  const highRiskInvs = investigations.filter(i => i.risk_score >= 65).length;
  
  const totalRisk = investigations.reduce((acc, curr) => acc + curr.risk_score, 0);
  const avgRisk = investigations.length > 0 ? Math.round(totalRisk / investigations.length) : 0;

  // Banking-specific metrics
  const fraudAttemptsPrevented = investigations.filter(i => 
    i.recommended_action && (i.recommended_action.toLowerCase().includes('lock') || i.recommended_action.toLowerCase().includes('block'))
  ).length;

  const uniqueUsers = new Set(events.map(e => e.user_id)).size;

  return (
    <div className="summary-grid">
      <div className="summary-card glass-panel interactive-card" onClick={() => onNavigate('events')} role="button" tabIndex={0}>
        <Activity className="icon-wrapper" size={48} />
        <span className="summary-title">Accounts Protected Today</span>
        <span className="summary-value">{uniqueUsers}</span>
        <span className="summary-trend" style={{ color: 'var(--text-secondary)' }}>Based on {events.length} Logins</span>
      </div>
      
      <div className="summary-card glass-panel interactive-card" onClick={() => onNavigate('alerts')} role="button" tabIndex={0}>
        <AlertTriangle className="icon-wrapper" size={48} color="var(--risk-high)" />
        <span className="summary-title">Active Alerts</span>
        <span className="summary-value" style={{ color: activeAlerts > 0 ? 'var(--risk-high)' : 'inherit' }}>
          {activeAlerts}
        </span>
        <span className="summary-trend" style={{ color: 'var(--text-secondary)' }}>Pending response</span>
      </div>
      
      <div className="summary-card glass-panel interactive-card" onClick={() => onNavigate('investigations')} role="button" tabIndex={0}>
        <ShieldAlert className="icon-wrapper" size={48} color="var(--risk-critical)" />
        <span className="summary-title">High-Risk Inv.</span>
        <span className="summary-value" style={{ color: highRiskInvs > 0 ? 'var(--risk-critical)' : 'inherit' }}>
          {highRiskInvs}
        </span>
        <span className="summary-trend" style={{ color: 'var(--text-secondary)' }}>Score &ge; 65</span>
      </div>
      
      <div className="summary-card glass-panel interactive-card" onClick={() => onNavigate('investigations')} role="button" tabIndex={0}>
        <BarChart3 className="icon-wrapper" size={48} color="var(--risk-low)" />
        <span className="summary-title">Fraud Prevented</span>
        <span className="summary-value" style={{ color: 'var(--risk-low)' }}>{fraudAttemptsPrevented}</span>
        <span className="summary-trend" style={{ color: 'var(--text-secondary)' }}>Avg Risk: {avgRisk}</span>
      </div>
    </div>
  );
};

export default SummaryCards;
