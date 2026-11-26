const BASE_URL = import.meta.env.VITE_API_URL || '';

async function fetchJSON(endpoint, options = {}) {
  const url = `${BASE_URL}${endpoint}`;
  const response = await fetch(url, {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    ...options,
  });

  if (!response.ok) {
    let errorDetail = 'Request failed';
    try {
      const err = await response.json();
      errorDetail = err.detail || JSON.stringify(err);
    } catch {
      errorDetail = await response.text();
    }
    throw new Error(errorDetail || `HTTP error ${response.status}`);
  }

  return response.json();
}

export const api = {
  // System
  getHealth: () => fetchJSON('/api/health'),
  getSystemStatus: () => fetchJSON('/api/system/status'),

  // Dashboard
  getDashboardSummary: () => fetchJSON('/api/dashboard/summary'),
  getDashboardMetrics: () => fetchJSON('/api/dashboard/metrics'),

  // Services
  getServices: () => fetchJSON('/api/services'),
  getService: (id) => fetchJSON(`/api/services/${id}`),

  // Simulation
  getSimulationScenarios: () => fetchJSON('/api/simulation/scenarios'),
  triggerScenario: (scenario) => fetchJSON(`/api/simulation/trigger/${scenario}`, { method: 'POST' }),
  resetSimulation: () => fetchJSON('/api/simulation/reset', { method: 'POST' }),
  getSimulationLogs: (limit = 40) => fetchJSON(`/api/simulation/logs?limit=${limit}`),

  // Incidents
  getIncidents: () => fetchJSON('/api/incidents'),
  getIncidentDetails: (id) => fetchJSON(`/api/incidents/${id}`),
  investigateIncident: (id) => fetchJSON(`/api/incidents/investigate/${id}`, { method: 'POST' }),

  // Agents
  getAgents: () => fetchJSON('/api/agents'),
  getAgentActivity: () => fetchJSON('/api/agents/activity'),

  // Remediation
  getRemediationInfo: (id) => fetchJSON(`/api/remediation/${id}`),
  approveRemediation: (id, approved = true, approverName = 'Lead Engineer', notes = '') =>
    fetchJSON(`/api/remediation/${id}/approve`, {
      method: 'POST',
      body: JSON.stringify({ approved, approver_name: approverName, notes }),
    }),
  rejectRemediation: (id) => fetchJSON(`/api/remediation/${id}/reject`, { method: 'POST' }),
  executeRemediation: (id) => fetchJSON(`/api/remediation/${id}/execute`, { method: 'POST' }),

  // Verification
  getVerificationDetails: (id) => fetchJSON(`/api/verification/${id}`),
  triggerVerification: (id) => fetchJSON(`/api/verification/${id}`, { method: 'POST' }),

  // Reports
  getReports: () => fetchJSON('/api/reports'),
  getIncidentReport: (id) => fetchJSON(`/api/reports/${id}`),
  downloadReportUrl: (id) => `${BASE_URL}/api/reports/${id}/download`,

  // Grafana Observability, Live Agent Evaluation & Cost Estimation
  getObservabilityMetrics: () => fetchJSON('/api/observability/metrics'),
  runLiveEvaluation: () => fetchJSON('/api/evaluation/run', { method: 'POST' }),
  getLatestEvaluation: () => fetchJSON('/api/evaluation/latest'),
  getCostEstimation: (monthlyIncidents = 1000) =>
    fetchJSON(`/api/cost/estimate?monthly_incidents=${monthlyIncidents}`),
};
