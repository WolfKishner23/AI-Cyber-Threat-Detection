import React from 'react';
import { Check, Loader2 } from 'lucide-react';

const STEPS = [
  "Login Event",
  "Detection",
  "Evidence Collection",
  "Risk Assessment",
  "Response Planning",
  "Completed"
];

const ProgressIndicator = () => {
  // All steps are complete for historic investigations as per requirements
  return (
    <div className="progress-track" style={{ marginBottom: '3rem' }}>
      {STEPS.map((step, idx) => {
        const isCompleted = true; 
        return (
          <div key={idx} className="progress-step">
            <div className={`step-circle ${isCompleted ? 'completed' : ''}`}>
              {isCompleted ? <Check size={14} /> : <Loader2 size={14} className="loader-spinner" style={{border: 'none'}}/>}
            </div>
            <span className="step-label" style={{ position: 'absolute', top: '32px', whiteSpace: 'nowrap', textAlign: 'center' }}>
              {step}
            </span>
          </div>
        );
      })}
    </div>
  );
};

export default ProgressIndicator;
