import { Shield, User } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import './index.css';

function Landing() {
  const navigate = useNavigate();

  return (
    <div className="app-container" style={{ justifyContent: 'center', alignItems: 'center' }}>
      <div className="glass-panel" style={{ padding: '3rem', textAlign: 'center', maxWidth: '800px', width: '100%' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '1rem', marginBottom: '2rem' }}>
          <Shield className="logo-icon" size={48} />
          <h1 style={{ fontSize: '2.5rem' }}>AI Threat Response</h1>
        </div>
        
        <p style={{ color: 'var(--text-secondary)', marginBottom: '3rem', fontSize: '1.1rem' }}>
          Welcome to the Secure Banking Portal. Please select your login type below.
        </p>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '2rem' }}>
          <div 
            className="summary-card glass-panel interactive-card" 
            onClick={() => navigate('/login')}
          >
            <div className="icon-wrapper" style={{ opacity: 1, color: 'var(--accent-purple)' }}>
              <User size={32} />
            </div>
            <h2 style={{ fontSize: '1.5rem', marginTop: '1rem' }}>Customer Login</h2>
            <p style={{ color: 'var(--text-secondary)', marginTop: '0.5rem' }}>
              Access your secure personal banking dashboard.
            </p>
          </div>

          <div 
            className="summary-card glass-panel interactive-card"
            onClick={() => navigate('/dashboard')}
          >
            <div className="icon-wrapper" style={{ opacity: 1, color: 'var(--accent-blue)' }}>
              <Shield size={32} />
            </div>
            <h2 style={{ fontSize: '1.5rem', marginTop: '1rem' }}>Security Analyst</h2>
            <p style={{ color: 'var(--text-secondary)', marginTop: '0.5rem' }}>
              Access the threat response and monitoring dashboard.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Landing;
