import React, { useEffect, useState } from 'react';
import { api } from '../api';
import { Server, RefreshCw, AlertCircle, CheckCircle2 } from 'lucide-react';

export default function ServicesMonitoring() {
  const [services, setServices] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchServices = async () => {
    try {
      const data = await api.getServices();
      setServices(data.services || []);
    } catch (err) {
      console.error("Error fetching services", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchServices();
    const interval = setInterval(fetchServices, 3000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="card">
      <div className="card-title" style={{ justifyContent: 'space-between' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <Server size={18} /> Distributed Service Topology & Telemetry
        </div>
        <button className="btn btn-secondary btn-sm" onClick={fetchServices}>
          <RefreshCw size={14} /> Refresh
        </button>
      </div>

      <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '1.25rem' }}>
        Live telemetry collected from simulated microservices. Threshold alerts: CPU &gt; 80%, Memory &gt; 80%, Latency &gt; 1000ms.
      </p>

      <div className="table-container">
        <table className="data-table">
          <thead>
            <tr>
              <th>SERVICE ID</th>
              <th>NAME</th>
              <th>HEALTH STATUS</th>
              <th>CPU USAGE</th>
              <th>MEMORY USAGE</th>
              <th>LATENCY</th>
              <th>REQUESTS</th>
              <th>ERRORS</th>
              <th>ERROR RATE</th>
            </tr>
          </thead>
          <tbody>
            {services.map((svc) => {
              const isDegraded = svc.status === 'DEGRADED';
              const isUnhealthy = svc.status === 'UNHEALTHY';
              const rowStyle = isUnhealthy 
                ? { backgroundColor: 'rgba(239, 68, 68, 0.08)' } 
                : isDegraded 
                ? { backgroundColor: 'rgba(245, 158, 11, 0.08)' } 
                : {};

              return (
                <tr key={svc.service_id} style={rowStyle}>
                  <td style={{ fontFamily: 'var(--font-mono)', fontWeight: 600 }}>{svc.service_id}</td>
                  <td style={{ fontWeight: 500 }}>{svc.name}</td>
                  <td>
                    <span className={`badge ${
                      isUnhealthy ? 'badge-danger' : isDegraded ? 'badge-warning' : 'badge-success'
                    }`}>
                      {isUnhealthy ? <AlertCircle size={12} /> : <CheckCircle2 size={12} />}
                      {svc.status}
                    </span>
                  </td>
                  <td>
                    <span style={{ 
                      fontWeight: svc.cpu_usage > 80 ? 700 : 400,
                      color: svc.cpu_usage > 80 ? '#f87171' : 'inherit'
                    }}>
                      {svc.cpu_usage}%
                    </span>
                  </td>
                  <td>
                    <span style={{ 
                      fontWeight: svc.memory_usage > 80 ? 700 : 400,
                      color: svc.memory_usage > 80 ? '#f87171' : 'inherit'
                    }}>
                      {svc.memory_usage}%
                    </span>
                  </td>
                  <td>
                    <span style={{ 
                      fontWeight: svc.response_time_ms > 1000 ? 700 : 400,
                      color: svc.response_time_ms > 1000 ? '#fbbf24' : 'inherit'
                    }}>
                      {svc.response_time_ms} ms
                    </span>
                  </td>
                  <td>{svc.request_count}</td>
                  <td>
                    <span style={{ color: svc.error_count > 0 ? '#f87171' : 'inherit' }}>
                      {svc.error_count}
                    </span>
                  </td>
                  <td>
                    <span className={`badge ${svc.error_rate > 5 ? 'badge-danger' : 'badge-info'}`}>
                      {svc.error_rate}%
                    </span>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
