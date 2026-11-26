import React, { useEffect, useState } from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
  Legend,
} from 'recharts';
import { Activity, Play, DollarSign, CheckCircle2, XCircle, Gauge, RefreshCw } from 'lucide-react';
import { api } from '../api';

export default function ObservabilityEval() {
  const [obs, setObs] = useState(null);
  const [evalData, setEvalData] = useState(null);
  const [costData, setCostData] = useState(null);
  const [monthlyVolume, setMonthlyVolume] = useState(1000);
  const [runningEval, setRunningEval] = useState(false);
  const [loading, setLoading] = useState(true);

  const loadAll = async (vol = monthlyVolume) => {
    try {
      const [obsRes, evalRes, costRes] = await Promise.all([
        api.getObservabilityMetrics(),
        api.getLatestEvaluation(),
        api.getCostEstimation(vol),
      ]);
      setObs(obsRes);
      setEvalData(evalRes);
      setCostData(costRes);
    } catch (err) {
      console.error('Error loading observability/evaluation data', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAll(monthlyVolume);
  }, [monthlyVolume]);

  const handleRunLiveEval = async () => {
    setRunningEval(true);
    try {
      const res = await api.runLiveEvaluation();
      setEvalData(res);
      await loadAll(monthlyVolume);
    } catch (err) {
      console.error('Live evaluation failed', err);
    } finally {
      setRunningEval(false);
    }
  };

  if (loading && !obs) {
    return <div className="card">Loading Grafana-style Observability, Live Evaluation & Cost Estimation...</div>;
  }

  const kpis = obs?.kpis || {};
  const serviceSeries = obs?.service_series || [];
  const results = evalData?.results || [];
  const tiers = costData?.volume_tiers || [];

  return (
    <div>
      {/* Header Banner */}
      <div className="card" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '0.75rem' }}>
        <div>
          <div className="card-title" style={{ marginBottom: '0.25rem' }}>
            <Gauge size={18} color="#f97316" /> Grafana-Style Observability, Live Agent Evaluation & Cost Estimation
          </div>
          <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
            Frameworks: <strong>CrewAI + Google ADK</strong> &nbsp;|&nbsp; Prometheus Scrape Endpoint: <code>/metrics</code>
          </div>
        </div>
        <div style={{ display: 'flex', gap: '0.5rem' }}>
          <button className="btn btn-secondary btn-sm" onClick={() => loadAll(monthlyVolume)}>
            <RefreshCw size={14} /> Refresh Metrics
          </button>
          <button className="btn btn-primary btn-sm" onClick={handleRunLiveEval} disabled={runningEval}>
            <Play size={14} /> {runningEval ? 'Running 5-Scenario Benchmark...' : 'Run Live Agent Evaluation'}
          </button>
        </div>
      </div>

      {/* Grafana KPI Row */}
      <div className="kpi-grid" style={{ marginBottom: '1.25rem' }}>
        <div className="kpi-card">
          <div className="kpi-label">LIVE EVAL PASS RATE</div>
          <div className="kpi-value" style={{ color: '#10b981' }}>
            {evalData?.overall_pass_rate_percent ?? kpis.eval_pass_rate_percent ?? 0}%
          </div>
          <div className="kpi-sub">
            {evalData?.scenarios_passed ?? 0}/{evalData?.scenarios_tested ?? 5} scenarios passed
          </div>
        </div>
        <div className="kpi-card">
          <div className="kpi-label">AVG PIPELINE LATENCY</div>
          <div className="kpi-value" style={{ color: '#38bdf8' }}>
            {evalData?.avg_pipeline_latency_ms ?? kpis.avg_agent_latency_ms ?? 0} ms
          </div>
          <div className="kpi-sub">ADK + CrewAI end-to-end</div>
        </div>
        <div className="kpi-card">
          <div className="kpi-label">AVG RCA CONFIDENCE</div>
          <div className="kpi-value" style={{ color: '#a855f7' }}>
            {evalData?.avg_rca_confidence_percent ?? 0}%
          </div>
          <div className="kpi-sub">Evidence-backed diagnosis</div>
        </div>
        <div className="kpi-card">
          <div className="kpi-label">PROJECTED COST ({monthlyVolume}/MO)</div>
          <div className="kpi-value" style={{ color: '#f59e0b' }}>
            ${costData?.projected_monthly?.estimated_usd?.toFixed(4) ?? '0.0000'}
          </div>
          <div className="kpi-sub">
            Hybrid LLM est: ${costData?.projected_monthly?.hybrid_if_llm_enabled_usd?.toFixed(4) ?? '0.0000'}/mo
          </div>
        </div>
      </div>

      {/* Grafana-style Charts */}
      <div className="grid-2" style={{ marginBottom: '1.25rem' }}>
        <div className="card" style={{ marginBottom: 0 }}>
          <div className="card-title">
            <Activity size={16} color="#38bdf8" /> Service CPU & Memory Utilization (%)
          </div>
          <div style={{ width: '100%', height: 240 }}>
            <ResponsiveContainer>
              <BarChart data={serviceSeries}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(148,163,184,0.15)" />
                <XAxis dataKey="service" tick={{ fontSize: 10, fill: '#94a3b8' }} />
                <YAxis domain={[0, 100]} tick={{ fontSize: 11, fill: '#94a3b8' }} />
                <Tooltip />
                <Legend />
                <Bar dataKey="cpu_percent" name="CPU %" fill="#38bdf8" radius={[4, 4, 0, 0]} />
                <Bar dataKey="memory_percent" name="Memory %" fill="#a855f7" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="card" style={{ marginBottom: 0 }}>
          <div className="card-title">
            <Activity size={16} color="#f59e0b" /> Service Response Latency (ms)
          </div>
          <div style={{ width: '100%', height: 240 }}>
            <ResponsiveContainer>
              <BarChart data={serviceSeries}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(148,163,184,0.15)" />
                <XAxis dataKey="service" tick={{ fontSize: 10, fill: '#94a3b8' }} />
                <YAxis tick={{ fontSize: 11, fill: '#94a3b8' }} />
                <Tooltip />
                <Bar dataKey="latency_ms" name="Latency (ms)" fill="#f59e0b" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Live Agent Evaluation Matrix */}
      <div className="card">
        <div className="card-title" style={{ justifyContent: 'space-between' }}>
          <span>Live Multi-Agent Evaluation Matrix (Google ADK + CrewAI)</span>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
            Last Run: {evalData?.evaluated_at ? new Date(evalData.evaluated_at).toLocaleTimeString() : '-'} ({evalData?.total_benchmark_ms ?? 0} ms)
          </span>
        </div>
        <div className="table-container">
          <table className="data-table">
            <thead>
              <tr>
                <th>SCENARIO</th>
                <th>SERVICE</th>
                <th>ADK MONITORING</th>
                <th>CREWAI RCA</th>
                <th>CREWAI REMEDIATION</th>
                <th>ADK VERIFICATION</th>
                <th>LATENCY</th>
                <th>SCORE</th>
              </tr>
            </thead>
            <tbody>
              {results.map((r) => (
                <tr key={r.scenario}>
                  <td style={{ fontWeight: 600 }}>{r.scenario}</td>
                  <td style={{ fontFamily: 'var(--font-mono)', fontSize: '0.75rem' }}>{r.service}</td>
                  <td>{r.checks?.adk_monitoring_passed ? <CheckCircle2 size={16} color="#10b981" /> : <XCircle size={16} color="#ef4444" />}</td>
                  <td>{r.checks?.crewai_rca_passed ? <CheckCircle2 size={16} color="#10b981" /> : <XCircle size={16} color="#ef4444" />}</td>
                  <td>{r.checks?.crewai_remediation_passed ? <CheckCircle2 size={16} color="#10b981" /> : <XCircle size={16} color="#ef4444" />}</td>
                  <td>{r.checks?.adk_verification_passed ? <CheckCircle2 size={16} color="#10b981" /> : <XCircle size={16} color="#ef4444" />}</td>
                  <td>{r.total_latency_ms} ms</td>
                  <td>
                    <span className={`badge ${r.passed ? 'badge-success' : 'badge-danger'}`}>
                      {r.score_percent}%
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Cost Estimation Table */}
      <div className="card">
        <div className="card-title" style={{ justifyContent: 'space-between', flexWrap: 'wrap', gap: '0.5rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <DollarSign size={16} color="#10b981" /> Agentic Cost Estimation ({costData?.active_mode})
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.78rem' }}>
            <span>Monthly Volume:</span>
            {[100, 1000, 10000].map((v) => (
              <button
                key={v}
                className={`btn btn-sm ${monthlyVolume === v ? 'btn-primary' : 'btn-secondary'}`}
                onClick={() => setMonthlyVolume(v)}
              >
                {v.toLocaleString()}
              </button>
            ))}
          </div>
        </div>

        <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '0.75rem' }}>
          Avg Tokens / Incident: <strong>{costData?.tokens_per_incident?.total_tokens ?? 0}</strong> ({costData?.tokens_per_incident?.input_tokens ?? 0} in / {costData?.tokens_per_incident?.output_tokens ?? 0} out)
          &nbsp;|&nbsp; Hybrid Cost / Incident: <strong>${costData?.per_incident_cost_usd?.hybrid_total?.toFixed(6) ?? '0.000000'}</strong>
        </div>

        <div className="table-container">
          <table className="data-table">
            <thead>
              <tr>
                <th>MONTHLY INCIDENTS</th>
                <th>DETERMINISTIC OFFLINE</th>
                <th>GOOGLE ADK ONLY (GEMINI 2.5 FLASH)</th>
                <th>HYBRID (ADK + CREWAI GROQ LLAMA 70B)</th>
              </tr>
            </thead>
            <tbody>
              {tiers.map((t) => (
                <tr key={t.monthly_incidents}>
                  <td style={{ fontWeight: 600 }}>{t.monthly_incidents.toLocaleString()} / month</td>
                  <td>${t.deterministic_usd.toFixed(4)}</td>
                  <td>${t.adk_only_usd.toFixed(4)}</td>
                  <td>${t.hybrid_adk_crewai_usd.toFixed(4)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
