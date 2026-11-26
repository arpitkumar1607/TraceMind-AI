from typing import TypedDict, List, Dict, Any, Optional

class IncidentState(TypedDict, total=False):
    incident_id: str
    title: str
    scenario_type: str
    affected_service: str
    severity: str
    status: str
    
    # Telemetry & Monitoring
    telemetry_snapshot: Dict[str, Any]
    detected_anomalies: List[str]
    recent_logs: List[Dict[str, Any]]
    
    # RCA Agent
    root_cause: str
    confidence_score: float
    evidence: List[str]
    is_llm_diagnosis: bool
    alternative_causes: List[str]
    explanation_summary: str
    
    # Remediation Agent
    recommended_action: str
    action_parameters: Dict[str, Any]
    risk_level: str
    requires_approval: bool
    approval_status: str
    execution_result: str
    
    # Verification Agent
    post_telemetry: Dict[str, Any]
    metric_deltas: Dict[str, Any]
    verification_status: str
    is_resolved: bool
    verification_notes: str
    
    # Chronological agent execution log
    agent_logs: List[Dict[str, Any]]
    created_at: str
    resolved_at: Optional[str]
