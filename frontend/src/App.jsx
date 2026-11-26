import React, { useState, useEffect } from 'react';
import { 
  LayoutDashboard, 
  Server, 
  AlertOctagon, 
  Bot, 
  PlayCircle, 
  ShieldCheck, 
  FileText, 
  Activity, 
  RotateCw,
  Cpu
} from 'lucide-react';
import { api } from './api';

import DashboardOverview from './components/DashboardOverview';
import ServicesMonitoring from './components/ServicesMonitoring';
import IncidentManagement from './components/IncidentManagement';
import IncidentDetails from './components/IncidentDetails';
import AgentActivity from './components/AgentActivity';
import SimulationCenter from './components/SimulationCenter';
import RemediationApproval from './components/RemediationApproval';
import IncidentReports from './components/IncidentReports';
import ObservabilityEval from './components/ObservabilityEval';

export default function App() {
  const [currentTab, setCurrentTab] = useState('overview');
  const [selectedIncidentId, setSelectedIncidentId] = useState(null);
  const [systemHealth, setSystemHealth] = useState({
    status: 'connecting',
    overall_health: 'HEALTHY',
    active_incidents_count: 0,
    llm_active: false
  });

  const pollSystemStatus = async () => {
    try {
      const data = await api.getSystemStatus();
      setSystemHealth({
        status: 'online',
        overall_health: data.overall_health,
        active_incidents_count: data.active_incidents_count,
        llm_active: data.llm_active
      });
    } catch {
      setSystemHealth((prev) => ({ ...prev, status: 'offline' }));
    }
  };

  useEffect(() => {
    pollSystemStatus();
    const interval = setInterval(pollSystemStatus, 4000);
    return () => clearInterval(interval);
  }, []);

  const handleSelectIncident = (id) => {
    setSelectedIncidentId(id);
    setCurrentTab('details');
  };

  const navItems = [
    { id: 'overview', label: 'Overview Dashboard', icon: <LayoutDashboard size={18} /> },
    { id: 'services', label: 'Services Monitoring', icon: <Server size={18} /> },
    { id: 'incidents', label: 'Incident Management', icon: <AlertOctagon size={18} /> },
    { id: 'agents', label: 'Agent Activity', icon: <Bot size={18} /> },
    { id: 'observability', label: 'Observability & Eval', icon: <Activity size={18} /> },
    { id: 'simulation', label: 'Simulation Center', icon: <PlayCircle size={18} /> },
    { 
      id: 'approval', 
      label: 'Remediation Approval', 
      icon: <ShieldCheck size={18} />,
      badge: systemHealth.active_incidents_count > 0 ? systemHealth.active_incidents_count : null
    },
    { id: 'reports', label: 'Incident Reports', icon: <FileText size={18} /> },
  ];

  return (
    <div className="app-container">
      {/* Sidebar Navigation */}
      <aside className="sidebar">
        <div className="sidebar-header">
          <div className="brand-title">
            <Cpu size={22} color="#3b82f6" />
            <span>TraceMind AI</span>
            <span className="brand-badge">v1.0</span>
          </div>
          <div className="brand-subtitle">
            Autonomous Root-Cause Analysis & Self-Healing Telemetry
          </div>
        </div>

        <ul className="nav-links">
          {navItems.map((item) => {
            const isActive = currentTab === item.id || (item.id === 'incidents' && currentTab === 'details');
            return (
              <li key={item.id} className="nav-item">
                <button
                  className={`nav-button ${isActive ? 'active' : ''}`}
                  onClick={() => {
                    setCurrentTab(item.id);
                    if (item.id !== 'details') setSelectedIncidentId(null);
                  }}
                >
                  {item.icon}
                  <span style={{ flexGrow: 1 }}>{item.label}</span>
                  {item.badge && (
                    <span className="badge badge-warning" style={{ fontSize: '0.65rem', padding: '0.1rem 0.35rem' }}>
                      {item.badge}
                    </span>
                  )}
                </button>
              </li>
            );
          })}
        </ul>

        <div className="sidebar-footer">
          <div>ENGINEERING VIVA PROTOTYPE</div>
          <div className="sys-health-pill">
            <span className={`health-dot ${
              systemHealth.status === 'offline' ? 'dot-red' :
              systemHealth.overall_health === 'HEALTHY' ? 'dot-green' :
              systemHealth.overall_health === 'DEGRADED' ? 'dot-yellow' : 'dot-red'
            }`} />
            <span>
              {systemHealth.status === 'offline' ? 'Backend Disconnected' : `${systemHealth.overall_health} CLUSTER`}
            </span>
          </div>
          <div style={{ marginTop: '0.3rem', fontSize: '0.68rem', color: 'var(--text-dim)' }}>
            LLM: {systemHealth.llm_active ? 'Groq Active' : 'Deterministic Fallback'}
          </div>
        </div>
      </aside>

      {/* Main App Content */}
      <div className="main-content">
        <header className="top-bar">
          <div className="page-title-box">
            <h1>
              {navItems.find((n) => n.id === currentTab)?.label || 
               (currentTab === 'details' ? `Incident Details #${selectedIncidentId}` : 'TraceMind AI')}
            </h1>
            <p>Autonomous Multi-Agent Telemetry & Orchestration Engine</p>
          </div>

          <div className="top-bar-actions">
            {currentTab !== 'simulation' && (
              <button 
                className="btn btn-secondary btn-sm"
                onClick={() => setCurrentTab('simulation')}
              >
                <PlayCircle size={14} /> Inject Fault Simulation
              </button>
            )}

            {currentTab !== 'approval' && systemHealth.active_incidents_count > 0 && (
              <button 
                className="btn btn-warning btn-sm"
                style={{ backgroundColor: '#f59e0b', color: '#000' }}
                onClick={() => setCurrentTab('approval')}
              >
                <ShieldCheck size={14} /> {systemHealth.active_incidents_count} Pending Review
              </button>
            )}
          </div>
        </header>

        <main className="content-body">
          {currentTab === 'overview' && (
            <DashboardOverview 
              onSelectIncident={handleSelectIncident}
              onNavigate={setCurrentTab}
            />
          )}

          {currentTab === 'services' && (
            <ServicesMonitoring />
          )}

          {currentTab === 'incidents' && (
            <IncidentManagement 
              onSelectIncident={handleSelectIncident}
              onNavigate={setCurrentTab}
            />
          )}

          {currentTab === 'details' && selectedIncidentId && (
            <IncidentDetails 
              incidentId={selectedIncidentId}
              onBack={() => setCurrentTab('incidents')}
              onNavigate={setCurrentTab}
            />
          )}

          {currentTab === 'agents' && (
            <AgentActivity />
          )}

          {currentTab === 'observability' && (
            <ObservabilityEval />
          )}

          {currentTab === 'simulation' && (
            <SimulationCenter 
              onSelectIncident={handleSelectIncident}
              onNavigate={setCurrentTab}
            />
          )}

          {currentTab === 'approval' && (
            <RemediationApproval 
              onSelectIncident={handleSelectIncident}
            />
          )}

          {currentTab === 'reports' && (
            <IncidentReports 
              onSelectIncident={handleSelectIncident}
            />
          )}
        </main>
      </div>
    </div>
  );
}
