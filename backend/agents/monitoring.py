import logging
from datetime import datetime, timezone
from typing import Dict, Any, List
from backend.agents.state import IncidentState
from backend.simulation import simulation_engine

logger = logging.getLogger("tracemind.agents.monitoring")

CPU_THRESHOLD = 80.0
MEMORY_THRESHOLD = 80.0
LATENCY_THRESHOLD_MS = 1000.0
ERROR_RATE_THRESHOLD = 5.0

def run_monitoring_agent(state: IncidentState) -> IncidentState:
    """
    Agent 1: Monitoring Agent
    Collects live telemetry from services, parses log streams, calculates metric ratios,
    and identifies anomalous behaviour based on defined thresholds.
    """
    logger.info("Monitoring Agent initiated for incident: %s", state.get("incident_id"))
    start_time = datetime.now(timezone.utc)
    
    # 1. Fetch current telemetry snapshot from simulation engine
    services_snapshot = simulation_engine.get_services_snapshot()
    recent_logs = simulation_engine.get_recent_logs(limit=20)
    
    anomalies: List[str] = []
    affected_service = state.get("affected_service")
    severity = "LOW"
    target_service_metrics: Dict[str, Any] = {}
    
    # 2. Threshold calculations on services
    for svc in services_snapshot:
        s_id = svc["service_id"]
        cpu = svc["cpu_usage"]
        mem = svc["memory_usage"]
        lat = svc["response_time_ms"]
        err_rate = svc["error_rate"]
        
        svc_anomalies = []
        if cpu > CPU_THRESHOLD:
            svc_anomalies.append(f"CPU utilization ({cpu}%) exceeded critical threshold of {CPU_THRESHOLD}%")
        if mem > MEMORY_THRESHOLD:
            svc_anomalies.append(f"Memory consumption ({mem}%) exceeded safe threshold of {MEMORY_THRESHOLD}%")
        if lat > LATENCY_THRESHOLD_MS:
            svc_anomalies.append(f"Response latency ({lat}ms) breached SLA limit of {LATENCY_THRESHOLD_MS}ms")
        if err_rate > ERROR_RATE_THRESHOLD:
            svc_anomalies.append(f"Error rate ({err_rate}%) exceeded anomaly limit of {ERROR_RATE_THRESHOLD}%")
            
        if svc_anomalies:
            anomalies.extend([f"[{s_id}] {a}" for a in svc_anomalies])
            if not affected_service or svc["status"] in ["DEGRADED", "UNHEALTHY"]:
                affected_service = s_id
                target_service_metrics = svc
                
    # 3. Log pattern inspection
    error_logs = [l for l in recent_logs if l["level"] in ["ERROR", "FATAL"]]
    if error_logs:
        anomalies.append(f"Detected {len(error_logs)} high-severity error logs in telemetry stream")
        if not target_service_metrics and error_logs:
            affected_service = error_logs[-1]["service_id"]

    # 4. Determine overall severity
    if any("exceeded critical threshold" in a or "FATAL" in str(error_logs) for a in anomalies):
        severity = "CRITICAL"
    elif anomalies:
        severity = "HIGH" if len(anomalies) > 1 else "MEDIUM"
        
    if not target_service_metrics and affected_service:
        target_service_metrics = simulation_engine.get_service(affected_service) or {}

    duration_ms = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000

    agent_entry = {
        "agent": "Monitoring Agent",
        "action": "TELEMETRY_ANOMALY_DETECTION",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "duration_ms": round(duration_ms, 2),
        "status": "COMPLETED",
        "summary": f"Detected {len(anomalies)} anomalies across service topology. Primary affected service: {affected_service}"
    }

    logs_copy = list(state.get("agent_logs", []))
    logs_copy.append(agent_entry)

    # Return updated state
    return {
        **state,
        "status": "Detected" if anomalies else "Healthy",
        "affected_service": affected_service or "system",
        "severity": severity,
        "detected_anomalies": anomalies,
        "telemetry_snapshot": target_service_metrics or {"services": services_snapshot},
        "recent_logs": recent_logs,
        "agent_logs": logs_copy
    }
