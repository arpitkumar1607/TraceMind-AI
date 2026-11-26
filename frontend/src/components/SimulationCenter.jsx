import React, { useEffect, useState } from 'react';
import { api } from '../api';
import { 
  Play, 
  RotateCcw, 
  Terminal, 
  Flame, 
  Database, 
  Clock, 
  AlertTriangle, 
  CheckCircle2, 
  HardDrive 
} from 'lucide-react';

export default function SimulationCenter({ onSelectIncident, onNavigate }) {
  const [scenarios, setScenarios] = useState({});
  const [activeScenario, setActiveScenario] = useState(null);
  const [mode, setMode] = useState('normal');
  const [logs, setLogs] = useState([]);
  const [loadingAction, setLoadingAction] = useState(false);
  const [feedback, setFeedback] = useState(null);

  const fetchSimulationState = async () => {
    try {
      const [scenRes, logRes] = await Promise.all([
        api.getSimulationScenarios(),
        api.getSimulationLogs(35)
      ]);
      setScenarios(scenRes.scenarios || {});
      setActiveScenario(scenRes.active_scenario);
      setMode(scenRes.mode);
      setLogs(logRes.logs || []);
    } catch (err) {
      console.error("Failed to load simulation state", err);
    }
  };

  useEffect(() => {
    fetchSimulationState();
    const interval = setInterval(fetchSimulationState, 3000);
    return () => clearInterval(interval);
  }, []);

  const handleTrigger = async (key) => {
    setLoadingAction(true);
    setFeedback(null);
    try {
      const res = await api.triggerScenario(key);
      setFeedback({
        type: 'success',
        message: `Triggered '${res.simulation.name}'. Autonomous incident ${res.incident.id} generated!`,
        incidentId: res.incident.id
      });
      await fetchSimulationState();
    } catch (err) {
      setFeedback({ type: 'danger', message: `Failed to trigger scenario: ${err.message}` });
    } finally {
      setLoadingAction(false);
    }
  };

  const handleReset = async () => {
    setLoadingAction(true);
    try {
      await api.resetSimulation();
      setFeedback({ type: 'info', message: 'Simulation cluster reset to normal baseline.' });
      await fetchSimulationState();
    } catch (err) {
      setFeedback({ type: 'danger', message: `Reset failed: ${err.message}` });
    } finally {
      setLoadingAction(false);
    }
  };

  const getScenarioIcon = (key) => {
    if (key === 'high_cpu') return <Flame size={20} color="#f87171" />;
    if (key === 'memory_exhaustion') return <HardDrive size={20} color="#c084fc" />;
    if (key === 'db_failure') return <Database size={20} color="#f59e0b" />;
    if (key === 'api_latency') return <Clock size={20} color="#38bdf8" />;
    return <AlertTriangle size={20} color="#ef4444" />;
  };

  return (
    <div>
      {/* Simulation Control Toolbar */}
      <div className="card" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '0.75rem' }}>
        <div>
          <h2 style={{ fontSize: '1.1rem', fontWeight: 600 }}>Fault Injection & Incident Simulation Center</h2>
          <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
            Inject controlled, reproducible telemetry anomalies to evaluate multi-agent diagnosis and self-healing.
          </p>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <span className={`badge ${mode === 'incident' ? 'badge-danger' : 'badge-success'}`}>
            CLUSTER MODE: {mode.toUpperCase()}
          </span>

          <button 
            className="btn btn-secondary btn-sm" 
            onClick={handleReset}
            disabled={loadingAction}
          >
            <RotateCcw size={14} /> Reset Simulation to Baseline
          </button>
        </div>
      </div>

      {/* Feedback banner */}
      {feedback && (
        <div className={`alert alert-${feedback.type}`}>
          <div style={{ flexGrow: 1 }}>{feedback.message}</div>
          {feedback.incidentId && (
            <button 
              className="btn btn-primary btn-sm"
              onClick={() => onSelectIncident(feedback.incidentId)}
            >
              Inspect Incident #{feedback.incidentId}
            </button>
          )}
        </div>
      )}

      {/* 5 Incident Scenarios Grid */}
      <div className="grid-3" style={{ marginBottom: '1.25rem' }}>
        {Object.entries(scenarios).map(([key, sc]) => {
          const isCurrentActive = activeScenario === key;
          return (
            <div 
              key={key} 
              className="card" 
              style={{ 
                borderLeft: isCurrentActive ? '4px solid var(--danger)' : '1px solid var(--border-color)',
                backgroundColor: isCurrentActive ? 'rgba(239, 68, 68, 0.05)' : 'var(--bg-card)'
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
                {getScenarioIcon(key)}
                <div style={{ fontWeight: 600, fontSize: '0.9rem' }}>{sc.name}</div>
              </div>

              <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)', minHeight: '42px', marginBottom: '0.75rem' }}>
                {sc.description}
              </p>

              <div style={{ fontSize: '0.75rem', marginBottom: '0.75rem', display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: 'var(--text-dim)' }}>Target Service:</span>
                <span className="badge badge-info">{sc.service_id}</span>
              </div>

              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span className={`badge ${
                  sc.severity === 'CRITICAL' ? 'badge-danger' :
                  sc.severity === 'HIGH' ? 'badge-warning' : 'badge-info'
                }`}>
                  {sc.severity}
                </span>

                <button
                  className={`btn btn-sm ${isCurrentActive ? 'btn-danger' : 'btn-primary'}`}
                  onClick={() => handleTrigger(key)}
                  disabled={loadingAction}
                >
                  <Play size={12} /> {isCurrentActive ? 'Re-Trigger Incident' : 'Trigger Incident'}
                </button>
              </div>
            </div>
          );
        })}
      </div>

      {/* Live Telemetry / Synthetic Log Terminal */}
      <div className="card">
        <div className="card-title" style={{ justifyContent: 'space-between' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Terminal size={16} /> Live Microservice Log Stream & Synthetic Telemetry
          </div>
          <span style={{ fontSize: '0.72rem', color: 'var(--text-dim)' }}>Auto-scrolling tail (last 35 entries)</span>
        </div>

        <div className="log-terminal">
          {logs.length === 0 ? (
            <div style={{ color: 'var(--text-dim)' }}>Waiting for log events from simulation engine...</div>
          ) : (
            logs.map((l, i) => (
              <div key={i} className="log-line">
                <span className="log-ts">[{new Date(l.timestamp).toLocaleTimeString()}]</span>
                <span className={`log-${l.level}`}>[{l.level}]</span>
                <span style={{ color: '#94a3b8' }}>[{l.service_id}]:</span>
                <span>{l.message}</span>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
