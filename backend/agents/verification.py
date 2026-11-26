import logging
from datetime import datetime, timezone
from typing import Dict, Any
from backend.agents.state import IncidentState
from backend.simulation import simulation_engine

logger = logging.getLogger("tracemind.agents.verification")

def run_verification_agent(state: IncidentState) -> IncidentState:
    """
    Agent 4: Verification Agent
    Measures post-remediation telemetry, calculates metric deltas against pre-incident baseline,
    and independently verifies if the application has returned to a healthy state.
    """
    logger.info("Verification Agent inspecting recovery for incident: %s", state.get("incident_id"))
    start_time = datetime.now(timezone.utc)
    
    affected_service = state.get("affected_service", "")
    pre_metrics = state.get("telemetry_snapshot", {})
    
    # 1. Fetch current post-remediation telemetry
    post_service_metrics = simulation_engine.get_service(affected_service) or {}
    
    pre_cpu = float(pre_metrics.get("cpu_usage", 0.0))
    post_cpu = float(post_service_metrics.get("cpu_usage", 0.0))
    cpu_delta = round(post_cpu - pre_cpu, 1)

    pre_mem = float(pre_metrics.get("memory_usage", 0.0))
    post_mem = float(post_service_metrics.get("memory_usage", 0.0))
    mem_delta = round(post_mem - pre_mem, 1)

    pre_lat = float(pre_metrics.get("response_time_ms", 0.0))
    post_lat = float(post_service_metrics.get("response_time_ms", 0.0))
    lat_delta = round(post_lat - pre_lat, 1)

    pre_err = float(pre_metrics.get("error_rate", 0.0))
    post_err = float(post_service_metrics.get("error_rate", 0.0))
    err_delta = round(post_err - pre_err, 2)

    metric_deltas = {
        "cpu_usage": {"before": pre_cpu, "after": post_cpu, "delta": cpu_delta, "unit": "%"},
        "memory_usage": {"before": pre_mem, "after": post_mem, "delta": mem_delta, "unit": "%"},
        "response_time_ms": {"before": pre_lat, "after": post_lat, "delta": lat_delta, "unit": "ms"},
        "error_rate": {"before": pre_err, "after": post_err, "delta": err_delta, "unit": "%"}
    }

    # 2. Independent health evaluation
    service_status = post_service_metrics.get("status", "HEALTHY")
    is_cpu_healthy = post_cpu < 80.0
    is_mem_healthy = post_mem < 80.0
    is_lat_healthy = post_lat < 1000.0
    is_err_healthy = post_err < 5.0
    health_check_passed = (service_status == "HEALTHY" and is_cpu_healthy and is_mem_healthy and is_lat_healthy and is_err_healthy)

    if health_check_passed:
        verification_status = "Resolved"
        is_resolved = True
        notes = (
            f"All health verification checks passed for {affected_service}. "
            f"Latency improved by {-lat_delta}ms, error rate dropped to {post_err}%, "
            f"and CPU/memory utilization returned within nominal thresholds."
        )
    elif post_err < pre_err or post_lat < pre_lat:
        verification_status = "Partially Resolved"
        is_resolved = False
        notes = f"Partial recovery observed. Metrics improved but service {affected_service} has not yet cleared all SLA thresholds."
    else:
        verification_status = "Failed"
        is_resolved = False
        notes = f"Verification failed. Post-remediation metrics remain abnormal on service {affected_service}."

    duration_ms = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
    now_iso = datetime.now(timezone.utc).isoformat()

    agent_entry = {
        "agent": "Verification Agent",
        "action": "POST_REMEDIATION_HEALTH_VERIFICATION",
        "timestamp": now_iso,
        "duration_ms": round(duration_ms, 2),
        "status": "COMPLETED",
        "summary": f"Result: {verification_status}. Health Check: {'PASSED' if health_check_passed else 'FAILED'}. {notes}"
    }

    logs_copy = list(state.get("agent_logs", []))
    logs_copy.append(agent_entry)

    return {
        **state,
        "status": verification_status,
        "is_resolved": is_resolved,
        "verification_status": verification_status,
        "post_telemetry": post_service_metrics,
        "metric_deltas": metric_deltas,
        "verification_notes": notes,
        "resolved_at": now_iso if is_resolved else None,
        "agent_logs": logs_copy
    }
