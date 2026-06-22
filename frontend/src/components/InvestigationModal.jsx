import React, { useState } from 'react';
import { X, ShieldAlert, Cpu, Database, ChevronDown, ChevronRight, CheckCircle2 } from 'lucide-react';
import ProgressIndicator from './ProgressIndicator';
import RiskBar from './RiskBar';

const InvestigationModal = ({ inv, onClose }) => {
  const [openSection, setOpenSection] = useState('summary');
  
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

  const toggleSection = (sec) => {
    setOpenSection(openSection === sec ? '' : sec);
  };

  // Format the AI summary using regex to create bullet points if it's a block of text
  const formatSummary = (text) => {
    if (!text) return <p>No summary available.</p>;
    
    // Simple parsing: split by newlines or sentences if no newlines
    const lines = text.split(/\n+/).filter(l => l.trim().length > 0);
    return (
      <ul style={{ listStyleType: 'none', padding: 0, margin: 0, display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
        {lines.map((line, idx) => {
          const isHighlight = line.toLowerCase().includes('recommended action') || line.toLowerCase().includes('conclusion');
          return (
            <li key={idx} style={{ 
              display: 'flex', 
              gap: '0.75rem', 
              alignItems: 'flex-start',
              padding: isHighlight ? '1rem' : '0.5rem',
              background: isHighlight ? 'rgba(59, 130, 246, 0.1)' : 'transparent',
              borderRadius: '6px',
              borderLeft: isHighlight ? '3px solid var(--accent-blue)' : 'none',
              fontWeight: isHighlight ? 600 : 400
            }}>
              {!isHighlight && <CheckCircle2 size={16} color="var(--risk-low)" style={{ marginTop: '2px', flexShrink: 0 }} />}
              <span style={{ lineHeight: 1.5 }}>{line.replace(/^-\s*/, '')}</span>
            </li>
          );
        })}
      </ul>
    );
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
            <ShieldAlert size={28} style={{ color: `var(--risk-${badgeClass})` }} />
            <div>
              <h2 style={{ fontSize: '1.25rem', marginBottom: '0.25rem' }}>
                Investigation #{inv.id}
                <span className={`badge ${badgeClass}`} style={{ marginLeft: '1rem' }}>{riskLevel}</span>
              </h2>
              <span style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }}>
                Customer ID: {inv.customer_id} • Alert ID: #{inv.alert_id} • Generated {new Date(inv.created_at).toLocaleString()}
              </span>
            </div>
          </div>
          <button className="icon-btn" onClick={onClose}><X size={24} /></button>
        </div>
        
        <div className="modal-body">
          <ProgressIndicator />
          
          <div className="modal-scores" style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)' }}>
            <div className="score-card">
              <span className="label" style={{ marginBottom: '0.5rem' }}>Risk Score</span>
              <RiskBar score={inv.risk_score} />
            </div>
            <div className="score-card">
              <span className="label" style={{ marginBottom: '0.5rem' }}>Confidence</span>
              <RiskBar score={inv.confidence_score} />
            </div>
            <div className="score-card" style={{ background: 'rgba(59, 130, 246, 0.1)', border: '1px solid rgba(59, 130, 246, 0.2)' }}>
              <span className="label" style={{ color: 'var(--accent-blue)' }}>Recommended Action</span>
              <span className="value" style={{ fontSize: '1.25rem', fontFamily: 'monospace' }}>{inv.recommended_action}</span>
            </div>
          </div>

          <div className="accordion">
            <summary onClick={() => toggleSection('summary')}>
              {openSection === 'summary' ? <ChevronDown size={18}/> : <ChevronRight size={18}/>}
              <CheckCircle2 size={18} color="var(--risk-low)"/> AI Investigation Summary
            </summary>
            {openSection === 'summary' && (
              <div className="accordion-content">
                {formatSummary(inv.investigation_summary)}
              </div>
            )}
          </div>

          <div className="accordion">
            <summary onClick={() => toggleSection('reasoning')}>
              {openSection === 'reasoning' ? <ChevronDown size={18}/> : <ChevronRight size={18}/>}
              <Cpu size={18} color="var(--accent-purple)"/> AI Reasoning & Trace
            </summary>
            {openSection === 'reasoning' && (
              <div className="accordion-content">
                <div style={{ marginBottom: '1.5rem' }}>
                  <h4 style={{ color: 'var(--text-secondary)', marginBottom: '0.5rem', textTransform: 'uppercase', fontSize: '0.75rem' }}>Final Analyst Reasoning</h4>
                  <p className="reasoning-text">{reasoning}</p>
                </div>
                <div>
                  <h4 style={{ color: 'var(--text-secondary)', marginBottom: '0.5rem', textTransform: 'uppercase', fontSize: '0.75rem' }}>Execution Trace</h4>
                  <ul className="trace-list">
                    {inv.reasoning_trace?.map((trace, i) => (
                      <li key={i}>{trace}</li>
                    ))}
                  </ul>
                </div>
              </div>
            )}
          </div>

          <div className="accordion">
            <summary onClick={() => toggleSection('evidence')}>
              {openSection === 'evidence' ? <ChevronDown size={18}/> : <ChevronRight size={18}/>}
              <Database size={18} color="var(--accent-blue)"/> Raw Evidence & Tool Outputs
            </summary>
            {openSection === 'evidence' && (
              <div className="accordion-content">
                <pre>{JSON.stringify(inv.evidence, null, 2)}</pre>
              </div>
            )}
          </div>

        </div>
      </div>
    </div>
  );
};

export default InvestigationModal;
