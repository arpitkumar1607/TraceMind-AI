import logging
from typing import Dict, Any, List
from backend.agents.state import IncidentState
from backend.agents.adk_agents import (
    run_adk_monitoring,
    run_adk_verification,
    get_adk_agent_specs,
)
from backend.agents.crewai_agents import (
    run_crewai_rca,
    run_crewai_remediation_recommendation,
    run_crewai_remediation_execution,
    get_crewai_agent_specs,
)

logger = logging.getLogger("tracemind.agents.workflow")


def get_all_agent_specs() -> List[Dict[str, Any]]:
    """Return unified agent definitions across Google ADK and CrewAI."""
    adk_specs = {a["id"]: a for a in get_adk_agent_specs()}
    crew_specs = {a["id"]: a for a in get_crewai_agent_specs()}
    return [
        adk_specs["monitoring_agent"],
        crew_specs["rca_agent"],
        crew_specs["remediation_agent"],
        adk_specs["verification_agent"],
    ]


def run_incident_investigation(initial_state: IncidentState) -> IncidentState:
    """
    Executes the investigation pipeline using ONLY Google ADK + CrewAI:
    1. Google ADK Monitoring Agent -> Telemetry & Anomaly Detection
    2. CrewAI RCA Agent -> Root-Cause Analysis & Evidence Correlation
    3. CrewAI Remediation Agent -> Whitelisted Action & HITL Safety Check
    """
    logger.info("Starting CrewAI + Google ADK investigation workflow for %s", initial_state.get("incident_id"))
    state = run_adk_monitoring(initial_state)
    state = run_crewai_rca(state)
    state = run_crewai_remediation_recommendation(state)
    return state


def run_incident_execution_and_verification(state: IncidentState) -> IncidentState:
    """
    Executes the post-approval pipeline using ONLY CrewAI + Google ADK:
    1. CrewAI Remediation Agent -> Controlled Simulation Execution
    2. Google ADK Verification Agent -> Post-Recovery Health & Metric Delta Verification
    """
    logger.info("Executing CrewAI remediation & Google ADK verification for %s", state.get("incident_id"))
    state = run_crewai_remediation_execution(state)
    state = run_adk_verification(state)
    return state
