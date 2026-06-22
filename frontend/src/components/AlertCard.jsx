import React from 'react';
import { AlertCircle, Clock, CheckCircle, Activity } from 'lucide-react';

const AlertCard = ({ alert, onRunInvestigation, isRunning }) => {
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

  return (
    <div className={`alert-card ${getBadgeClass(alert.severity)}`}>
      <div className="alert-header">
        <div className="alert-title">#{alert.id} - {alert.alert_type}</div>
        <span className={`badge ${getBadgeClass(alert.severity)}`}>
          {alert.severity}
        </span>
      </div>
      
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
