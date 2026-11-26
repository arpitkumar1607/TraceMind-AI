import React, { useEffect, useState } from 'react';
import { api } from '../api';
import { 
  Activity, 
  AlertTriangle, 
  CheckCircle, 
  Clock, 
  Cpu, 
  HardDrive, 
  TrendingUp, 
  AlertCircle 
} from 'lucide-react';
import { 
  ResponsiveContainer, 
  LineChart, 
  Line, 
  XAxis, 
  YAxis, 
  Tooltip, 
  CartesianGrid 
} from 'recharts';

export default function DashboardOverview({ onSelectIncident, onNavigate }) {
  const [summary, setSummary] = useState(null);
  const [metrics, setMetrics] = useState([]);
  const [loading, setLoading] = useState(true);

  const loadData = async () => {
    try {
      const [sumData, metData] = await Promise.all([
        api.getDashboardSummary(),
        api.getDashboardMetrics()
      ]);
      setSummary(sumData);
      setMetrics(metData.metrics || []);
    } catch (err) {
      console.error("Failed to load dashboard data", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 4000);
    return () => clearInterval(interval);
  }, []);

  if (loading && !summary) {
    return <div className="card">Loading telemetry overview...</div>;
  }

  const healthColor = 
    summary?.system_health === 'HEALTHY' ? 'badge-success' :
    summary?.system_health === 'DEGRADED' ? 'badge-warning' : 'badge-danger';

  return (
    <div>
      {/* KPI Stats Grid */}
      <div className="grid-4">
        <div className="stat-card">
          <div className="stat-header">
            <span>SYSTEM STATUS</span>
            <Activity size={16} />
          </div>
          <div className="stat-value" style={{ fontSize: '1.2rem', marginTop: '0.4rem' }}>
            <span className={`badge ${healthColor}`}>{summary?.system_health || 'HEALTHY'}</span>
          </div>
          <div className="stat-sub">5 Microservices Online</div>
        </div>

        <div className="stat-card">
          <div className="stat-header">
            <span>ACTIVE INCIDENTS</span>
            <AlertTriangle size={16} color="#f59e0b" />
          </div>
          <div className="stat-value">{summary?.active_incidents ?? 0}</div>
          <div className="stat-sub">Requiring attention or in remediation</div>
        </div>

        <div className="stat-card">
          <div className="stat-header">
            <span>RESOLVED INCIDENTS</span>
            <CheckCircle size={16} color="#10b981" />
          </div>
          <div className="stat-value">{summary?.resolved_incidents ?? 0}</div>
          <div className="stat-sub">{summary?.total_incidents ?? 0} Total logged</div>
        </div>

        <div className="stat-card">
          <div className="stat-header">
            <span>AVG RESPONSE TIME</span>
            <Clock size={16} color="#3b82f6" />
          </div>
          <div className="stat-value">{summary?.avg_response_time_ms ?? 0} <span style={{ fontSize: '0.9rem', fontWeight: 400 }}>ms</span></div>
          <div className="stat-sub">Error Rate: {summary?.avg_error_rate ?? 0}%</div>
        </div>
      </div>

      {/* Telemetry Charts Grid */}
      <div className="grid-2">
        <div className="card">
          <div className="card-title">
            <Cpu size={16} color="#38bdf8" /> Cluster CPU Utilization Over Time (%)
          </div>
          <div style={{ height: 200 }}>
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={metrics}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                <XAxis dataKey="time" stroke="#64748b" fontSize={11} />
                <YAxis domain={[0, 100]} stroke="#64748b" fontSize={11} />
                <Tooltip contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155' }} />
                <Line type="monotone" dataKey="cpu_usage" stroke="#38bdf8" strokeWidth={2} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="card">
          <div className="card-title">
            <HardDrive size={16} color="#a855f7" /> Cluster Memory Allocation (%)
          </div>
          <div style={{ height: 200 }}>
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={metrics}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                <XAxis dataKey="time" stroke="#64748b" fontSize={11} />
                <YAxis domain={[0, 100]} stroke="#64748b" fontSize={11} />
                <Tooltip contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155' }} />
                <Line type="monotone" dataKey="memory_usage" stroke="#a855f7" strokeWidth={2} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="card">
          <div className="card-title">
            <TrendingUp size={16} color="#f59e0b" /> Ingress Response Latency (ms)
          </div>
          <div style={{ height: 200 }}>
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={metrics}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                <XAxis dataKey="time" stroke="#64748b" fontSize={11} />
                <YAxis stroke="#64748b" fontSize={11} />
                <Tooltip contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155' }} />
                <Line type="monotone" dataKey="response_time_ms" stroke="#f59e0b" strokeWidth={2} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="card">
          <div className="card-title">
            <AlertCircle size={16} color="#ef4444" /> Cluster HTTP Error Rate (%)
          </div>
          <div style={{ height: 200 }}>
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={metrics}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                <XAxis dataKey="time" stroke="#64748b" fontSize={11} />
                <YAxis domain={[0, 'auto']} stroke="#64748b" fontSize={11} />
                <Tooltip contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155' }} />
                <Line type="monotone" dataKey="error_rate" stroke="#ef4444" strokeWidth={2} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Recent Incident Activity Table */}
      <div className="card">
        <div className="card-title" style={{ justifyContent: 'space-between' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <AlertTriangle size={16} /> Recent Autonomous Incident Feed
          </div>
          <button className="btn btn-secondary btn-sm" onClick={() => onNavigate('incidents')}>
            View All Incidents
          </button>
        </div>

        {summary?.recent_incidents?.length === 0 ? (
          <div style={{ padding: '1rem', color: 'var(--text-muted)', textAlign: 'center', fontSize: '0.85rem' }}>
            No incidents recorded. System running at nominal parameters.
          </div>
        ) : (
          <div className="table-container">
            <table className="data-table">
              <thead>
                <tr>
                  <th>INCIDENT ID</th>
                  <th>TITLE</th>
                  <th>AFFECTED SERVICE</th>
                  <th>SEVERITY</th>
                  <th>STATUS</th>
                  <th>ROOT CAUSE</th>
                  <th>ACTION</th>
                </tr>
              </thead>
              <tbody>
                {summary?.recent_incidents?.map((inc) => (
                  <tr key={inc.id}>
                    <td style={{ fontFamily: 'var(--font-mono)', fontWeight: 600 }}>{inc.id}</td>
                    <td>{inc.title}</td>
                    <td><span className="badge badge-info">{inc.affected_service}</span></td>
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
                        inc.status === 'Awaiting Approval' ? 'badge-warning' : 'badge-purple'
                      }`}>
                        {inc.status}
                      </span>
                    </td>
                    <td style={{ maxWidth: '280px', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                      {inc.root_cause || 'Investigating...'}
                    </td>
                    <td>
                      <button 
                        className="btn btn-secondary btn-sm"
                        onClick={() => onSelectIncident(inc.id)}
                      >
                        Details
                      </button>
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
