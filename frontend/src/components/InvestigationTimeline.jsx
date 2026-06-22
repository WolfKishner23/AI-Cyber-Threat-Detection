import React from 'react';
import { Shield, ArrowRight, User, AlertOctagon } from 'lucide-react';

const InvestigationTimeline = ({ investigations, onSelect }) => {
  const getRiskClass = (score) => {
    if (score >= 85) return 'critical';
    if (score >= 65) return 'high';
    if (score >= 35) return 'medium';
    return 'low';
  };

  return (
    <div className="investigations-grid">
      {investigations.map(inv => (
        <div key={inv.id} className="investigation-card glass-panel" onClick={() => onSelect(inv)}>
          <div className="alert-header">
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <Shield size={16} className={`logo-icon`} style={{ color: `var(--risk-${getRiskClass(inv.risk_score)})` }} />
              <strong style={{ fontSize: '1rem' }}>Investigation #{inv.id}</strong>
            </div>
            <span className={`badge ${getRiskClass(inv.risk_score)}`}>Risk: {inv.risk_score}</span>
          </div>
          
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', marginTop: '0.5rem', flex: 1 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--text-secondary)', fontSize: '0.875rem' }}>
              <User size={14} /> Customer: <span style={{ color: 'var(--text-primary)' }}>{inv.customer_id}</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--text-secondary)', fontSize: '0.875rem' }}>
              <AlertOctagon size={14} /> Alert ID: <span style={{ color: 'var(--text-primary)' }}>#{inv.alert_id}</span>
            </div>
          </div>
          
          <div style={{ marginTop: '1rem', paddingTop: '1rem', borderTop: '1px solid var(--border-glass)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
              <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', textTransform: 'uppercase' }}>Action Taken</span>
              <span style={{ color: 'var(--accent-blue)', fontWeight: 600, fontSize: '0.875rem', fontFamily: 'monospace' }}>
                {inv.recommended_action || 'N/A'}
              </span>
            </div>
            <ArrowRight size={16} color="var(--text-muted)" />
          </div>
        </div>
      ))}
      
      {investigations.length === 0 && (
        <div className="empty-state glass-panel" style={{ gridColumn: '1 / -1' }}>
          <Shield size={48} opacity={0.5} />
          <h3>No Investigations Found</h3>
          <p>Adjust your filters or wait for new alerts to be processed.</p>
        </div>
      )}
    </div>
  );
};

export default InvestigationTimeline;
