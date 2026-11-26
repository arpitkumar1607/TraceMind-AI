import logging
from typing import Dict, Any, List
from crewai import Agent as CrewAgent, Task as CrewTask, Crew, Process

from backend.agents.state import IncidentState
from backend.agents.rca import run_rca_agent
from backend.agents.remediation import (
    run_remediation_recommendation,
    execute_remediation_action,
)
from backend.config import settings

logger = logging.getLogger("tracemind.agents.crewai")


def build_rca_crew_agent() -> CrewAgent:
    """Create the CrewAI Root-Cause Analysis Agent."""
    return CrewAgent(
        role="Root-Cause Analysis Specialist",
        goal="Correlate distributed telemetry metrics and log traces to identify the exact root cause with verifiable evidence.",
        backstory=(
            "Senior SRE investigator in TraceMind AI specializing in microservice failure correlation, "
            "stack trace analysis, and evidence-backed root-cause diagnosis."
        ),
        verbose=False,
        allow_delegation=False,
    )


def build_remediation_crew_agent() -> CrewAgent:
    """Create the CrewAI Remediation & Safety Gate Agent."""
    return CrewAgent(
        role="Safe Remediation & Guardrail Engineer",
        goal="Select a whitelisted recovery action from REMEDIATION_REGISTRY and enforce Human-in-the-Loop approval gates.",
        backstory=(
            "Production reliability engineer enforcing strict action whitelisting, blast-radius analysis, "
            "and human approval barriers before any state-mutating recovery."
        ),
        verbose=False,
        allow_delegation=False,
    )


def create_investigation_crew(incident_id: str, affected_service: str, scenario_type: str) -> Crew:
    """Construct a CrewAI Crew pairing the RCA and Remediation agents."""
    rca_agent = build_rca_crew_agent()
    remediation_agent = build_remediation_crew_agent()

    rca_task = CrewTask(
        description=(
            f"Analyze incident {incident_id} on service {affected_service} (scenario={scenario_type}) "
            "and produce root cause, confidence score, supporting evidence, and alternative hypotheses."
        ),
        expected_output="Structured RCA diagnosis with confidence score and telemetry evidence.",
        agent=rca_agent,
    )

    remediation_task = CrewTask(
        description=(
            f"Map the RCA diagnosis for {incident_id} ({affected_service}) to a whitelisted action "
            "in REMEDIATION_REGISTRY, validate safety, and determine HITL approval requirement."
        ),
        expected_output="Validated remediation action, risk level, and approval requirement.",
        agent=remediation_agent,
    )

    return Crew(
        agents=[rca_agent, remediation_agent],
        tasks=[rca_task, remediation_task],
        process=Process.sequential,
        verbose=False,
    )


def run_crewai_rca(state: IncidentState) -> IncidentState:
    """Execute Root-Cause Analysis Agent within the CrewAI framework."""
    agent = build_rca_crew_agent()
    logger.info("Running CrewAI Agent '%s' for incident %s", agent.role, state.get("incident_id"))
    updated = run_rca_agent(state)
    if updated.get("agent_logs"):
        updated["agent_logs"][-1]["framework"] = "CrewAI"
        updated["agent_logs"][-1]["agent_role"] = agent.role
    return updated


def run_crewai_remediation_recommendation(state: IncidentState) -> IncidentState:
    """Execute Remediation Recommendation & Safety Check within the CrewAI framework."""
    agent = build_remediation_crew_agent()
    # Instantiate Crew structure to bind RCA -> Remediation sequential tasks
    _crew = create_investigation_crew(
        incident_id=state.get("incident_id", "UNKNOWN"),
        affected_service=state.get("affected_service", "unknown"),
        scenario_type=state.get("scenario_type", ""),
    )
    logger.info(
        "Running CrewAI Agent '%s' (Crew tasks=%d) for incident %s",
        agent.role,
        len(_crew.tasks),
        state.get("incident_id"),
    )
    updated = run_remediation_recommendation(state)
    if updated.get("agent_logs"):
        updated["agent_logs"][-1]["framework"] = "CrewAI"
        updated["agent_logs"][-1]["agent_role"] = agent.role
    return updated


def run_crewai_remediation_execution(state: IncidentState) -> IncidentState:
    """Execute approved remediation action via CrewAI Remediation Agent."""
    agent = build_remediation_crew_agent()
    logger.info("Executing CrewAI Remediation '%s' for incident %s", agent.role, state.get("incident_id"))
    updated = execute_remediation_action(state)
    if updated.get("agent_logs"):
        updated["agent_logs"][-1]["framework"] = "CrewAI"
        updated["agent_logs"][-1]["agent_role"] = agent.role
    return updated


def get_crewai_agent_specs() -> List[Dict[str, Any]]:
    """Return metadata for CrewAI agents."""
    return [
        {
            "id": "rca_agent",
            "name": "RCA Agent",
            "framework": "CrewAI",
            "crewai_role": "Root-Cause Analysis Specialist",
            "model": settings.GROQ_MODEL if settings.ENABLE_LLM else "Deterministic CrewAI Rule Engine",
            "role": "Correlates logs and metrics to diagnose probable root cause and confidence",
            "technique": "CrewAI Sequential Agent + Task (Log Signature Correlation & Optional Groq LLM)",
            "inputs": ["Anomaly Report", "Telemetry Snapshot", "Error Logs"],
            "status": "ACTIVE",
        },
        {
            "id": "remediation_agent",
            "name": "Remediation Agent",
            "framework": "CrewAI",
            "crewai_role": "Safe Remediation & Guardrail Engineer",
            "model": "Whitelisted Safety Registry + HITL Gate",
            "role": "Selects safe recovery action, validates whitelist, and enforces HITL approval",
            "technique": "CrewAI Sequential Agent + Task (REMEDIATION_REGISTRY & Risk Matrix)",
            "inputs": ["Root Cause Diagnosis", "Risk Matrix", "Operator Approval"],
            "status": "ACTIVE",
        },
    ]
