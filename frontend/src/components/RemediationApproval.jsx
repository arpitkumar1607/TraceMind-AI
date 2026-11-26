import React, { useEffect, useState } from 'react';
import { api } from '../api';
import { ShieldAlert, Check, X, CheckCircle2, AlertTriangle, ArrowRight } from 'lucide-react';

export default function RemediationApproval({ onSelectIncident }) {
  const [pendingIncidents, setPendingIncidents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [processingId, setProcessingId] = useState(null);
  const [actionResult, setActionResult] = useState(null);

  const fetchPending = async () => {
    try {
      const data = await api.getIncidents();
      const pending = (data || []).filter(
        (i) => i.status === 'Awaiting Approval' || (i.approval_status === 'PENDING' && i.recommended_action)
      );
      setPendingIncidents(pending);
    } catch (err) {
      console.error("Failed to fetch pending approvals", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPending();
    const interval = setInterval(fetchPending, 4000);
    return () => clearInterval(interval);
  }, []);

  const handleDecision = async (incidentId, approved) => {
    setProcessingId(incidentId);
    setActionResult(null);
    try {
      if (approved) {
        const res = await api.approveRemediation(incidentId, true, "DevOps Engineer");
        setActionResult({
          type: 'success',
          message: `Remediation executed and verified for Incident ${incidentId}. Status: ${res.incident.status}`,
          incident: res.incident
        });
      } else {
        const res = await api.rejectRemediation(incidentId);
        setActionResult({
          type: 'warning',
          message: `Remediation rejected by human operator for Incident ${incidentId}.`,
          incident: res.incident
        });
      }
      await fetchPending();
    } catch (err) {
      setActionResult({
        type: 'danger',
        message: `Action execution error: ${err.message}`
      });
    } finally {
      setProcessingId(null);
    }
  };

  return (
    <div>
      <div className="card">
        <div className="card-title">
          <ShieldAlert size={18} color="#f59e0b" /> Human-in-the-Loop Remediation Approval Gate
        </div>
        <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
          High-risk and service-impacting remediation actions are halted at this safety barrier. 
          Operators must explicitly review potential blast radius before autonomous execution.
        </p>
      </div>

      {actionResult && (
        <div className={`alert alert-${actionResult.type}`}>
          <div style={{ flexGrow: 1 }}>{actionResult.message}</div>
          {actionResult.incident && (
            <button 
              className="btn btn-primary btn-sm"
              onClick={() => onSelectIncident(actionResult.incident.id)}
            >
              View Verification Details
            </button>
          )}
        </div>
      )}

      {pendingIncidents.length === 0 ? (
        <div className="card" style={{ padding: '3rem', textAlign: 'center', color: 'var(--text-muted)' }}>
          <CheckCircle2 size={40} color="#10b981" style={{ margin: '0 auto 1rem auto' }} />
          <h3 style={{ fontSize: '1rem', fontWeight: 600, color: 'var(--text-main)' }}>No Pending Approvals</h3>
          <p style={{ fontSize: '0.8rem', marginTop: '0.3rem' }}>
            All detected incidents have been resolved, or no high-risk recovery action currently requires operator clearance.
          </p>
        </div>
      ) : (
        <div className="grid-2">
          {pendingIncidents.map((inc) => (
            <div 
              key={inc.id} 
              className="card"
              style={{ borderLeft: '4px solid #f59e0b' }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.75rem' }}>
                <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.8rem', fontWeight: 600 }}>{inc.id}</span>
                <span className={`badge ${
                  inc.risk_level === 'HIGH' ? 'badge-danger' :
                  inc.risk_level === 'MEDIUM' ? 'badge-warning' : 'badge-info'
                }`}>
                  {inc.risk_level} RISK
                </span>
              </div>

              <h3 style={{ fontSize: '1rem', fontWeight: 600, marginBottom: '0.4rem' }}>{inc.title}</h3>
              <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '0.75rem' }}>
                Target Microservice: <span className="badge badge-info">{inc.affected_service}</span>
              </p>

              <div style={{ backgroundColor: 'var(--bg-secondary)', padding: '0.75rem', borderRadius: '4px', marginBottom: '1rem', fontSize: '0.78rem' }}>
                <div style={{ marginBottom: '0.4rem' }}>
                  <strong style={{ color: 'var(--text-main)' }}>Root Cause Diagnosed:</strong>
                  <div style={{ color: 'var(--text-muted)' }}>{inc.root_cause || 'Investigating'}</div>
                </div>

                <div style={{ marginBottom: '0.4rem' }}>
                  <strong style={{ color: 'var(--text-main)' }}>Recommended Recovery Action:</strong>
                  <div style={{ color: '#60a5fa', fontFamily: 'var(--font-mono)', fontWeight: 600 }}>{inc.recommended_action}</div>
                </div>

                <div>
                  <strong style={{ color: 'var(--text-main)' }}>Potential Blast Radius:</strong>
                  <div style={{ color: '#fca5a5' }}>
                    {inc.action_parameters?.spec?.potential_impact || 'Transient throughput fluctuation.'}
                  </div>
                </div>
              </div>

              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <button 
                  className="btn btn-secondary btn-sm"
                  onClick={() => onSelectIncident(inc.id)}
                >
                  Inspect Evidence
                </button>

                <div style={{ display: 'flex', gap: '0.5rem' }}>
                  <button 
                    className="btn btn-danger btn-sm"
                    onClick={() => handleDecision(inc.id, false)}
                    disabled={processingId === inc.id}
                  >
                    <X size={14} /> Reject
                  </button>

                  <button 
                    className="btn btn-success btn-sm"
                    onClick={() => handleDecision(inc.id, true)}
                    disabled={processingId === inc.id}
                  >
                    <Check size={14} /> {processingId === inc.id ? 'Executing...' : 'Approve & Execute'}
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
