import React from 'react';
import { Search, Filter } from 'lucide-react';

const Filters = ({ filters, setFilters }) => {
  const handleChange = (e) => {
    const { name, value } = e.target;
    setFilters(prev => ({ ...prev, [name]: value }));
  };

  return (
    <div className="glass-panel" style={{ padding: '1rem', display: 'flex', gap: '1rem', alignItems: 'center', flexWrap: 'wrap' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--text-secondary)' }}>
        <Filter size={18} />
        <span style={{ fontSize: '0.875rem', fontWeight: 500, textTransform: 'uppercase' }}>Filters</span>
      </div>
      
      <div style={{ display: 'flex', flex: 1, minWidth: '200px', background: 'rgba(0,0,0,0.2)', borderRadius: '6px', padding: '0.5rem 1rem', border: '1px solid var(--border-glass)', alignItems: 'center', gap: '0.5rem' }}>
        <Search size={16} color="var(--text-secondary)" />
        <input 
          type="text" 
          name="search" 
          placeholder="Search Customer ID or Alert Type..." 
          value={filters.search}
          onChange={handleChange}
          style={{ background: 'transparent', border: 'none', color: 'white', outline: 'none', width: '100%', fontSize: '0.875rem' }}
        />
      </div>

      <select 
        name="severity" 
        value={filters.severity} 
        onChange={handleChange}
        style={{ background: 'rgba(0,0,0,0.2)', border: '1px solid var(--border-glass)', color: 'white', padding: '0.5rem', borderRadius: '6px', outline: 'none' }}
      >
        <option value="ALL">All Severities</option>
        <option value="critical">Critical</option>
        <option value="high">High</option>
        <option value="medium">Medium</option>
        <option value="low">Low</option>
      </select>
    </div>
  );
};

export default Filters;
