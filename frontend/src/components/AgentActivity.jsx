import React, { useEffect, useState } from 'react';
import { api } from '../api';
import { Bot, Activity, Search, Wrench, CheckCircle2, Clock, RefreshCw } from 'lucide-react';

export default function AgentActivity() {
  const [agents, setAgents] = useState([]);
  const [activity, setActivity] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchData = async () => {
    try {
      const [agentRes, actRes] = await Promise.all([
        api.getAgents(),
        api.getAgentActivity()
      ]);
      setAgents(agentRes.agents || []);
      setActivity(actRes.timeline || []);
    } catch (err) {
      console.error("Error fetching agent data", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 4000);
    return () => clearInterval(interval);
  }, []);

  const getAgentIcon = (name) => {
    if (name.includes('Monitoring')) return <Activity size={18} color="#38bdf8" />;
    if (name.includes('RCA') || name.includes('Root-Cause')) return <Search size={18} color="#a855f7" />;
    if (name.includes('Remediation')) return <Wrench size={18} color="#f59e0b" />;
    return <CheckCircle2 size={18} color="#10b981" />;
  };

  return (
    <div>
      {/* 4 Specialized Agents Overview Cards */}
      <div className="grid-2" style={{ marginBottom: '1.25rem' }}>
        {agents.map((agent) => (
          <div key={agent.id} className="card" style={{ marginBottom: 0 }}>
            <div className="card-title" style={{ justifyContent: 'space-between' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                {getAgentIcon(agent.name)} {agent.name}
              </div>
              <div style={{ display: 'flex', gap: '0.35rem', alignItems: 'center' }}>
                {agent.framework && <span className="badge badge-info">{agent.framework}</span>}
                <span className="badge badge-success">{agent.status}</span>
              </div>
            </div>

            <div style={{ fontSize: '0.82rem', marginBottom: '0.5rem' }}>
              <strong style={{ color: 'var(--text-muted)' }}>Responsibility:</strong> {agent.role}
            </div>

            <div style={{ fontSize: '0.78rem', marginBottom: '0.5rem', color: 'var(--text-muted)' }}>
              <strong>Execution Logic:</strong> {agent.technique}
            </div>

            <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>
              <strong>Inputs:</strong> {agent.inputs?.join(', ')}
            </div>
          </div>
        ))}
      </div>

      {/* Chronological Global Agent Execution Feed */}
      <div className="card">
        <div className="card-title" style={{ justifyContent: 'space-between' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Clock size={16} /> Global Agent Execution Journal
          </div>
          <button className="btn btn-secondary btn-sm" onClick={fetchData}>
            <RefreshCw size={14} /> Refresh
          </button>
        </div>

        {activity.length === 0 ? (
          <div style={{ padding: '1.5rem', textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.82rem' }}>
            No agent executions logged yet. Agents run automatically when incidents are detected.
          </div>
        ) : (
          <div className="table-container">
            <table className="data-table">
              <thead>
                <tr>
                  <th>TIMESTAMP</th>
                  <th>AGENT</th>
                  <th>TASK / ACTION</th>
                  <th>INCIDENT</th>
                  <th>DURATION</th>
                  <th>EXECUTION SUMMARY</th>
                </tr>
              </thead>
              <tbody>
                {activity.map((item) => (
                  <tr key={item.id}>
                    <td style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                      {item.timestamp ? new Date(item.timestamp).toLocaleTimeString() : '-'}
                    </td>
                    <td>
                      <span className="badge badge-info">{item.agent_name}</span>
                    </td>
                    <td style={{ fontWeight: 500, fontSize: '0.78rem' }}>{item.task}</td>
                    <td style={{ fontFamily: 'var(--font-mono)', fontSize: '0.75rem' }}>{item.incident_id}</td>
                    <td style={{ fontSize: '0.75rem' }}>{item.duration_ms} ms</td>
                    <td style={{ maxWidth: '380px', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', fontSize: '0.78rem' }}>
                      {item.summary}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
