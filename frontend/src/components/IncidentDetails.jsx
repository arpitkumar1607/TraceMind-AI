import React, { useEffect, useState } from 'react';
import { api } from '../api';
import { 
  ArrowLeft, 
  Activity, 
  Search, 
  Wrench, 
  CheckCircle2, 
  Clock, 
  ShieldCheck, 
  Cpu, 
  HardDrive, 
  Sparkles, 
  FileText 
} from 'lucide-react';

export default function IncidentDetails({ incidentId, onBack, onNavigate }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);

  const fetchDetails = async () => {
    try {
      const res = await api.getIncidentDetails(incidentId);
      setData(res);
    } catch (err) {
      console.error("Failed to load incident details", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDetails();
  }, [incidentId]);

  const handleApprove = async () => {
    setActionLoading(true);
    try {
      await api.approveRemediation(incidentId, true, "DevOps Engineer");
      await fetchDetails();
    } catch (err) {
      alert("Remediation execution failed: " + err.message);
    } finally {
      setActionLoading(false);
    }
  };

  if (loading || !data) {
    return <div className="card">Loading complete incident telemetry & agent analysis...</div>;
  }

  const { incident, agent_executions, remediation_actions, verification_results } = data;
  const initial = incident.initial_metrics || {};
  const finalM = incident.final_metrics || {};
  const deltas = incident.metric_deltas || {};
  const verification = verification_results?.[0] || null;

  return (
    <div>
      {/* Top action header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1rem' }}>
        <button className="btn btn-secondary btn-sm" onClick={onBack}>
          <ArrowLeft size={14} /> Back to Incidents
        </button>

        <div style={{ display: 'flex', gap: '0.5rem' }}>
          {incident.status === 'Resolved' && (
            <a 
              href={api.downloadReportUrl(incident.id)}
              className="btn btn-secondary btn-sm"
              download
            >
              <FileText size={14} /> Download Post-Mortem Report (.md)
            </a>
          )}
          {incident.status === 'Awaiting Approval' && (
            <button className="btn btn-success btn-sm" onClick={handleApprove} disabled={actionLoading}>
              <ShieldCheck size={14} /> {actionLoading ? 'Executing Remediation...' : 'Approve & Execute Remediation'}
            </button>
          )}
        </div>
      </div>

      {/* Incident Header Card */}
      <div className="card" style={{ borderLeft: '4px solid var(--primary)' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.3rem' }}>
              <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.85rem', color: 'var(--text-muted)' }}>
                {incident.id}
              </span>
              <span className={`badge ${
                incident.severity === 'CRITICAL' ? 'badge-danger' :
                incident.severity === 'HIGH' ? 'badge-warning' : 'badge-info'
              }`}>
                {incident.severity} SEVERITY
              </span>
              <span className={`badge ${
                incident.status === 'Resolved' ? 'badge-success' :
                incident.status === 'Awaiting Approval' ? 'badge-warning' : 'badge-purple'
              }`}>
                {incident.status}
              </span>
            </div>
            <h2 style={{ fontSize: '1.25rem', fontWeight: 600 }}>{incident.title}</h2>
          </div>

          <div style={{ textAlign: 'right', fontSize: '0.8rem', color: 'var(--text-muted)' }}>
            <div>Created: {new Date(incident.created_at).toLocaleTimeString()}</div>
            {incident.resolved_at && (
              <div>Resolved: {new Date(incident.resolved_at).toLocaleTimeString()} (Duration: {incident.recovery_duration_seconds}s)</div>
            )}
          </div>
        </div>
      </div>

      {/* Four Agents Analysis Cards */}
      <div className="grid-2">
        {/* AGENT 1: Monitoring & Anomaly Detection */}
        <div className="card">
          <div className="card-title">
            <Activity size={16} color="#38bdf8" /> Agent 1: Monitoring Findings
          </div>

          <div style={{ marginBottom: '0.75rem', fontSize: '0.82rem' }}>
            <strong>Affected Microservice:</strong> <span className="badge badge-info">{incident.affected_service}</span>
          </div>

          <div style={{ marginBottom: '0.75rem' }}>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '0.3rem' }}>Telemetry Snapshot at Anomaly Trigger:</div>
            <div className="grid-2" style={{ gap: '0.5rem', marginBottom: '0.5rem' }}>
              <div style={{ backgroundColor: 'var(--bg-secondary)', padding: '0.5rem', borderRadius: '4px', fontSize: '0.78rem' }}>
                CPU: <strong>{initial.cpu_usage || '-'}%</strong>
              </div>
              <div style={{ backgroundColor: 'var(--bg-secondary)', padding: '0.5rem', borderRadius: '4px', fontSize: '0.78rem' }}>
                Memory: <strong>{initial.memory_usage || '-'}%</strong>
              </div>
              <div style={{ backgroundColor: 'var(--bg-secondary)', padding: '0.5rem', borderRadius: '4px', fontSize: '0.78rem' }}>
                Latency: <strong>{initial.response_time_ms || '-'} ms</strong>
              </div>
              <div style={{ backgroundColor: 'var(--bg-secondary)', padding: '0.5rem', borderRadius: '4px', fontSize: '0.78rem' }}>
                Error Rate: <strong>{initial.error_rate || '-'}%</strong>
              </div>
            </div>
          </div>

          <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '0.3rem' }}>Detected Anomalies:</div>
          <ul style={{ paddingLeft: '1.2rem', fontSize: '0.78rem', color: '#fca5a5' }}>
            {incident.evidence_summary?.split('\n').filter(Boolean).map((ev, idx) => (
              <li key={idx} style={{ marginBottom: '0.2rem' }}>{ev}</li>
            ))}
          </ul>
        </div>

        {/* AGENT 2: Root-Cause Analysis */}
        <div className="card">
          <div className="card-title" style={{ justifyContent: 'space-between' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <Search size={16} color="#a855f7" /> Agent 2: Root Cause Analysis (RCA)
            </div>
            <span className={`badge ${incident.is_llm_diagnosis ? 'badge-purple' : 'badge-info'}`}>
              <Sparkles size={11} /> {incident.is_llm_diagnosis ? 'Groq LLM' : 'Deterministic Rule Engine'}
            </span>
          </div>

          <div style={{ marginBottom: '0.75rem' }}>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Probable Root Cause:</div>
            <div style={{ fontSize: '0.9rem', fontWeight: 600, color: '#fff', marginTop: '0.2rem' }}>
              {incident.root_cause || 'Investigating...'}
            </div>
          </div>

          <div style={{ marginBottom: '0.75rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', marginBottom: '0.25rem' }}>
              <span style={{ color: 'var(--text-muted)' }}>Confidence Score</span>
              <span style={{ fontWeight: 600 }}>{Math.round((incident.confidence_score || 0) * 100)}%</span>
            </div>
            <div style={{ width: '100%', height: '6px', backgroundColor: 'var(--bg-secondary)', borderRadius: '3px', overflow: 'hidden' }}>
              <div 
                style={{ 
                  width: `${(incident.confidence_score || 0) * 100}%`, 
                  height: '100%', 
                  backgroundColor: incident.confidence_score > 0.85 ? 'var(--success)' : 'var(--warning)' 
                }} 
              />
            </div>
          </div>

          <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '0.3rem' }}>Correlated Telemetry Evidence:</div>
          <div className="log-terminal" style={{ maxHeight: '110px' }}>
            {incident.evidence_summary?.split('\n').map((line, idx) => (
              <div key={idx} className="log-line">
                <span className="log-INFO">●</span>
                <span>{line}</span>
              </div>
            ))}
          </div>
        </div>

        {/* AGENT 3: Remediation & Safety Guardrails */}
        <div className="card">
          <div className="card-title">
            <Wrench size={16} color="#f59e0b" /> Agent 3: Remediation & Safety Guardrails
          </div>

          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem', fontSize: '0.82rem' }}>
            <span>Recommended Safe Action:</span>
            <code style={{ color: '#60a5fa', fontWeight: 600 }}>{incident.recommended_action || 'None'}</code>
          </div>

          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem', fontSize: '0.82rem' }}>
            <span>Risk Classification:</span>
            <span className={`badge ${
              incident.risk_level === 'HIGH' ? 'badge-danger' :
              incident.risk_level === 'MEDIUM' ? 'badge-warning' : 'badge-success'
            }`}>
              {incident.risk_level} RISK
            </span>
          </div>

          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.75rem', fontSize: '0.82rem' }}>
            <span>Human Approval Gate:</span>
            <span className={`badge ${
              incident.approval_status === 'APPROVED' || incident.approval_status === 'EXECUTED' ? 'badge-success' :
              incident.approval_status === 'PENDING' ? 'badge-warning' : 'badge-info'
            }`}>
              {incident.approval_status}
            </span>
          </div>

          <div style={{ backgroundColor: 'var(--bg-secondary)', padding: '0.5rem 0.75rem', borderRadius: '4px', fontSize: '0.78rem' }}>
            <div style={{ color: 'var(--text-muted)', marginBottom: '0.2rem' }}>Execution Result:</div>
            <div style={{ color: incident.execution_result ? 'var(--text-main)' : 'var(--text-dim)' }}>
              {incident.execution_result || 'Awaiting execution of approved action.'}
            </div>
          </div>
        </div>

        {/* AGENT 4: Health Verification */}
        <div className="card">
          <div className="card-title">
            <CheckCircle2 size={16} color="#10b981" /> Agent 4: Health Verification & Metric Deltas
          </div>

          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.75rem', fontSize: '0.82rem' }}>
            <span>Verification Status:</span>
            <span className={`badge ${
              incident.verification_status === 'Resolved' ? 'badge-success' :
              incident.verification_status === 'Failed' ? 'badge-danger' : 'badge-warning'
            }`}>
              {incident.verification_status}
            </span>
          </div>

          <table className="data-table" style={{ fontSize: '0.75rem' }}>
            <thead>
              <tr>
                <th>SIGNAL</th>
                <th>PRE-RECOVERY</th>
                <th>POST-RECOVERY</th>
                <th>IMPROVEMENT</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td>CPU Usage</td>
                <td>{deltas.cpu_usage?.before ?? initial.cpu_usage ?? '-'}%</td>
                <td>{deltas.cpu_usage?.after ?? finalM.cpu_usage ?? '-'}%</td>
                <td style={{ color: 'var(--success)', fontWeight: 600 }}>
                  {deltas.cpu_usage?.delta ? `${deltas.cpu_usage.delta}%` : '-'}
                </td>
              </tr>
              <tr>
                <td>Memory</td>
                <td>{deltas.memory_usage?.before ?? initial.memory_usage ?? '-'}%</td>
                <td>{deltas.memory_usage?.after ?? finalM.memory_usage ?? '-'}%</td>
                <td style={{ color: 'var(--success)', fontWeight: 600 }}>
                  {deltas.memory_usage?.delta ? `${deltas.memory_usage.delta}%` : '-'}
                </td>
              </tr>
              <tr>
                <td>Latency</td>
                <td>{deltas.response_time_ms?.before ?? initial.response_time_ms ?? '-'} ms</td>
                <td>{deltas.response_time_ms?.after ?? finalM.response_time_ms ?? '-'} ms</td>
                <td style={{ color: 'var(--success)', fontWeight: 600 }}>
                  {deltas.response_time_ms?.delta ? `${deltas.response_time_ms.delta} ms` : '-'}
                </td>
              </tr>
              <tr>
                <td>Error Rate</td>
                <td>{deltas.error_rate?.before ?? initial.error_rate ?? '-'}%</td>
                <td>{deltas.error_rate?.after ?? finalM.error_rate ?? '-'}%</td>
                <td style={{ color: 'var(--success)', fontWeight: 600 }}>
                  {deltas.error_rate?.delta ? `${deltas.error_rate.delta}%` : '-'}
                </td>
              </tr>
            </tbody>
          </table>

          {verification?.notes && (
            <div style={{ marginTop: '0.5rem', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
              Note: {verification.notes}
            </div>
          )}
        </div>
      </div>

      {/* Chronological Agent Execution Timeline */}
      <div className="card">
        <div className="card-title">
          <Clock size={16} /> Multi-Agent Execution Timeline
        </div>

        {agent_executions?.length === 0 ? (
          <div style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>No agent executions logged yet.</div>
        ) : (
          <div className="timeline">
            {agent_executions.map((exec, idx) => (
              <div key={idx} className="timeline-item">
                <div className="timeline-point" />
                <div className="timeline-header">
                  <span>{exec.agent_name}</span>
                  <span>{exec.duration_ms} ms</span>
                </div>
                <div className="timeline-title">{exec.task}</div>
                <div className="timeline-desc">
                  {exec.output?.summary || JSON.stringify(exec.output)}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
