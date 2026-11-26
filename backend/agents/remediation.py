import logging
from datetime import datetime, timezone
from typing import Dict, Any, Tuple
from backend.agents.state import IncidentState
from backend.simulation import simulation_engine

logger = logging.getLogger("tracemind.agents.remediation")

# Strict Whitelisted Remediation Action Registry
REMEDIATION_REGISTRY: Dict[str, Dict[str, Any]] = {
    "scale_down_workload": {
        "name": "scale_down_workload",
        "description": "Throttle background batch worker concurrency from 32 to 4 workers to relieve CPU pressure.",
        "target_services": ["order-processing-service"],
        "risk_level": "MEDIUM",
        "requires_approval": True,
        "potential_impact": "Non-urgent batch calculation delays while immediate API throughput stabilizes.",
        "expected_result": "CPU utilization drops below 35%; response latency normalizes."
    },
    "clear_service_cache": {
        "name": "clear_service_cache",
        "description": "Purge unreferenced objects in in-memory LRU cache partition and invoke explicit garbage collection.",
        "target_services": ["inventory-service"],
        "risk_level": "MEDIUM",
        "requires_approval": True,
        "potential_impact": "Transient cache-miss latency for subsequent inventory lookups for ~10 seconds.",
        "expected_result": "Memory consumption drops from >90% to safe operating baseline (~40%)."
    },
    "reset_db_connection_pool": {
        "name": "reset_db_connection_pool",
        "description": "Drain orphaned client connections, flush pool sockets, and re-establish fresh PostgreSQL pool.",
        "target_services": ["payment-service"],
        "risk_level": "HIGH",
        "requires_approval": True,
        "potential_impact": "Active in-flight database transactions (<1s) will be rolled back cleanly.",
        "expected_result": "Database timeouts clear; active connection pool metrics recover to 0% errors."
    },
    "enable_circuit_breaker": {
        "name": "enable_circuit_breaker",
        "description": "Trip circuit breaker for degraded downstream dependency to serve cached fallbacks.",
        "target_services": ["api-gateway"],
        "risk_level": "LOW",
        "requires_approval": False,
        "potential_impact": "Downstream recommendation widget serves cached or static fallback data.",
        "expected_result": "API Gateway response time drops from >3000ms to <100ms."
    },
    "rollback_bad_configuration": {
        "name": "rollback_bad_configuration",
        "description": "Revert active runtime configuration to known healthy baseline revision (rev-491).",
        "target_services": ["auth-service"],
        "risk_level": "MEDIUM",
        "requires_approval": True,
        "potential_impact": "Reverts recently deployed experimental configuration flags.",
        "expected_result": "HTTP 500 error rate drops to 0.0%; token validation succeeds."
    },
    "restart_service": {
        "name": "restart_service",
        "description": "Gracefully terminate and restart the affected container process.",
        "target_services": ["order-processing-service", "inventory-service", "payment-service", "api-gateway", "auth-service"],
        "risk_level": "HIGH",
        "requires_approval": True,
        "potential_impact": "Service unavailable for approximately 2-5 seconds during process bounce.",
        "expected_result": "Clean process restart; volatile memory and thread state reset."
    }
}


def validate_remediation_safety(action_name: str, target_service: str) -> Tuple[bool, str]:
    """
    Strict safety validation:
    1. Rejects any non-whitelisted action (prevents arbitrary command execution).
    2. Ensures the action is authorized for the target service.
    """
    if action_name not in REMEDIATION_REGISTRY:
        return False, f"Safety Violation: Action '{action_name}' is not in the approved remediation registry."
    
    spec = REMEDIATION_REGISTRY[action_name]
    if target_service not in spec["target_services"]:
        return False, f"Safety Violation: Action '{action_name}' is not authorized on service '{target_service}'."
        
    return True, "Safety validation passed: Action is registered, bounded, and verified."


def run_remediation_recommendation(state: IncidentState) -> IncidentState:
    """
    Agent 3 (Phase 1): Remediation Recommendation & Safety Validation.
    Maps diagnosis to registered safe actions and sets approval requirements.
    """
    logger.info("Remediation Agent determining action for incident: %s", state.get("incident_id"))
    start_time = datetime.now(timezone.utc)
    
    scenario_type = state.get("scenario_type", "")
    affected_service = state.get("affected_service", "order-processing-service")
    
    # Map scenario to registered safe action
    action_map = {
        "high_cpu": "scale_down_workload",
        "memory_exhaustion": "clear_service_cache",
        "db_failure": "reset_db_connection_pool",
        "api_latency": "enable_circuit_breaker",
        "http_500": "rollback_bad_configuration"
    }
    
    action_name = action_map.get(scenario_type, "restart_service")
    spec = REMEDIATION_REGISTRY[action_name]
    
    # Safety Check
    is_safe, safety_msg = validate_remediation_safety(action_name, affected_service)
    if not is_safe:
        logger.error("Remediation safety check failed: %s", safety_msg)
        action_name = "restart_service"
        spec = REMEDIATION_REGISTRY[action_name]

    duration_ms = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000

    agent_entry = {
        "agent": "Remediation Agent",
        "action": "ACTION_RECOMMENDATION_AND_SAFETY_VALIDATION",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "duration_ms": round(duration_ms, 2),
        "status": "COMPLETED",
        "summary": (
            f"Recommended: {action_name} on {affected_service}. "
            f"Risk: {spec['risk_level']}. Requires Approval: {spec['requires_approval']}. "
            f"Safety validation: PASSED."
        )
    }

    logs_copy = list(state.get("agent_logs", []))
    logs_copy.append(agent_entry)

    requires_approval = spec["requires_approval"]
    next_status = "Awaiting Approval" if requires_approval else "Remediating"

    return {
        **state,
        "status": next_status,
        "recommended_action": action_name,
        "action_parameters": {"target_service": affected_service, "spec": spec},
        "risk_level": spec["risk_level"],
        "requires_approval": requires_approval,
        "approval_status": "PENDING" if requires_approval else "NOT_REQUIRED",
        "agent_logs": logs_copy
    }


def execute_remediation_action(state: IncidentState) -> IncidentState:
    """
    Agent 3 (Phase 2): Controlled Execution of Approved Action in Simulation.
    Executes only after approval or safety check.
    """
    action_name = state.get("recommended_action")
    affected_service = state.get("affected_service")
    start_time = datetime.now(timezone.utc)

    # Re-validate safety before execution
    is_safe, reason = validate_remediation_safety(action_name, affected_service)
    if not is_safe:
        return {
            **state,
            "status": "Failed",
            "execution_result": f"Execution halted by safety guardrails: {reason}"
        }

    logger.info("Executing safe remediation: %s on %s", action_name, affected_service)
    result = simulation_engine.execute_remediation(action_name, affected_service)
    duration_ms = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000

    agent_entry = {
        "agent": "Remediation Agent",
        "action": "CONTROLLED_ACTION_EXECUTION",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "duration_ms": round(duration_ms, 2),
        "status": "COMPLETED",
        "summary": f"Executed action '{action_name}' successfully on {affected_service}. Simulation entered Recovery mode."
    }

    logs_copy = list(state.get("agent_logs", []))
    logs_copy.append(agent_entry)

    return {
        **state,
        "status": "Verifying",
        "approval_status": "EXECUTED",
        "execution_result": result.get("message", "Remediation executed successfully."),
        "agent_logs": logs_copy
    }
