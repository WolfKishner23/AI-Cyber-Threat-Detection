import React from 'react';

const RiskBar = ({ score }) => {
  let color = 'var(--risk-low)';
  if (score >= 85) color = 'var(--risk-critical)';
  else if (score >= 65) color = 'var(--risk-high)';
  else if (score >= 35) color = 'var(--risk-medium)';

  return (
    <div className="risk-bar-container" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', width: '100%' }}>
      <div style={{ flex: 1, height: '6px', background: 'var(--border-glass)', borderRadius: '3px', overflow: 'hidden' }}>
        <div style={{ width: `${score}%`, height: '100%', background: color, transition: 'width 0.5s ease-in-out' }} />
      </div>
      <span style={{ fontSize: '0.875rem', fontWeight: 600, color, minWidth: '24px', textAlign: 'right' }}>{score}</span>
    </div>
  );
};

export default RiskBar;
