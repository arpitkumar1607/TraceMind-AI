import React, { useEffect, useState } from 'react';
import { api } from '../api';
import { AlertOctagon, Eye, RefreshCw, CheckCircle, ShieldAlert } from 'lucide-react';

export default function IncidentManagement({ onSelectIncident, onNavigate }) {
  const [incidents, setIncidents] = useState([]);
  const [filter, setFilter] = useState('ALL');
  const [loading, setLoading] = useState(true);

  const fetchIncidents = async () => {
    try {
      const data = await api.getIncidents();
      setIncidents(data || []);
    } catch (err) {
      console.error("Error loading incidents", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchIncidents();
    const interval = setInterval(fetchIncidents, 4000);
    return () => clearInterval(interval);
  }, []);

  const filteredIncidents = incidents.filter((inc) => {
    if (filter === 'ACTIVE') return inc.status !== 'Resolved' && inc.status !== 'Failed';
    if (filter === 'RESOLVED') return inc.status === 'Resolved';
    if (filter === 'APPROVAL') return inc.status === 'Awaiting Approval';
    return true;
  });

  return (
    <div className="card">
      <div className="card-title" style={{ justifyContent: 'space-between', flexWrap: 'wrap', gap: '0.75rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <AlertOctagon size={18} /> Incident Registry & Lifecycle Management
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <div style={{ display: 'flex', gap: '0.25rem', backgroundColor: 'var(--bg-secondary)', padding: '0.2rem', borderRadius: '4px' }}>
            {['ALL', 'ACTIVE', 'APPROVAL', 'RESOLVED'].map((f) => (
              <button
                key={f}
                className={`btn btn-sm ${filter === f ? 'btn-primary' : 'btn-secondary'}`}
                onClick={() => setFilter(f)}
              >
                {f}
              </button>
            ))}
          </div>

          <button className="btn btn-secondary btn-sm" onClick={fetchIncidents}>
            <RefreshCw size={14} /> Refresh
          </button>
        </div>
      </div>

      {filteredIncidents.length === 0 ? (
        <div style={{ padding: '2.5rem', textAlign: 'center', color: 'var(--text-muted)' }}>
          <ShieldAlert size={36} style={{ margin: '0 auto 0.75rem auto', opacity: 0.5 }} />
          <div>No incidents match filter: <strong>{filter}</strong></div>
          <p style={{ fontSize: '0.75rem', marginTop: '0.4rem' }}>
            You can trigger a failure scenario in the Simulation Center to test the autonomous multi-agent pipeline.
          </p>
          <button 
            className="btn btn-primary btn-sm" 
            style={{ marginTop: '0.75rem' }} 
            onClick={() => onNavigate('simulation')}
          >
            Go to Simulation Center
          </button>
        </div>
      ) : (
        <div className="table-container">
          <table className="data-table">
            <thead>
              <tr>
                <th>INCIDENT ID</th>
                <th>AFFECTED SERVICE</th>
                <th>SCENARIO TYPE</th>
                <th>SEVERITY</th>
                <th>STATUS</th>
                <th>ROOT CAUSE</th>
                <th>RECOVERY TIME</th>
                <th>ACTIONS</th>
              </tr>
            </thead>
            <tbody>
              {filteredIncidents.map((inc) => (
                <tr key={inc.id}>
                  <td style={{ fontFamily: 'var(--font-mono)', fontWeight: 600 }}>{inc.id}</td>
                  <td><span className="badge badge-info">{inc.affected_service}</span></td>
                  <td>{inc.scenario_type}</td>
                  <td>
                    <span className={`badge ${
                      inc.severity === 'CRITICAL' ? 'badge-danger' :
                      inc.severity === 'HIGH' ? 'badge-warning' : 'badge-info'
                    }`}>
                      {inc.severity}
                    </span>
                  </td>
                  <td>
                    <span className={`badge ${
                      inc.status === 'Resolved' ? 'badge-success' :
                      inc.status === 'Awaiting Approval' ? 'badge-warning' :
                      inc.status === 'Failed' ? 'badge-danger' : 'badge-purple'
                    }`}>
                      {inc.status}
                    </span>
                  </td>
                  <td style={{ maxWidth: '240px', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                    {inc.root_cause || 'Analyzing telemetry...'}
                  </td>
                  <td>
                    {inc.recovery_duration_seconds ? `${inc.recovery_duration_seconds}s` : '-'}
                  </td>
                  <td>
                    <div style={{ display: 'flex', gap: '0.35rem' }}>
                      <button
                        className="btn btn-secondary btn-sm"
                        onClick={() => onSelectIncident(inc.id)}
                      >
                        <Eye size={12} /> Inspect
                      </button>
                      {inc.status === 'Awaiting Approval' && (
                        <button
                          className="btn btn-warning btn-sm"
                          style={{ backgroundColor: '#f59e0b', color: '#000' }}
                          onClick={() => onNavigate('approval')}
                        >
                          Review Action
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
