import React, { useEffect } from 'react';
import { CheckCircle2, AlertTriangle, X } from 'lucide-react';

const Toast = ({ message, type = 'success', onClose, autoClose = 5000 }) => {
  useEffect(() => {
    if (autoClose) {
      const timer = setTimeout(onClose, autoClose);
      return () => clearTimeout(timer);
    }
  }, [autoClose, onClose]);

  const bgColor = type === 'success' ? 'var(--risk-low-bg)' : 'var(--risk-critical-bg)';
  const borderColor = type === 'success' ? 'rgba(16, 185, 129, 0.3)' : 'rgba(239, 68, 68, 0.3)';
  const iconColor = type === 'success' ? 'var(--risk-low)' : 'var(--risk-critical)';
  const Icon = type === 'success' ? CheckCircle2 : AlertTriangle;

  return (
    <div style={{
      position: 'fixed', bottom: '2rem', right: '2rem', zIndex: 9999,
      background: 'var(--bg-panel)', border: `1px solid ${borderColor}`,
      borderRadius: '8px', padding: '1rem', display: 'flex', alignItems: 'center', gap: '1rem',
      boxShadow: '0 10px 25px -5px rgba(0, 0, 0, 0.5)',
      animation: 'slideIn 0.3s cubic-bezier(0.16, 1, 0.3, 1)'
    }}>
      <div style={{ background: bgColor, padding: '0.5rem', borderRadius: '50%', display: 'flex' }}>
        <Icon color={iconColor} size={20} />
      </div>
      <div style={{ color: 'var(--text-primary)', fontSize: '0.9rem', fontWeight: 500 }}>
        {message}
      </div>
      <button onClick={onClose} style={{ background: 'none', border: 'none', color: 'var(--text-secondary)', cursor: 'pointer', marginLeft: '1rem' }}>
        <X size={16} />
      </button>
    </div>
  );
};

export default Toast;
