import { useState } from 'react';
import { Landmark, Eye, EyeOff, CheckCircle2, ShieldAlert, XCircle, Loader2, AlertTriangle } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import './index.css';

const API_BASE = 'http://localhost:8001/api/v1';

const AUTH_STEPS = [
  'Authenticating...',
  'Verifying Credentials...',
  'Checking Device...',
  'Checking Login Security...',
];

const ANOMALY_LABELS = {
  impossible_travel: 'Impossible Travel Detected',
  new_device: 'Unknown Device',
  new_location: 'New Login Location',
  unusual_time: 'Unusual Login Time',
  multiple_failed_logins: 'Multiple Failed Attempts',
};

function Login() {
  const navigate = useNavigate();

  const [form, setForm] = useState({
    customerId: '',
    password: '',
    location: 'Mumbai',
    rememberMe: false,
  });
  const [showPassword, setShowPassword] = useState(false);

  // loginState: 'idle' | 'processing' | 'success' | 'verification' | 'error'
  const [loginState, setLoginState] = useState('idle');
  const [stepText, setStepText] = useState(AUTH_STEPS[0]);
  const [customerData, setCustomerData] = useState(null);
  const [errorMsg, setErrorMsg] = useState('');

  const locations = [
    'Mumbai', 'Delhi', 'Bangalore', 'Hyderabad',
    'Chennai', 'Pune', 'Kolkata', 'London',
    'New York', 'Singapore', 'Dubai',
    'North Sentinel Island', 'Pyongyang, North Korea', 'Juba, South Sudan'
  ];

  const runStepAnimation = () => {
    let step = 0;
    const interval = setInterval(() => {
      step++;
      if (step < AUTH_STEPS.length) {
        setStepText(AUTH_STEPS[step]);
      } else {
        clearInterval(interval);
      }
    }, 600);
    return interval;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoginState('processing');
    setStepText(AUTH_STEPS[0]);
    setErrorMsg('');

    const animInterval = runStepAnimation();

    try {
      const res = await fetch(`${API_BASE}/customer/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          customer_id: form.customerId,
          password: form.password,
          location: form.location,
        }),
      });

      // Keep animation running for ~2.5s for realistic feel
      await new Promise((r) => setTimeout(r, 2500));
      clearInterval(animInterval);

      if (res.status === 401) {
        const data = await res.json();
        const attempts = data.detail?.attempts_remaining;
        if (attempts !== undefined) {
          setErrorMsg(`Invalid Customer ID or Password. Attempts Remaining: ${attempts}`);
        } else {
          setErrorMsg('Invalid Customer ID or Password');
        }
        setLoginState('error');
        return;
      }

      if (!res.ok) {
        setErrorMsg('An unexpected error occurred. Please try again.');
        setLoginState('error');
        return;
      }

      const data = await res.json();
      setCustomerData(data);

      // Use the behavioral risk data from the backend response
      if (data.risk_level === 'high' || data.risk_level === 'critical') {
        setLoginState('verification');
      } else {
        setLoginState('success');
      }

    } catch (err) {
      clearInterval(animInterval);
      setErrorMsg('Could not connect to the server. Is the backend running?');
      setLoginState('error');
    }
  };

  const maskedAccount = (acct) =>
    acct ? 'XXXX' + acct.slice(-4) : 'XXXX0000';

  const riskColor = (level) => {
    switch (level) {
      case 'critical': return 'var(--risk-critical)';
      case 'high': return 'var(--risk-high)';
      case 'medium': return 'var(--risk-medium)';
      default: return 'var(--risk-low)';
    }
  };

  /* ── Processing Screen ──────────────────────────────────────────────────── */
  if (loginState === 'processing') {
    return (
      <div className="app-container" style={{ justifyContent: 'center', alignItems: 'center' }}>
        <div className="glass-panel" style={cardStyle}>
          <BankHeader />
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '2rem', padding: '3rem 0' }}>
            <Loader2 size={52} style={{ color: 'var(--accent-blue)', animation: 'spin 1s linear infinite' }} />
            <p style={{ fontSize: '1.15rem', color: 'var(--text-primary)', minHeight: '1.8rem', textAlign: 'center' }}>
              {stepText}
            </p>
          </div>
        </div>
      </div>
    );
  }

  /* ── Success Screen ─────────────────────────────────────────────────────── */
  if (loginState === 'success') {
    const score = customerData?.risk_score ?? 0;
    const level = customerData?.risk_level ?? 'low';
    const anomalies = customerData?.anomalies ?? [];

    return (
      <div className="app-container" style={{ justifyContent: 'center', alignItems: 'center' }}>
        <div className="glass-panel" style={cardStyle}>
          <BankHeader />
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '1.25rem', padding: '1rem 0' }}>
            <CheckCircle2 size={60} style={{ color: 'var(--risk-low)' }} />
            <h2 style={{ fontSize: '1.5rem', color: 'var(--text-primary)' }}>Login Successful</h2>
            <p style={{ fontSize: '1.15rem', color: 'var(--text-primary)', textAlign: 'center' }}>
              Welcome, {customerData?.customer_name}
            </p>
            <div style={infoBox}>
              <p style={mutedLabel}>Account</p>
              <p style={infoValue}>{maskedAccount(customerData?.account_number)}</p>
              <p style={{ ...mutedLabel, marginTop: '0.5rem' }}>Location</p>
              <p style={infoValue}>{form.location}</p>
            </div>

            {/* Risk Summary Badge */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', padding: '0.5rem 1rem', borderRadius: '20px', background: 'rgba(255,255,255,0.04)', border: `1px solid ${riskColor(level)}` }}>
              <div style={{ width: 8, height: 8, borderRadius: '50%', background: riskColor(level) }} />
              <span style={{ fontSize: '0.85rem', color: riskColor(level), textTransform: 'capitalize' }}>
                Risk: {level} ({score}/100)
              </span>
            </div>

            {anomalies.length > 0 && (
              <div style={{ width: '100%', padding: '0.75rem', borderRadius: '8px', background: 'rgba(255,255,255,0.03)', fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                <p style={{ fontWeight: 600, marginBottom: '0.3rem', color: 'var(--text-primary)' }}>Findings:</p>
                {anomalies.map((a) => (
                  <p key={a} style={{ margin: '0.15rem 0' }}>
                    - {ANOMALY_LABELS[a] || a}
                  </p>
                ))}
              </div>
            )}

            <button
              className="btn btn-primary"
              onClick={() => navigate('/')}
              style={{ width: '100%', padding: '0.85rem', marginTop: '0.25rem' }}
            >
              Return to Home
            </button>
          </div>
        </div>
      </div>
    );
  }

  /* ── Verification Screen (high/critical risk) ───────────────────────────── */
  if (loginState === 'verification') {
    const score = customerData?.risk_score ?? 0;
    const level = customerData?.risk_level ?? 'high';
    const anomalies = customerData?.anomalies ?? [];

    return (
      <div className="app-container" style={{ justifyContent: 'center', alignItems: 'center' }}>
        <div className="glass-panel" style={cardStyle}>
          <BankHeader />
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '1.25rem', padding: '1rem 0', textAlign: 'center' }}>
            <ShieldAlert size={60} style={{ color: riskColor(level) }} />
            <h2 style={{ fontSize: '1.35rem', color: riskColor(level) }}>
              Additional Verification Required
            </h2>
            <p style={{ color: 'var(--text-secondary)', lineHeight: '1.6' }}>
              Suspicious login activity detected.<br />
              An OTP has been sent to your registered device.
            </p>

            {/* Show detected anomalies */}
            <div style={{ width: '100%', padding: '0.75rem', borderRadius: '8px', background: 'rgba(255,80,80,0.06)', border: '1px solid rgba(255,80,80,0.15)', textAlign: 'left' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', marginBottom: '0.4rem' }}>
                <AlertTriangle size={14} style={{ color: riskColor(level) }} />
                <span style={{ fontWeight: 600, fontSize: '0.85rem', color: riskColor(level) }}>
                  Risk Score: {score}/100 ({level})
                </span>
              </div>
              {anomalies.map((a) => (
                <p key={a} style={{ margin: '0.15rem 0', fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                  - {ANOMALY_LABELS[a] || a}
                </p>
              ))}
            </div>

            <input type="text" maxLength={6} placeholder="Enter 6-digit OTP" style={otpInput} />
            <button
              className="btn btn-primary"
              style={{ width: '100%', padding: '0.85rem' }}
              onClick={() => setLoginState('success')}
            >
              Verify OTP
            </button>
            <button
              className="btn btn-secondary"
              style={{ width: '100%', padding: '0.85rem' }}
              onClick={() => setLoginState('idle')}
            >
              Cancel
            </button>
          </div>
        </div>
      </div>
    );
  }

  /* ── Error Screen ───────────────────────────────────────────────────────── */
  if (loginState === 'error') {
    return (
      <div className="app-container" style={{ justifyContent: 'center', alignItems: 'center' }}>
        <div className="glass-panel" style={cardStyle}>
          <BankHeader />
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '1.5rem', padding: '2rem 0', textAlign: 'center' }}>
            <XCircle size={64} style={{ color: 'var(--risk-high)' }} />
            <h2 style={{ fontSize: '1.4rem', color: 'var(--risk-high)' }}>Authentication Failed</h2>
            <p style={{ color: 'var(--text-secondary)', lineHeight: '1.6' }}>{errorMsg}</p>
            <button className="btn btn-primary" style={{ width: '100%', padding: '0.85rem' }} onClick={() => setLoginState('idle')}>
              Try Again
            </button>
            <button className="btn btn-secondary" style={{ width: '100%', padding: '0.85rem' }} onClick={() => navigate('/')}>
              Back to Home
            </button>
          </div>
        </div>
      </div>
    );
  }

  /* ── Login Form (idle) ──────────────────────────────────────────────────── */
  return (
    <div className="app-container" style={{ justifyContent: 'center', alignItems: 'center' }}>
      <div className="glass-panel" style={cardStyle}>
        <BankHeader />
        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1.4rem' }}>
          <div style={fieldGroup}>
            <label style={fieldLabel}>Customer ID</label>
            <input type="text" required placeholder="e.g. CUST1001" style={fieldInput}
              value={form.customerId}
              onChange={(e) => setForm({ ...form, customerId: e.target.value })}
            />
          </div>
          <div style={fieldGroup}>
            <label style={fieldLabel}>Password</label>
            <div style={{ position: 'relative', display: 'flex', alignItems: 'center' }}>
              <input type={showPassword ? 'text' : 'password'} required
                style={{ ...fieldInput, paddingRight: '2.75rem' }}
                value={form.password}
                onChange={(e) => setForm({ ...form, password: e.target.value })}
              />
              <button type="button" onClick={() => setShowPassword(!showPassword)} style={eyeBtn} tabIndex={-1}>
                {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
              </button>
            </div>
          </div>
          <div style={fieldGroup}>
            <label style={fieldLabel}>Location</label>
            <select style={fieldInput} value={form.location}
              onChange={(e) => setForm({ ...form, location: e.target.value })}
            >
              {locations.map((loc) => (
                <option key={loc} value={loc} style={{ background: 'var(--bg-panel)' }}>{loc}</option>
              ))}
            </select>
          </div>
          <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.875rem', color: 'var(--text-secondary)', cursor: 'pointer' }}>
            <input type="checkbox" checked={form.rememberMe}
              onChange={(e) => setForm({ ...form, rememberMe: e.target.checked })}
            />
            Remember Me
          </label>
          <button type="submit" className="btn btn-primary" style={{ padding: '0.9rem', fontSize: '1rem' }}>
            Secure Login
          </button>
          <button type="button" className="btn btn-secondary" onClick={() => navigate('/')} style={{ padding: '0.9rem' }}>
            Back
          </button>
        </form>
      </div>
    </div>
  );
}

function BankHeader() {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '0.4rem', marginBottom: '2rem' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', color: 'var(--accent-blue)' }}>
        <Landmark size={36} />
        <h1 style={{ fontSize: '1.75rem', fontWeight: 700 }}>AI Secure Bank</h1>
      </div>
      <h2 style={{ fontSize: '1rem', color: 'var(--text-secondary)', fontWeight: 400 }}>Customer Login</h2>
    </div>
  );
}

const cardStyle = { padding: '3rem', width: '100%', maxWidth: '450px', minHeight: '540px', display: 'flex', flexDirection: 'column' };
const fieldGroup = { display: 'flex', flexDirection: 'column', gap: '0.45rem' };
const fieldLabel = { fontSize: '0.9rem', color: 'var(--text-secondary)' };
const fieldInput = { background: 'rgba(255,255,255,0.05)', border: '1px solid var(--border-glass)', padding: '0.85rem', borderRadius: '6px', color: 'var(--text-primary)', outline: 'none', fontSize: '1rem', width: '100%' };
const eyeBtn = { position: 'absolute', right: '0.75rem', background: 'none', border: 'none', color: 'var(--text-secondary)', cursor: 'pointer', display: 'flex', alignItems: 'center' };
const infoBox = { background: 'rgba(255,255,255,0.03)', padding: '1rem 1.5rem', borderRadius: '8px', width: '100%', textAlign: 'center' };
const mutedLabel = { fontSize: '0.8rem', color: 'var(--text-muted)', margin: 0 };
const infoValue = { fontSize: '1rem', color: 'var(--text-primary)', margin: '0.2rem 0 0' };
const otpInput = { background: 'rgba(255,255,255,0.05)', border: '1px solid var(--border-glass)', padding: '0.85rem', borderRadius: '6px', color: 'var(--text-primary)', outline: 'none', fontSize: '1.2rem', width: '100%', textAlign: 'center', letterSpacing: '0.4em' };

export default Login;
