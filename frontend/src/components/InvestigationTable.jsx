import React, { useState } from 'react';
import { Shield, ChevronDown, ChevronUp } from 'lucide-react';
import RiskBar from './RiskBar';

const InvestigationTable = ({ investigations, onSelect, customerMap, maskAccount }) => {
  const [sortField, setSortField] = useState('id');
  const [sortAsc, setSortAsc] = useState(false);

  const handleSort = (field) => {
    if (sortField === field) {
      setSortAsc(!sortAsc);
    } else {
      setSortField(field);
      setSortAsc(false); // Default desc for new field
    }
  };

  const sortedData = [...investigations].sort((a, b) => {
    let valA = a[sortField];
    let valB = b[sortField];
    if (typeof valA === 'string') {
      valA = valA.toLowerCase();
      valB = valB?.toLowerCase() || '';
    }
    if (valA < valB) return sortAsc ? -1 : 1;
    if (valA > valB) return sortAsc ? 1 : -1;
    return 0;
  });

  const getRiskClass = (score) => {
    if (score >= 85) return 'critical';
    if (score >= 65) return 'high';
    if (score >= 35) return 'medium';
    return 'low';
  };

  const SortIcon = ({ field }) => {
    if (sortField !== field) return <span style={{ opacity: 0.3, marginLeft: '4px' }}>↕</span>;
    return sortAsc ? <ChevronUp size={14} style={{ display: 'inline', marginLeft: '4px' }}/> : <ChevronDown size={14} style={{ display: 'inline', marginLeft: '4px' }}/>;
  };

  return (
    <div className="table-responsive glass-panel" style={{ borderRadius: '12px', overflow: 'hidden' }}>
      <table className="data-table">
        <thead>
          <tr>
            <th onClick={() => handleSort('id')} style={{ cursor: 'pointer' }}>Investigation <SortIcon field="id"/></th>
            <th onClick={() => handleSort('customer_id')} style={{ cursor: 'pointer' }}>Customer <SortIcon field="customer_id"/></th>
            <th onClick={() => handleSort('risk_score')} style={{ cursor: 'pointer', width: '25%' }}>Risk Score <SortIcon field="risk_score"/></th>
            <th onClick={() => handleSort('confidence_score')} style={{ cursor: 'pointer' }}>Confidence <SortIcon field="confidence_score"/></th>
            <th onClick={() => handleSort('recommended_action')} style={{ cursor: 'pointer' }}>Action <SortIcon field="recommended_action"/></th>
            <th onClick={() => handleSort('created_at')} style={{ cursor: 'pointer' }}>Timestamp <SortIcon field="created_at"/></th>
          </tr>
        </thead>
        <tbody>
          {sortedData.map(inv => (
            <tr key={inv.id} onClick={() => onSelect(inv)} style={{ cursor: 'pointer' }}>
              <td>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <Shield size={14} style={{ color: `var(--risk-${getRiskClass(inv.risk_score)})` }} />
                  #{inv.id}
                </div>
              </td>
              <td>
                  <div style={{ fontWeight: 500 }}>👤 {customerMap?.[inv.customer_id]?.full_name || inv.customer_id}</div>
                  <div style={{ fontSize: '0.75rem', fontFamily: 'monospace', color: 'var(--text-secondary)' }}>Customer ID: {inv.customer_id}</div>
                  {customerMap?.[inv.customer_id]?.account_number && <div style={{ fontSize: '0.75rem', fontFamily: 'monospace', color: 'var(--text-secondary)' }}>Account: {maskAccount(customerMap[inv.customer_id].account_number)}</div>}
              </td>
              <td><RiskBar score={inv.risk_score} /></td>
              <td>{inv.confidence_score}%</td>
              <td style={{ color: 'var(--accent-blue)', fontWeight: 500 }}>{inv.recommended_action || 'N/A'}</td>
              <td style={{ color: 'var(--text-secondary)' }}>{new Date(inv.created_at).toLocaleString()}</td>
            </tr>
          ))}
          {sortedData.length === 0 && (
            <tr>
              <td colSpan="6" style={{ textAlign: 'center', padding: '3rem', color: 'var(--text-muted)' }}>
                No investigations found.
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
};

export default InvestigationTable;
