import uuid
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend.database import get_db
from backend.models import (
    Incident,
    AgentExecution,
    RemediationAction,
    VerificationResult,
    TelemetryRecord
)
from backend.schemas import (
    IncidentResponse,
    DashboardSummary,
    AgentActivityItem,
    ApprovalRequest,
    IncidentReportResponse
)
from backend.simulation import simulation_engine
from backend.agents.workflow import (
    run_incident_investigation,
    run_incident_execution_and_verification,
    get_all_agent_specs,
)
from backend.agents.remediation import REMEDIATION_REGISTRY
from backend.observability import (
    get_grafana_observability_snapshot,
    run_live_agent_evaluation,
    get_latest_evaluation,
    estimate_costs,
)
from backend.config import settings

router = APIRouter(prefix="/api")

def utc_now():
    return datetime.now(timezone.utc)


# ==========================================
# SYSTEM & HEALTH
# ==========================================
@router.get("/health")
def health_check():
    return {
        "status": "healthy",
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "frameworks": ["CrewAI", "Google ADK"],
        "llm_enabled": settings.ENABLE_LLM,
        "llm_model": settings.GROQ_MODEL if settings.ENABLE_LLM else "Deterministic Rule Engine (Fallback)",
        "timestamp": utc_now().isoformat()
    }

@router.get("/system/status")
def system_status(db: Session = Depends(get_db)):
    active_incidents = db.query(Incident).filter(Incident.status.notin_(["Resolved", "Failed"])).count()
    services = simulation_engine.get_services_snapshot()
    unhealthy = [s for s in services if s["status"] != "HEALTHY"]
    
    overall = "HEALTHY"
    if unhealthy:
        overall = "DEGRADED" if len(unhealthy) == 1 else "CRITICAL"
        
    return {
        "overall_health": overall,
        "active_incidents_count": active_incidents,
        "simulation_mode": simulation_engine.mode,
        "active_scenario": simulation_engine.active_scenario,
        "services_count": len(services),
        "unhealthy_services_count": len(unhealthy),
        "llm_active": settings.ENABLE_LLM,
        "timestamp": utc_now().isoformat()
    }


# ==========================================
# DASHBOARD
# ==========================================
@router.get("/dashboard/summary", response_model=DashboardSummary)
def get_dashboard_summary(db: Session = Depends(get_db)):
    total = db.query(Incident).count()
    active = db.query(Incident).filter(Incident.status.notin_(["Resolved", "Failed"])).count()
    resolved = db.query(Incident).filter(Incident.status == "Resolved").count()
    failed = db.query(Incident).filter(Incident.status == "Failed").count()

    services = simulation_engine.get_services_snapshot()
    avg_lat = round(sum(s["response_time_ms"] for s in services) / max(len(services), 1), 1)
    avg_cpu = round(sum(s["cpu_usage"] for s in services) / max(len(services), 1), 1)
    avg_mem = round(sum(s["memory_usage"] for s in services) / max(len(services), 1), 1)
    avg_err = round(sum(s["error_rate"] for s in services) / max(len(services), 1), 2)

    health = "HEALTHY"
    if any(s["status"] == "UNHEALTHY" for s in services):
        health = "UNHEALTHY"
    elif any(s["status"] == "DEGRADED" for s in services):
        health = "DEGRADED"

    recent = db.query(Incident).order_by(desc(Incident.created_at)).limit(5).all()

    return DashboardSummary(
        total_incidents=total,
        active_incidents=active,
        resolved_incidents=resolved,
        failed_incidents=failed,
        avg_response_time_ms=avg_lat,
        avg_cpu_usage=avg_cpu,
        avg_memory_usage=avg_mem,
        avg_error_rate=avg_err,
        system_health=health,
        recent_incidents=[IncidentResponse.model_validate(inc) for inc in recent]
    )

@router.get("/dashboard/metrics")
def get_dashboard_metrics():
    """Returns rolling time-series telemetry metrics for Recharts."""
    timeline = simulation_engine.get_metrics_timeline()
    return {"metrics": timeline}


# ==========================================
# SERVICES MONITORING
# ==========================================
@router.get("/services")
def list_services():
    return {"services": simulation_engine.get_services_snapshot()}

@router.get("/services/{service_id}")
def get_service(service_id: str):
    svc = simulation_engine.get_service(service_id)
    if not svc:
        raise HTTPException(status_code=404, detail=f"Service '{service_id}' not found")
    return svc


# ==========================================
# SIMULATION CENTER
# ==========================================
@router.get("/simulation/scenarios")
def get_scenarios():
    return {
        "scenarios": simulation_engine.SCENARIOS,
        "active_scenario": simulation_engine.active_scenario,
        "mode": simulation_engine.mode
    }

@router.post("/simulation/trigger/{scenario}")
def trigger_scenario(scenario: str, db: Session = Depends(get_db)):
    try:
        sim_data = simulation_engine.trigger_scenario(scenario)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Create incident in database
    inc_id = f"INC-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
    meta = simulation_engine.SCENARIOS[scenario]

    db_incident = Incident(
        id=inc_id,
        title=f"{meta['name']} on {meta['service_id']}",
        scenario_type=scenario,
        affected_service=meta["service_id"],
        severity=meta["severity"],
        status="Detected",
        created_at=utc_now()
    )
    db.add(db_incident)
    db.commit()
    db.refresh(db_incident)

    # Immediately trigger autonomous Agent 1 & Agent 2 investigation workflow
    initial_state = {
        "incident_id": inc_id,
        "title": db_incident.title,
        "scenario_type": scenario,
        "affected_service": meta["service_id"],
        "severity": meta["severity"],
        "status": "Detected",
        "telemetry_snapshot": {},
        "detected_anomalies": [],
        "agent_logs": []
    }
    
    investigated_state = run_incident_investigation(initial_state)

    # Persist findings back to database
    db_incident.status = investigated_state.get("status", "Diagnosis Completed")
    db_incident.root_cause = investigated_state.get("root_cause")
    db_incident.confidence_score = investigated_state.get("confidence_score", 0.0)
    db_incident.evidence_summary = "\n".join(investigated_state.get("evidence", []))
    db_incident.is_llm_diagnosis = investigated_state.get("is_llm_diagnosis", False)
    db_incident.recommended_action = investigated_state.get("recommended_action")
    db_incident.action_parameters = investigated_state.get("action_parameters")
    db_incident.risk_level = investigated_state.get("risk_level", "MEDIUM")
    db_incident.approval_status = investigated_state.get("approval_status", "PENDING")
    db_incident.initial_metrics = investigated_state.get("telemetry_snapshot")

    # Persist agent execution logs
    for log_item in investigated_state.get("agent_logs", []):
        db_exec = AgentExecution(
            incident_id=inc_id,
            agent_name=log_item["agent"],
            task_description=log_item["action"],
            status=log_item.get("status", "COMPLETED"),
            duration_ms=log_item.get("duration_ms", 0.0),
            output_data={"summary": log_item.get("summary")},
            executed_at=utc_now()
        )
        db.add(db_exec)

    # Persist recommended remediation action record
    if db_incident.recommended_action:
        db_remed = RemediationAction(
            incident_id=inc_id,
            action_name=db_incident.recommended_action,
            description=investigated_state.get("action_parameters", {}).get("spec", {}).get("description", "Safe remediation"),
            target_service=db_incident.affected_service,
            risk_level=db_incident.risk_level,
            requires_approval=investigated_state.get("requires_approval", True),
            approval_status=db_incident.approval_status
        )
        db.add(db_remed)

    db.commit()
    db.refresh(db_incident)

    return {
        "status": "triggered",
        "scenario": scenario,
        "incident": IncidentResponse.model_validate(db_incident),
        "simulation": sim_data
    }

@router.post("/simulation/reset")
def reset_simulation():
    res = simulation_engine.reset()
    return res

@router.get("/simulation/logs")
def get_simulation_logs(limit: int = 50):
    return {"logs": simulation_engine.get_recent_logs(limit=limit)}


# ==========================================
# INCIDENTS MANAGEMENT
# ==========================================
@router.get("/incidents", response_model=List[IncidentResponse])
def list_incidents(db: Session = Depends(get_db)):
    incidents = db.query(Incident).order_by(desc(Incident.created_at)).all()
    return [IncidentResponse.model_validate(i) for i in incidents]

@router.get("/incidents/{incident_id}")
def get_incident_details(incident_id: str, db: Session = Depends(get_db)):
    inc = db.query(Incident).filter(Incident.id == incident_id).first()
    if not inc:
        raise HTTPException(status_code=404, detail=f"Incident {incident_id} not found")

    executions = db.query(AgentExecution).filter(AgentExecution.incident_id == incident_id).order_by(AgentExecution.executed_at).all()
    remediations = db.query(RemediationAction).filter(RemediationAction.incident_id == incident_id).all()
    verifications = db.query(VerificationResult).filter(VerificationResult.incident_id == incident_id).all()

    return {
        "incident": IncidentResponse.model_validate(inc),
        "agent_executions": [
            {
                "agent_name": e.agent_name,
                "task": e.task_description,
                "status": e.status,
                "duration_ms": e.duration_ms,
                "output": e.output_data,
                "executed_at": e.executed_at.isoformat() if e.executed_at else None
            }
            for e in executions
        ],
        "remediation_actions": [
            {
                "action_name": r.action_name,
                "description": r.description,
                "risk_level": r.risk_level,
                "requires_approval": r.requires_approval,
                "approval_status": r.approval_status,
                "approved_by": r.approved_by,
                "executed_at": r.executed_at.isoformat() if r.executed_at else None,
                "execution_log": r.execution_log
            }
            for r in remediations
        ],
        "verification_results": [
            {
                "is_resolved": v.is_resolved,
                "verification_status": v.verification_status,
                "pre_metrics": v.pre_metrics,
                "post_metrics": v.post_metrics,
                "metric_deltas": v.metric_deltas,
                "notes": v.notes,
                "verified_at": v.verified_at.isoformat() if v.verified_at else None
            }
            for v in verifications
        ]
    }

@router.post("/incidents/investigate/{incident_id}")
def trigger_investigation(incident_id: str, db: Session = Depends(get_db)):
    inc = db.query(Incident).filter(Incident.id == incident_id).first()
    if not inc:
        raise HTTPException(status_code=404, detail="Incident not found")

    state = {
        "incident_id": inc.id,
        "title": inc.title,
        "scenario_type": inc.scenario_type,
        "affected_service": inc.affected_service,
        "severity": inc.severity,
        "status": inc.status,
        "agent_logs": []
    }
    updated = run_incident_investigation(state)

    inc.status = updated.get("status", "Diagnosis Completed")
    inc.root_cause = updated.get("root_cause")
    inc.confidence_score = updated.get("confidence_score", 0.0)
    inc.evidence_summary = "\n".join(updated.get("evidence", []))
    inc.is_llm_diagnosis = updated.get("is_llm_diagnosis", False)
    inc.recommended_action = updated.get("recommended_action")
    inc.action_parameters = updated.get("action_parameters")
    inc.risk_level = updated.get("risk_level", "MEDIUM")
    inc.approval_status = updated.get("approval_status", "PENDING")
    inc.initial_metrics = updated.get("telemetry_snapshot")

    db.commit()
    db.refresh(inc)
    return IncidentResponse.model_validate(inc)


# ==========================================
# AGENTS STATUS & ACTIVITY
# ==========================================
@router.get("/agents")
def list_agents():
    return {
        "frameworks": ["CrewAI", "Google ADK"],
        "agents": get_all_agent_specs()
    }

@router.get("/agents/activity")
def get_agents_activity(db: Session = Depends(get_db)):
    executions = db.query(AgentExecution).order_by(desc(AgentExecution.executed_at)).limit(30).all()
    timeline = [
        {
            "id": e.id,
            "incident_id": e.incident_id,
            "agent_name": e.agent_name,
            "task": e.task_description,
            "status": e.status,
            "duration_ms": e.duration_ms,
            "summary": e.output_data.get("summary") if e.output_data else "",
            "timestamp": e.executed_at.isoformat() if e.executed_at else None
        }
        for e in executions
    ]
    return {"timeline": timeline}


# ==========================================
# REMEDIATION & HUMAN APPROVAL
# ==========================================
@router.get("/remediation/{incident_id}")
def get_remediation_info(incident_id: str, db: Session = Depends(get_db)):
    inc = db.query(Incident).filter(Incident.id == incident_id).first()
    if not inc:
        raise HTTPException(status_code=404, detail="Incident not found")
    
    spec = REMEDIATION_REGISTRY.get(inc.recommended_action, {})
    return {
        "incident_id": inc.id,
        "affected_service": inc.affected_service,
        "recommended_action": inc.recommended_action,
        "risk_level": inc.risk_level,
        "approval_status": inc.approval_status,
        "requires_approval": spec.get("requires_approval", True),
        "reason": f"RCA confirmed {inc.root_cause}. Recovery required to restore SLA.",
        "expected_result": spec.get("expected_result", "Restores normal performance"),
        "potential_impact": spec.get("potential_impact", "Minimal transient latency"),
        "spec": spec
    }

@router.post("/remediation/{incident_id}/approve")
def approve_remediation(incident_id: str, approval: ApprovalRequest, db: Session = Depends(get_db)):
    inc = db.query(Incident).filter(Incident.id == incident_id).first()
    if not inc:
        raise HTTPException(status_code=404, detail="Incident not found")
    
    if inc.approval_status == "EXECUTED":
        raise HTTPException(status_code=400, detail="Remediation has already been executed.")

    inc.approval_status = "APPROVED" if approval.approved else "REJECTED"
    inc.status = "Remediating" if approval.approved else "Diagnosis Completed"

    # Update remediation action record
    remed = db.query(RemediationAction).filter(RemediationAction.incident_id == incident_id).first()
    if remed:
        remed.approval_status = inc.approval_status
        remed.approved_by = approval.approver_name

    db.commit()

    # If approved, automatically trigger execution and verification workflow!
    if approval.approved:
        return execute_remediation(incident_id, db)

    return {"message": f"Remediation decision recorded: {inc.approval_status}", "incident": IncidentResponse.model_validate(inc)}

@router.post("/remediation/{incident_id}/reject")
def reject_remediation(incident_id: str, db: Session = Depends(get_db)):
    req = ApprovalRequest(approved=False, approver_name="Operator (Rejected)")
    return approve_remediation(incident_id, req, db)

@router.post("/remediation/{incident_id}/execute")
def execute_remediation(incident_id: str, db: Session = Depends(get_db)):
    inc = db.query(Incident).filter(Incident.id == incident_id).first()
    if not inc:
        raise HTTPException(status_code=404, detail="Incident not found")

    state = {
        "incident_id": inc.id,
        "title": inc.title,
        "scenario_type": inc.scenario_type,
        "affected_service": inc.affected_service,
        "severity": inc.severity,
        "status": inc.status,
        "telemetry_snapshot": inc.initial_metrics or {},
        "recommended_action": inc.recommended_action,
        "requires_approval": False,
        "agent_logs": []
    }

    # Execute remediation and run verification agent
    verified_state = run_incident_execution_and_verification(state)

    inc.status = verified_state.get("status", "Resolved")
    inc.approval_status = "EXECUTED"
    inc.execution_result = verified_state.get("execution_result")
    inc.verification_status = verified_state.get("verification_status")
    inc.final_metrics = verified_state.get("post_telemetry")
    inc.metric_deltas = verified_state.get("metric_deltas")
    
    if verified_state.get("is_resolved"):
        now_dt = utc_now()
        inc.resolved_at = now_dt
        if inc.created_at:
            duration = (now_dt - inc.created_at.replace(tzinfo=timezone.utc)).total_seconds()
            inc.recovery_duration_seconds = round(max(duration, 1.0), 1)

    # Persist execution agent logs
    for log_item in verified_state.get("agent_logs", []):
        db_exec = AgentExecution(
            incident_id=inc.id,
            agent_name=log_item["agent"],
            task_description=log_item["action"],
            status=log_item.get("status", "COMPLETED"),
            duration_ms=log_item.get("duration_ms", 0.0),
            output_data={"summary": log_item.get("summary")},
            executed_at=utc_now()
        )
        db.add(db_exec)

    # Persist verification result record
    v_res = VerificationResult(
        incident_id=inc.id,
        is_resolved=verified_state.get("is_resolved", False),
        verification_status=verified_state.get("verification_status", "RESOLVED"),
        pre_metrics=inc.initial_metrics,
        post_metrics=inc.final_metrics,
        metric_deltas=inc.metric_deltas,
        health_check_passed=verified_state.get("is_resolved", False),
        notes=verified_state.get("verification_notes", "Recovery verified."),
        verified_at=utc_now()
    )
    db.add(v_res)

    db.commit()
    db.refresh(inc)

    return {
        "status": "success",
        "incident": IncidentResponse.model_validate(inc),
        "verification": {
            "status": inc.verification_status,
            "metric_deltas": inc.metric_deltas,
            "notes": verified_state.get("verification_notes")
        }
    }


# ==========================================
# VERIFICATION
# ==========================================
@router.get("/verification/{incident_id}")
def get_verification_details(incident_id: str, db: Session = Depends(get_db)):
    v_record = db.query(VerificationResult).filter(VerificationResult.incident_id == incident_id).order_by(desc(VerificationResult.verified_at)).first()
    if not v_record:
        raise HTTPException(status_code=404, detail=f"No verification record found for {incident_id}")
    
    return {
        "incident_id": incident_id,
        "is_resolved": v_record.is_resolved,
        "status": v_record.verification_status,
        "pre_metrics": v_record.pre_metrics,
        "post_metrics": v_record.post_metrics,
        "metric_deltas": v_record.metric_deltas,
        "notes": v_record.notes,
        "verified_at": v_record.verified_at.isoformat() if v_record.verified_at else None
    }

@router.post("/verification/{incident_id}")
def trigger_verification(incident_id: str, db: Session = Depends(get_db)):
    """Explicitly re-run verification on an existing incident."""
    inc = db.query(Incident).filter(Incident.id == incident_id).first()
    if not inc:
        raise HTTPException(status_code=404, detail="Incident not found")
    
    state = {
        "incident_id": inc.id,
        "affected_service": inc.affected_service,
        "telemetry_snapshot": inc.initial_metrics or {},
        "agent_logs": []
    }
    
    from backend.agents.verification import run_verification_agent
    res = run_verification_agent(state)
    
    inc.verification_status = res.get("verification_status", "RESOLVED")
    if res.get("is_resolved"):
        inc.status = "Resolved"
        inc.resolved_at = utc_now()
    inc.final_metrics = res.get("post_telemetry")
    inc.metric_deltas = res.get("metric_deltas")
    
    db.commit()
    return {"message": "Verification completed", "result": res}


# ==========================================
# REPORTS
# ==========================================
@router.get("/reports", response_model=List[IncidentResponse])
def list_reports(db: Session = Depends(get_db)):
    reports = db.query(Incident).filter(Incident.status.in_(["Resolved", "Partially Resolved", "Failed"])).order_by(desc(Incident.created_at)).all()
    return [IncidentResponse.model_validate(r) for r in reports]

@router.get("/reports/{incident_id}", response_model=IncidentReportResponse)
def get_incident_report(incident_id: str, db: Session = Depends(get_db)):
    inc = db.query(Incident).filter(Incident.id == incident_id).first()
    if not inc:
        raise HTTPException(status_code=404, detail="Incident report not found")

    remed = db.query(RemediationAction).filter(RemediationAction.incident_id == incident_id).first()
    verif = db.query(VerificationResult).filter(VerificationResult.incident_id == incident_id).order_by(desc(VerificationResult.verified_at)).first()

    pre = inc.initial_metrics or {}
    post = inc.final_metrics or {}
    deltas = inc.metric_deltas or {}

    evidence_list = [line.strip() for line in (inc.evidence_summary or "").split("\n") if line.strip()]

    summary_md = f"""# Incident Report: {inc.id}
**Title:** {inc.title}
**Service:** {inc.affected_service}
**Severity:** {inc.severity}
**Status:** {inc.status}
**Duration:** {inc.recovery_duration_seconds or 0.0}s

## 1. Root Cause Analysis
- **Root Cause:** {inc.root_cause or 'Under investigation'}
- **Confidence Score:** {int(inc.confidence_score * 100)}%
- **Diagnosis Provider:** {'Groq LLM' if inc.is_llm_diagnosis else 'Deterministic Rule Engine'}

### Supporting Evidence:
{chr(10).join(f"- {e}" for e in evidence_list)}

## 2. Remediation Executed
- **Action:** `{inc.recommended_action}`
- **Risk Level:** {inc.risk_level}
- **Approval Status:** {inc.approval_status}
- **Execution Log:** {inc.execution_result or 'Completed'}

## 3. Verification & Metric Deltas
| Metric | Before | After | Delta |
|---|---|---|---|
| CPU Usage | {deltas.get('cpu_usage', {}).get('before', pre.get('cpu_usage', 'N/A'))}% | {deltas.get('cpu_usage', {}).get('after', post.get('cpu_usage', 'N/A'))}% | {deltas.get('cpu_usage', {}).get('delta', 'N/A')}% |
| Memory Usage | {deltas.get('memory_usage', {}).get('before', pre.get('memory_usage', 'N/A'))}% | {deltas.get('memory_usage', {}).get('after', post.get('memory_usage', 'N/A'))}% | {deltas.get('memory_usage', {}).get('delta', 'N/A')}% |
| Latency | {deltas.get('response_time_ms', {}).get('before', pre.get('response_time_ms', 'N/A'))}ms | {deltas.get('response_time_ms', {}).get('after', post.get('response_time_ms', 'N/A'))}ms | {deltas.get('response_time_ms', {}).get('delta', 'N/A')}ms |
| Error Rate | {deltas.get('error_rate', {}).get('before', pre.get('error_rate', 'N/A'))}% | {deltas.get('error_rate', {}).get('after', post.get('error_rate', 'N/A'))}% | {deltas.get('error_rate', {}).get('delta', 'N/A')}% |

**Verification Result:** {inc.verification_status}
**Notes:** {verif.notes if verif else 'Automated recovery verified successfully.'}
"""

    return IncidentReportResponse(
        incident_id=inc.id,
        title=inc.title,
        created_at=inc.created_at,
        resolved_at=inc.resolved_at,
        duration_seconds=inc.recovery_duration_seconds,
        affected_service=inc.affected_service,
        severity=inc.severity,
        final_status=inc.status,
        root_cause=inc.root_cause or "Not determined",
        confidence_score=inc.confidence_score,
        is_llm_diagnosis=inc.is_llm_diagnosis,
        evidence=evidence_list,
        remediation_action=inc.recommended_action or "None",
        approval_status=inc.approval_status,
        approved_by=remed.approved_by if remed else "Admin",
        pre_remediation_metrics=pre,
        post_remediation_metrics=post,
        metric_improvements=deltas,
        verification_result=inc.verification_status,
        summary_markdown=summary_md
    )

@router.get("/reports/{incident_id}/download")
def download_incident_report(incident_id: str, db: Session = Depends(get_db)):
    report_data = get_incident_report(incident_id, db)
    return Response(
        content=report_data.summary_markdown,
        media_type="text/markdown",
        headers={"Content-Disposition": f"attachment; filename=TraceMind-Report-{incident_id}.md"}
    )


# ==========================================
# GRAFANA OBSERVABILITY, LIVE EVAL & COST
# ==========================================
@router.get("/observability/metrics")
def observability_metrics(db: Session = Depends(get_db)):
    return get_grafana_observability_snapshot(db)


@router.post("/evaluation/run")
def run_evaluation_suite():
    return run_live_agent_evaluation()


@router.get("/evaluation/latest")
def get_evaluation_suite():
    return get_latest_evaluation()


@router.get("/cost/estimate")
def get_cost_estimation(monthly_incidents: int = 1000, db: Session = Depends(get_db)):
    return estimate_costs(db, projected_monthly_incidents=monthly_incidents)
