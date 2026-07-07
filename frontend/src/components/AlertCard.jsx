import React from 'react';
import { AlertCircle, Clock, CheckCircle, Activity, AlertTriangle } from 'lucide-react';

const ANOMALY_LABELS = {
  impossible_travel: 'Impossible Travel',
  new_device: 'New Device',
  new_location: 'New Location',
  unusual_time: 'Unusual Login Time',
  multiple_failed_logins: 'Multiple Failed Logins',
};

const AlertCard = ({ alert, onRunInvestigation, isRunning, customerMap, maskAccount }) => {
  const profile = customerMap?.[alert.event?.user_id];
  const customerName = profile?.full_name || alert.event?.user_id;

  // Extract behavioral analysis from raw_payload if available
  const behavioral = alert.event?.raw_payload?.behavioral_analysis;
  const anomalies = behavioral?.anomalies || [];
  const riskScore = behavioral?.risk_score;
  const riskLevel = behavioral?.risk_level;

  const getBadgeClass = (severity) => {
    switch(severity?.toLowerCase()) {
      case 'critical': return 'critical';
      case 'high': return 'high';
      case 'medium': return 'medium';
      case 'low': return 'low';
      default: return 'low';
    }
  };

  const getStatusClass = (status) => {
    return status === 'new' ? 'status-new' : 'status-investigating';
  };

  const riskColor = (level) => {
    switch (level) {
      case 'critical': return 'var(--risk-critical)';
      case 'high': return 'var(--risk-high)';
      case 'medium': return 'var(--risk-medium)';
      default: return 'var(--risk-low)';
    }
  };

  return (
    <div className={`alert-card ${getBadgeClass(alert.severity)}`}>
      <div className="alert-header">
        <div className="alert-title">#{alert.id} - {alert.alert_type.replace(/_/g, ' ')}</div>
        <span className={`badge ${getBadgeClass(alert.severity)}`}>
          {alert.severity}
        </span>
      </div>
      
      <div className="alert-meta" style={{ marginBottom: '0.5rem' }}>
        <div style={{ fontWeight: 500 }}>&#x1F464; {customerName}</div>
        <div style={{ fontSize: '0.75rem', fontFamily: 'monospace', color: 'var(--text-secondary)' }}>Customer ID: {alert.event?.user_id}</div>
        {profile?.account_number && <div style={{ fontSize: '0.75rem', fontFamily: 'monospace', color: 'var(--text-secondary)' }}>Account: {maskAccount(profile.account_number)}</div>}
      </div>

      {/* Behavioral Risk Badge */}
      {riskScore != null && (
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', marginBottom: '0.4rem', padding: '0.3rem 0.6rem', borderRadius: '12px', background: 'rgba(255,255,255,0.03)', border: `1px solid ${riskColor(riskLevel)}`, width: 'fit-content' }}>
          <AlertTriangle size={12} style={{ color: riskColor(riskLevel) }} />
          <span style={{ fontSize: '0.75rem', color: riskColor(riskLevel), fontWeight: 600, textTransform: 'capitalize' }}>
            Risk: {riskLevel} ({riskScore}/100)
          </span>
        </div>
      )}

      {/* Anomaly Tags */}
      {anomalies.length > 0 && (
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.3rem', marginBottom: '0.5rem' }}>
          {anomalies.map((a) => (
            <span key={a} style={{
              fontSize: '0.7rem',
              padding: '0.15rem 0.5rem',
              borderRadius: '10px',
              background: 'rgba(255,255,255,0.05)',
              border: '1px solid var(--border-glass)',
              color: 'var(--text-secondary)',
            }}>
              {ANOMALY_LABELS[a] || a}
            </span>
          ))}
        </div>
      )}

      <div className="alert-meta">
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
          <Activity size={12} /> Status: <span className={`badge ${getStatusClass(alert.status)}`}>{alert.status}</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
          <Clock size={12} /> {new Date(alert.created_at).toLocaleString()}
        </div>
      </div>
      
      <button 
        className="btn btn-secondary" 
        onClick={() => onRunInvestigation(alert.id)}
        disabled={isRunning}
        style={{ width: '100%', marginTop: '0.5rem' }}
      >
        {isRunning ? (
          <><div className="loader-spinner" style={{width: '14px', height: '14px', borderWidth: '2px'}}></div> Running...</>
        ) : (
          <><CheckCircle size={16} /> Run Investigation</>
        )}
      </button>
    </div>
  );
};

export default AlertCard;
