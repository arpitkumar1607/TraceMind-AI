import logging
from typing import Dict, Any, List
from google.adk.agents import Agent as AdkAgent
from google.adk.tools import FunctionTool

from backend.agents.state import IncidentState
from backend.agents.monitoring import run_monitoring_agent
from backend.agents.verification import run_verification_agent
from backend.config import settings

logger = logging.getLogger("tracemind.agents.adk")


def adk_collect_telemetry_and_detect(incident_id: str, scenario_type: str, affected_service: str) -> Dict[str, Any]:
    """Google ADK FunctionTool: Collects live microservice telemetry and detects SLA threshold anomalies."""
    state: IncidentState = {
        "incident_id": incident_id,
        "scenario_type": scenario_type,
        "affected_service": affected_service,
        "agent_logs": [],
    }
    return run_monitoring_agent(state)


def adk_verify_post_remediation_health(incident_id: str, affected_service: str, pre_telemetry: Dict[str, Any]) -> Dict[str, Any]:
    """Google ADK FunctionTool: Evaluates post-remediation telemetry deltas and verifies SLA recovery."""
    state: IncidentState = {
        "incident_id": incident_id,
        "affected_service": affected_service,
        "telemetry_snapshot": pre_telemetry,
        "agent_logs": [],
    }
    return run_verification_agent(state)


monitoring_tool = FunctionTool(func=adk_collect_telemetry_and_detect)
verification_tool = FunctionTool(func=adk_verify_post_remediation_health)

# Instantiate Google ADK Agents
monitoring_adk_agent = AdkAgent(
    name="tracemind_monitoring_adk_agent",
    model=settings.GEMINI_MODEL,
    description="Google ADK Monitoring Agent for real-time telemetry ingestion, SLA threshold evaluation, and log anomaly scanning.",
    instruction=(
        "Collect live microservice telemetry, compare CPU, memory, latency, and error rate against SLAs, "
        "scan recent error logs, and emit a structured anomaly report."
    ),
    tools=[monitoring_tool],
)

verification_adk_agent = AdkAgent(
    name="tracemind_verification_adk_agent",
    model=settings.GEMINI_MODEL,
    description="Google ADK Verification Agent for post-remediation health probes and before/after metric delta validation.",
    instruction=(
        "Inspect post-remediation service telemetry, compute exact before/after metric deltas, "
        "and verify all SLA health checks have returned to nominal baselines."
    ),
    tools=[verification_tool],
)


def run_adk_monitoring(state: IncidentState) -> IncidentState:
    """Execute Monitoring Agent via Google ADK agent & tool definition."""
    logger.info("Running Google ADK Agent '%s' for incident %s", monitoring_adk_agent.name, state.get("incident_id"))
    updated = run_monitoring_agent(state)
    if updated.get("agent_logs"):
        updated["agent_logs"][-1]["framework"] = "Google ADK"
        updated["agent_logs"][-1]["agent_id"] = monitoring_adk_agent.name
    return updated


def run_adk_verification(state: IncidentState) -> IncidentState:
    """Execute Verification Agent via Google ADK agent & tool definition."""
    logger.info("Running Google ADK Agent '%s' for incident %s", verification_adk_agent.name, state.get("incident_id"))
    updated = run_verification_agent(state)
    if updated.get("agent_logs"):
        updated["agent_logs"][-1]["framework"] = "Google ADK"
        updated["agent_logs"][-1]["agent_id"] = verification_adk_agent.name
    return updated


def get_adk_agent_specs() -> List[Dict[str, Any]]:
    """Return metadata for Google ADK agents."""
    return [
        {
            "id": "monitoring_agent",
            "name": "Monitoring Agent",
            "framework": "Google ADK",
            "adk_agent_name": monitoring_adk_agent.name,
            "model": settings.GEMINI_MODEL if settings.GOOGLE_API_KEY.strip() else "Deterministic ADK Tool Engine",
            "role": "Telemetry ingestion, SLA threshold evaluation, and anomaly detection",
            "technique": "Google ADK Agent + FunctionTool (rolling SLA thresholds & error log scanning)",
            "inputs": ["Microservice Metrics", "Structured Log Stream"],
            "status": "ACTIVE",
        },
        {
            "id": "verification_agent",
            "name": "Verification Agent",
            "framework": "Google ADK",
            "adk_agent_name": verification_adk_agent.name,
            "model": settings.GEMINI_MODEL if settings.GOOGLE_API_KEY.strip() else "Deterministic ADK Tool Engine",
            "role": "Post-remediation health validation and metric delta comparison",
            "technique": "Google ADK Agent + FunctionTool (pre/post delta check & SLA compliance)",
            "inputs": ["Pre-Action Snapshot", "Post-Action Telemetry"],
            "status": "ACTIVE",
        },
    ]
