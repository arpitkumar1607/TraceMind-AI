from datetime import datetime, timezone
from sqlalchemy import (
    Column,
    String,
    Float,
    Integer,
    Boolean,
    DateTime,
    Text,
    JSON,
    ForeignKey
)
from sqlalchemy.orm import relationship
from backend.database import Base


def utc_now():
    return datetime.now(timezone.utc)


class Incident(Base):
    __tablename__ = "incidents"

    id = Column(String(64), primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    scenario_type = Column(String(64), nullable=False)
    affected_service = Column(String(128), nullable=False)
    severity = Column(String(32), default="MEDIUM")
    status = Column(String(64), default="Detected", index=True)
    
    # RCA fields
    root_cause = Column(Text, nullable=True)
    confidence_score = Column(Float, default=0.0)
    evidence_summary = Column(Text, nullable=True)
    is_llm_diagnosis = Column(Boolean, default=False)
    
    # Remediation fields
    recommended_action = Column(String(128), nullable=True)
    action_parameters = Column(JSON, nullable=True)
    risk_level = Column(String(32), default="MEDIUM")
    approval_status = Column(String(32), default="PENDING")
    execution_result = Column(Text, nullable=True)
    
    # Verification & Metrics
    verification_status = Column(String(64), default="PENDING")
    initial_metrics = Column(JSON, nullable=True)
    final_metrics = Column(JSON, nullable=True)
    metric_deltas = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=utc_now)
    resolved_at = Column(DateTime, nullable=True)
    recovery_duration_seconds = Column(Float, nullable=True)

    # Relationships
    agent_executions = relationship("AgentExecution", back_populates="incident", cascade="all, delete-orphan")
    remediation_actions = relationship("RemediationAction", back_populates="incident", cascade="all, delete-orphan")
    verification_results = relationship("VerificationResult", back_populates="incident", cascade="all, delete-orphan")


class TelemetryRecord(Base):
    __tablename__ = "telemetry_records"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    service_name = Column(String(128), nullable=False, index=True)
    cpu_usage = Column(Float, nullable=False)
    memory_usage = Column(Float, nullable=False)
    response_time_ms = Column(Float, nullable=False)
    request_count = Column(Integer, default=0)
    error_count = Column(Integer, default=0)
    error_rate = Column(Float, default=0.0)
    status = Column(String(32), default="HEALTHY")
    scenario = Column(String(64), default="normal")
    log_level = Column(String(16), default="INFO")
    log_message = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=utc_now, index=True)


class AgentExecution(Base):
    __tablename__ = "agent_executions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    incident_id = Column(String(64), ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False, index=True)
    agent_name = Column(String(64), nullable=False)
    task_description = Column(String(255), nullable=False)
    status = Column(String(32), default="COMPLETED")
    input_data = Column(JSON, nullable=True)
    output_data = Column(JSON, nullable=True)
    executed_at = Column(DateTime, default=utc_now)
    duration_ms = Column(Float, default=0.0)

    incident = relationship("Incident", back_populates="agent_executions")


class RemediationAction(Base):
    __tablename__ = "remediation_actions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    incident_id = Column(String(64), ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False, index=True)
    action_name = Column(String(128), nullable=False)
    description = Column(Text, nullable=False)
    target_service = Column(String(128), nullable=False)
    risk_level = Column(String(32), default="MEDIUM")
    requires_approval = Column(Boolean, default=True)
    approval_status = Column(String(32), default="PENDING")
    approved_by = Column(String(64), nullable=True)
    executed_at = Column(DateTime, nullable=True)
    result_status = Column(String(32), default="PENDING")
    execution_log = Column(Text, nullable=True)

    incident = relationship("Incident", back_populates="remediation_actions")


class VerificationResult(Base):
    __tablename__ = "verification_results"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    incident_id = Column(String(64), ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False, index=True)
    is_resolved = Column(Boolean, default=False)
    verification_status = Column(String(32), default="PENDING")
    pre_metrics = Column(JSON, nullable=True)
    post_metrics = Column(JSON, nullable=True)
    metric_deltas = Column(JSON, nullable=True)
    health_check_passed = Column(Boolean, default=False)
    notes = Column(Text, nullable=True)
    verified_at = Column(DateTime, default=utc_now)

    incident = relationship("Incident", back_populates="verification_results")
