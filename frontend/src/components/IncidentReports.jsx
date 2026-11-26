import React, { useEffect, useState } from 'react';
import { api } from '../api';
import { FileText, Download, Eye, CheckCircle2, Clock } from 'lucide-react';

export default function IncidentReports({ onSelectIncident }) {
  const [reports, setReports] = useState([]);
  const [selectedReport, setSelectedReport] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchReports = async () => {
    try {
      const data = await api.getReports();
      setReports(data || []);
      if (data && data.length > 0 && !selectedReport) {
        loadReportDetail(data[0].id);
      }
    } catch (err) {
      console.error("Failed to load incident reports", err);
    } finally {
      setLoading(false);
    }
  };

  const loadReportDetail = async (id) => {
    try {
      const rep = await api.getIncidentReport(id);
      setSelectedReport(rep);
    } catch (err) {
      console.error("Failed to fetch report detail", err);
    }
  };

  useEffect(() => {
    fetchReports();
  }, []);

  return (
    <div>
      <div className="card">
        <div className="card-title">
          <FileText size={18} /> Incident Post-Mortem & Audit Reports
        </div>
        <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
          Detailed compliance post-mortem reports capturing root-cause analysis, human approval timestamps,
          remediation execution logs, and before/after verification deltas.
        </p>
      </div>

      {reports.length === 0 ? (
        <div className="card" style={{ padding: '3rem', textAlign: 'center', color: 'var(--text-muted)' }}>
          <FileText size={40} style={{ margin: '0 auto 1rem auto', opacity: 0.5 }} />
          <h3>No Post-Mortem Reports Available</h3>
          <p style={{ fontSize: '0.8rem', marginTop: '0.3rem' }}>
            Reports are generated automatically once an incident completes the remediation and verification stages.
          </p>
        </div>
      ) : (
        <div className="grid-3">
          {/* Left: Incident list */}
          <div className="card" style={{ height: 'fit-content' }}>
            <div className="card-title">Resolved Incident Log</div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
              {reports.map((r) => {
                const isSelected = selectedReport?.incident_id === r.id;
                return (
                  <div
                    key={r.id}
                    onClick={() => loadReportDetail(r.id)}
                    style={{
                      padding: '0.75rem',
                      borderRadius: '4px',
                      cursor: 'pointer',
                      border: isSelected ? '1px solid var(--primary)' : '1px solid var(--border-color)',
                      backgroundColor: isSelected ? 'var(--bg-secondary)' : 'transparent',
                      transition: 'background 0.15s ease'
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', marginBottom: '0.2rem' }}>
                      <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 600 }}>{r.id}</span>
                      <span className="badge badge-success">{r.status}</span>
                    </div>
                    <div style={{ fontSize: '0.82rem', fontWeight: 500 }}>{r.title}</div>
                    <div style={{ fontSize: '0.72rem', color: 'var(--text-dim)', marginTop: '0.2rem' }}>
                      Recovery: {r.recovery_duration_seconds ? `${r.recovery_duration_seconds}s` : 'N/A'}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Right: Selected Report Preview (Spans 2 columns) */}
          <div className="card" style={{ gridColumn: 'span 2' }}>
            {selectedReport ? (
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid var(--border-color)', paddingBottom: '0.75rem', marginBottom: '1rem' }}>
                  <div>
                    <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                      POST-MORTEM REPORT: {selectedReport.incident_id}
                    </span>
                    <h2 style={{ fontSize: '1.2rem', fontWeight: 600 }}>{selectedReport.title}</h2>
                  </div>

                  <a 
                    href={api.downloadReportUrl(selectedReport.incident_id)}
                    className="btn btn-primary btn-sm"
                    download
                  >
                    <Download size={14} /> Download Markdown (.md)
                  </a>
                </div>

                <div className="grid-2" style={{ marginBottom: '1rem' }}>
                  <div style={{ backgroundColor: 'var(--bg-secondary)', padding: '0.75rem', borderRadius: '4px', fontSize: '0.8rem' }}>
                    <div><strong>Microservice:</strong> {selectedReport.affected_service}</div>
                    <div><strong>Severity:</strong> {selectedReport.severity}</div>
                    <div><strong>Total Recovery Time:</strong> {selectedReport.duration_seconds} seconds</div>
                  </div>

                  <div style={{ backgroundColor: 'var(--bg-secondary)', padding: '0.75rem', borderRadius: '4px', fontSize: '0.8rem' }}>
                    <div><strong>Remediation Executed:</strong> <code>{selectedReport.remediation_action}</code></div>
                    <div><strong>Approval Status:</strong> {selectedReport.approval_status} (By {selectedReport.approved_by || 'Admin'})</div>
                    <div><strong>Verification Result:</strong> {selectedReport.verification_result}</div>
                  </div>
                </div>

                <div style={{ marginBottom: '1.25rem' }}>
                  <h4 style={{ fontSize: '0.9rem', marginBottom: '0.4rem' }}>Root Cause Diagnosis</h4>
                  <div style={{ backgroundColor: 'var(--bg-secondary)', padding: '0.75rem', borderRadius: '4px', fontSize: '0.82rem', borderLeft: '3px solid #a855f7' }}>
                    <div>{selectedReport.root_cause}</div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.3rem' }}>
                      Confidence: {Math.round(selectedReport.confidence_score * 100)}% | Provider: {selectedReport.is_llm_diagnosis ? 'Groq LLM' : 'Deterministic Rule Engine'}
                    </div>
                  </div>
                </div>

                <div style={{ marginBottom: '1.25rem' }}>
                  <h4 style={{ fontSize: '0.9rem', marginBottom: '0.4rem' }}>Telemetry Metrics Delta</h4>
                  <table className="data-table" style={{ fontSize: '0.78rem' }}>
                    <thead>
                      <tr>
                        <th>METRIC</th>
                        <th>BEFORE RECOVERY</th>
                        <th>AFTER RECOVERY</th>
                        <th>DELTA</th>
                      </tr>
                    </thead>
                    <tbody>
                      {Object.entries(selectedReport.metric_improvements || {}).map(([metric, val]) => (
                        <tr key={metric}>
                          <td style={{ fontWeight: 500 }}>{metric}</td>
                          <td>{val.before} {val.unit}</td>
                          <td>{val.after} {val.unit}</td>
                          <td style={{ color: 'var(--success)', fontWeight: 600 }}>{val.delta} {val.unit}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                <div>
                  <h4 style={{ fontSize: '0.9rem', marginBottom: '0.4rem' }}>Markdown Source Export</h4>
                  <pre style={{ 
                    backgroundColor: '#0b1120', 
                    padding: '0.75rem', 
                    borderRadius: '4px', 
                    fontSize: '0.72rem', 
                    fontFamily: 'var(--font-mono)', 
                    overflowX: 'auto',
                    maxHeight: '180px',
                    color: '#94a3b8'
                  }}>
                    {selectedReport.summary_markdown}
                  </pre>
                </div>
              </div>
            ) : (
              <div style={{ color: 'var(--text-muted)', textAlign: 'center', padding: '2rem' }}>
                Select an incident from the left to view the post-mortem report.
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
