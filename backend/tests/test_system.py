import pytest
from fastapi.testclient import TestClient
from backend.app import app
from backend.database import init_db
from backend.agents.monitoring import run_monitoring_agent
from backend.agents.rca import run_rca_agent, deterministic_rca
from backend.agents.remediation import validate_remediation_safety, run_remediation_recommendation
from backend.agents.verification import run_verification_agent
from backend.simulation import simulation_engine

# Initialize database tables for tests
init_db()

client = TestClient(app)

def test_health_and_system_status():
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert "TraceMind AI" in data["app_name"]

    res_sys = client.get("/api/system/status")
    assert res_sys.status_code == 200
    sys_data = res_sys.json()
    assert "overall_health" in sys_data
    assert "services_count" in sys_data


def test_services_monitoring():
    res = client.get("/api/services")
    assert res.status_code == 200
    services = res.json()["services"]
    assert len(services) == 5
    service_ids = [s["service_id"] for s in services]
    assert "order-processing-service" in service_ids
    assert "payment-service" in service_ids


def test_simulation_scenarios_and_reset():
    res = client.get("/api/simulation/scenarios")
    assert res.status_code == 200
    scenarios = res.json()["scenarios"]
    assert "high_cpu" in scenarios
    assert "memory_exhaustion" in scenarios
    assert "db_failure" in scenarios
    assert "api_latency" in scenarios
    assert "http_500" in scenarios

    # Reset
    reset_res = client.post("/api/simulation/reset")
    assert reset_res.status_code == 200
    assert reset_res.json()["status"] == "success"


def test_monitoring_agent_detection():
    # Trigger CPU spike in simulation
    simulation_engine.trigger_scenario("high_cpu")
    
    state = {
        "incident_id": "TEST-INC-01",
        "scenario_type": "high_cpu",
        "affected_service": "order-processing-service",
        "agent_logs": []
    }
    
    monitored = run_monitoring_agent(state)
    assert monitored["status"] == "Detected"
    assert len(monitored["detected_anomalies"]) > 0
    assert any("CPU utilization" in a for a in monitored["detected_anomalies"])
    
    # Cleanup
    simulation_engine.reset()


def test_rca_agent_evidence_generation():
    anomalies = ["[order-processing-service] CPU utilization (94.8%) exceeded critical threshold of 80.0%"]
    logs = [{"service_id": "order-processing-service", "message": "Thread pool saturation: CPU utilization exceeded 90%"}]
    telemetry = {"cpu_usage": 94.8, "response_time_ms": 2450.0}

    root_cause, confidence, evidence, alt_causes, explanation = deterministic_rca(
        "high_cpu", "order-processing-service", anomalies, logs, telemetry
    )

    assert "CPU" in root_cause or "thread pool" in root_cause.lower()
    assert confidence > 0.85
    assert len(evidence) > 0
    assert len(alt_causes) > 0
    assert len(explanation) > 0


def test_remediation_safety_validation():
    # Valid action
    is_safe, msg = validate_remediation_safety("scale_down_workload", "order-processing-service")
    assert is_safe is True

    # Invalid action (arbitrary shell command attempt should fail)
    is_safe_bad, msg_bad = validate_remediation_safety("rm -rf /", "order-processing-service")
    assert is_safe_bad is False
    assert "Safety Violation" in msg_bad

    # Invalid target service
    is_safe_target, msg_target = validate_remediation_safety("scale_down_workload", "unauthorized-service")
    assert is_safe_target is False


def test_full_incident_lifecycle_workflow():
    """
    Test complete end-to-end lifecycle:
    Trigger scenario -> Monitoring -> RCA -> Approval Request -> Approval Execution -> Verification -> Report
    """
    # 1. Trigger database failure scenario
    trig_res = client.post("/api/simulation/trigger/db_failure")
    assert trig_res.status_code == 200
    trig_data = trig_res.json()
    incident_id = trig_data["incident"]["id"]
    assert trig_data["incident"]["affected_service"] == "payment-service"
    assert trig_data["incident"]["recommended_action"] == "reset_db_connection_pool"
    assert trig_data["incident"]["risk_level"] == "HIGH"
    assert trig_data["incident"]["approval_status"] == "PENDING"

    # 2. Inspect incident details
    inc_res = client.get(f"/api/incidents/{incident_id}")
    assert inc_res.status_code == 200
    details = inc_res.json()
    assert len(details["agent_executions"]) >= 2  # Monitoring & RCA logged
    assert "payment-service" in details["incident"]["affected_service"]

    # 3. Approve remediation
    appr_res = client.post(
        f"/api/remediation/{incident_id}/approve",
        json={"approved": True, "approver_name": "DevOps Engineer Lead", "notes": "Approved for emergency recovery"}
    )
    assert appr_res.status_code == 200
    appr_data = appr_res.json()
    assert appr_data["incident"]["approval_status"] == "EXECUTED"
    assert appr_data["incident"]["status"] == "Resolved"
    assert appr_data["incident"]["verification_status"] == "Resolved"

    # 4. Verification Check
    verif_res = client.get(f"/api/verification/{incident_id}")
    assert verif_res.status_code == 200
    verif_data = verif_res.json()
    assert verif_data["is_resolved"] is True
    assert "metric_deltas" in verif_data

    # 5. Report generation and download
    rep_res = client.get(f"/api/reports/{incident_id}")
    assert rep_res.status_code == 200
    rep_data = rep_res.json()
    assert rep_data["final_status"] == "Resolved"
    assert "reset_db_connection_pool" in rep_data["remediation_action"]
    assert "Incident Report" in rep_data["summary_markdown"]

    down_res = client.get(f"/api/reports/{incident_id}/download")
    assert down_res.status_code == 200
    assert "text/markdown" in down_res.headers["content-type"]

    # Cleanup
    simulation_engine.reset()


def test_all_five_scenarios_trigger():
    """Verify that all 5 required scenarios trigger and can be diagnosed."""
    scenarios = ["high_cpu", "memory_exhaustion", "db_failure", "api_latency", "http_500"]
    for sc in scenarios:
        res = client.post(f"/api/simulation/trigger/{sc}")
        assert res.status_code == 200
        data = res.json()
        assert data["incident"]["scenario_type"] == sc
        assert data["incident"]["root_cause"] is not None
        assert data["incident"]["confidence_score"] > 0.5
        simulation_engine.reset()


def test_crewai_and_adk_frameworks():
    """Verify ONLY CrewAI and Google ADK are configured as the agentic frameworks."""
    res = client.get("/api/agents")
    assert res.status_code == 200
    data = res.json()
    assert set(data["frameworks"]) == {"CrewAI", "Google ADK"}
    frameworks_used = {a["framework"] for a in data["agents"]}
    assert frameworks_used == {"CrewAI", "Google ADK"}


def test_live_evaluation_suite():
    """Run live agent evaluation across all 5 scenarios and verify 100% pass rate."""
    res = client.post("/api/evaluation/run")
    assert res.status_code == 200
    data = res.json()
    assert data["scenarios_tested"] == 5
    assert data["scenarios_passed"] == 5
    assert data["overall_pass_rate_percent"] == 100.0


def test_observability_prometheus_and_cost():
    """Verify Grafana/Prometheus /metrics endpoint, observability JSON, and cost estimation."""
    prom = client.get("/metrics")
    assert prom.status_code == 200
    assert "tracemind_agent_eval_pass_rate" in prom.text
    assert "tracemind_estimated_cost_usd" in prom.text

    obs = client.get("/api/observability/metrics")
    assert obs.status_code == 200
    assert "service_series" in obs.json()

    cost = client.get("/api/cost/estimate?monthly_incidents=1000")
    assert cost.status_code == 200
    cost_data = cost.json()
    assert cost_data["projected_monthly"]["selected_volume"] == 1000
    assert len(cost_data["volume_tiers"]) == 3
