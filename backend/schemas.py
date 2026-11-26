from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class ServiceMetric(BaseModel):
    service_id: str
    name: str
    status: str  # HEALTHY, DEGRADED, UNHEALTHY
    cpu_usage: float
    memory_usage: float
    response_time_ms: float
    request_count: int
    error_count: int
    error_rate: float
    last_updated: datetime


class AnomalyReport(BaseModel):
    is_anomaly: bool
    affected_service: Optional[str] = None
    severity: str = "LOW"
    detected_anomalies: List[str] = []
    telemetry_snapshot: Dict[str, Any] = {}
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class RCAResult(BaseModel):
    probable_root_cause: str
    confidence_score: float
    affected_component: str
    supporting_evidence: List[str] = []
    related_metrics: Dict[str, Any] = {}
    relevant_logs: List[str] = []
    alternative_causes: List[str] = []
    is_llm_diagnosis: bool = False
    explanation_summary: str = ""


class RemediationRecommendation(BaseModel):
    action_name: str
    target_service: str
    description: str
    reason: str
    expected_result: str
    risk_level: str  # LOW, MEDIUM, HIGH
    potential_impact: str
    requires_approval: bool
    parameters: Dict[str, Any] = {}


class VerificationSummary(BaseModel):
    is_resolved: bool
    status: str  # RESOLVED, PARTIALLY_RESOLVED, FAILED
    pre_metrics: Dict[str, Any] = {}
    post_metrics: Dict[str, Any] = {}
    metric_deltas: Dict[str, Any] = {}
    health_check_passed: bool
    notes: str


class IncidentCreate(BaseModel):
    scenario_type: str
    service_name: Optional[str] = None


class IncidentResponse(BaseModel):
    id: str
    title: str
    scenario_type: str
    affected_service: str
    severity: str
    status: str
    root_cause: Optional[str] = None
    confidence_score: float = 0.0
    evidence_summary: Optional[str] = None
    is_llm_diagnosis: bool = False
    recommended_action: Optional[str] = None
    action_parameters: Optional[Dict[str, Any]] = None
    risk_level: str = "MEDIUM"
    approval_status: str = "PENDING"
    execution_result: Optional[str] = None
    verification_status: str = "PENDING"
    initial_metrics: Optional[Dict[str, Any]] = None
    final_metrics: Optional[Dict[str, Any]] = None
    metric_deltas: Optional[Dict[str, Any]] = None
    created_at: datetime
    resolved_at: Optional[datetime] = None
    recovery_duration_seconds: Optional[float] = None

    model_config = ConfigDict(from_attributes=True)


class ApprovalRequest(BaseModel):
    approved: bool
    approver_name: str = "System Admin"
    notes: Optional[str] = None


class ScenarioTriggerRequest(BaseModel):
    scenario: str  # high_cpu, memory_exhaustion, db_failure, api_latency, http_500


class DashboardSummary(BaseModel):
    total_incidents: int
    active_incidents: int
    resolved_incidents: int
    failed_incidents: int
    avg_response_time_ms: float
    avg_cpu_usage: float
    avg_memory_usage: float
    avg_error_rate: float
    system_health: str
    recent_incidents: List[IncidentResponse]


class AgentActivityItem(BaseModel):
    agent_name: str
    responsibility: str
    current_task: str
    status: str  # IDLE, RUNNING, COMPLETED, FAILED
    last_execution_time: Optional[datetime] = None
    last_output: Optional[Dict[str, Any]] = None


class IncidentReportResponse(BaseModel):
    incident_id: str
    title: str
    created_at: datetime
    resolved_at: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    affected_service: str
    severity: str
    final_status: str
    root_cause: str
    confidence_score: float
    is_llm_diagnosis: bool
    evidence: List[str]
    remediation_action: str
    approval_status: str
    approved_by: Optional[str] = None
    pre_remediation_metrics: Dict[str, Any]
    post_remediation_metrics: Dict[str, Any]
    metric_improvements: Dict[str, Any]
    verification_result: str
    summary_markdown: str
