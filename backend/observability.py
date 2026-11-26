import time
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.models import Incident, AgentExecution
from backend.simulation import simulation_engine
from backend.agents.workflow import (
    run_incident_investigation,
    run_incident_execution_and_verification,
)
from backend.agents.remediation import validate_remediation_safety
from backend.config import settings

# Latest cached live evaluation run
_LATEST_EVALUATION: Optional[Dict[str, Any]] = None

# Approximate token profile per incident across 4 agents (ADK Monitoring, CrewAI RCA, CrewAI Remediation, ADK Verification)
TOKENS_PER_INCIDENT = {
    "monitoring_adk": {"input": 320, "output": 140},
    "rca_crewai": {"input": 950, "output": 380},
    "remediation_crewai": {"input": 420, "output": 190},
    "verification_adk": {"input": 290, "output": 130},
}

# Pricing per 1M tokens (USD)
MODEL_PRICING_PER_1M = {
    "deterministic": {"label": "Deterministic Rule + Tool Engine (Active Offline)", "input": 0.0, "output": 0.0},
    "gemini_2_5_flash": {"label": "Google ADK (Gemini 2.5 Flash)", "input": 0.15, "output": 0.60},
    "groq_llama_70b": {"label": "CrewAI + Groq (Llama 3.3 70B)", "input": 0.59, "output": 0.79},
}


def _calc_cost_usd(input_tokens: int, output_tokens: int, in_price: float, out_price: float) -> float:
    return round((input_tokens / 1_000_000) * in_price + (output_tokens / 1_000_000) * out_price, 6)


def estimate_costs(db: Session, projected_monthly_incidents: int = 1000) -> Dict[str, Any]:
    """Compute actual & projected cost estimation for CrewAI + Google ADK pipelines."""
    total_incidents = db.query(Incident).count()
    llm_incidents = db.query(Incident).filter(Incident.is_llm_diagnosis == True).count()  # noqa: E712

    total_in_per_inc = sum(v["input"] for v in TOKENS_PER_INCIDENT.values())
    total_out_per_inc = sum(v["output"] for v in TOKENS_PER_INCIDENT.values())

    # Hybrid ADK (Gemini Flash) + CrewAI (Groq Llama 70B)
    adk_in = TOKENS_PER_INCIDENT["monitoring_adk"]["input"] + TOKENS_PER_INCIDENT["verification_adk"]["input"]
    adk_out = TOKENS_PER_INCIDENT["monitoring_adk"]["output"] + TOKENS_PER_INCIDENT["verification_adk"]["output"]
    crew_in = TOKENS_PER_INCIDENT["rca_crewai"]["input"] + TOKENS_PER_INCIDENT["remediation_crewai"]["input"]
    crew_out = TOKENS_PER_INCIDENT["rca_crewai"]["output"] + TOKENS_PER_INCIDENT["remediation_crewai"]["output"]

    adk_cost_per_inc = _calc_cost_usd(
        adk_in, adk_out,
        MODEL_PRICING_PER_1M["gemini_2_5_flash"]["input"],
        MODEL_PRICING_PER_1M["gemini_2_5_flash"]["output"],
    )
    crew_cost_per_inc = _calc_cost_usd(
        crew_in, crew_out,
        MODEL_PRICING_PER_1M["groq_llama_70b"]["input"],
        MODEL_PRICING_PER_1M["groq_llama_70b"]["output"],
    )
    hybrid_cost_per_inc = round(adk_cost_per_inc + crew_cost_per_inc, 6)

    actual_spend_usd = round(llm_incidents * hybrid_cost_per_inc, 6) if settings.ENABLE_LLM else 0.0

    tiers = []
    for volume in [100, 1000, 10000]:
        tiers.append({
            "monthly_incidents": volume,
            "deterministic_usd": 0.0,
            "adk_only_usd": round(volume * _calc_cost_usd(total_in_per_inc, total_out_per_inc, 0.15, 0.60), 4),
            "hybrid_adk_crewai_usd": round(volume * hybrid_cost_per_inc, 4),
        })

    return {
        "active_mode": "LLM-Enabled Hybrid (ADK + CrewAI)" if settings.ENABLE_LLM else "Deterministic Offline ($0.00)",
        "total_incidents_recorded": total_incidents,
        "llm_incidents_recorded": llm_incidents,
        "actual_spend_usd": actual_spend_usd,
        "tokens_per_incident": {
            "input_tokens": total_in_per_inc,
            "output_tokens": total_out_per_inc,
            "total_tokens": total_in_per_inc + total_out_per_inc,
            "breakdown": TOKENS_PER_INCIDENT,
        },
        "per_incident_cost_usd": {
            "deterministic": 0.0,
            "adk_portion": adk_cost_per_inc,
            "crewai_portion": crew_cost_per_inc,
            "hybrid_total": hybrid_cost_per_inc,
        },
        "projected_monthly": {
            "selected_volume": projected_monthly_incidents,
            "estimated_usd": 0.0 if not settings.ENABLE_LLM else round(projected_monthly_incidents * hybrid_cost_per_inc, 4),
            "hybrid_if_llm_enabled_usd": round(projected_monthly_incidents * hybrid_cost_per_inc, 4),
        },
        "volume_tiers": tiers,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def run_live_agent_evaluation() -> Dict[str, Any]:
    """
    Execute a live end-to-end evaluation benchmark across all 5 failure scenarios
    using the Google ADK + CrewAI pipeline. Leaves simulation clean afterwards.
    """
    global _LATEST_EVALUATION
    results: List[Dict[str, Any]] = []
    total_start = time.perf_counter()

    try:
        for scenario_key, meta in simulation_engine.SCENARIOS.items():
            simulation_engine.reset()
            trig = simulation_engine.trigger_scenario(scenario_key)
            target_svc = trig["affected_service"]

            t0 = time.perf_counter()
            state = {
                "incident_id": f"EVAL-{scenario_key.upper()}",
                "title": meta.get("name", scenario_key),
                "scenario_type": scenario_key,
                "affected_service": target_svc,
                "agent_logs": [],
            }

            investigated = run_incident_investigation(state)
            if investigated.get("requires_approval", True):
                investigated["approval_status"] = "APPROVED"
            verified = run_incident_execution_and_verification(investigated)
            total_ms = round((time.perf_counter() - t0) * 1000, 2)

            # Evaluate each agent stage
            adk_mon_pass = (
                len(verified.get("detected_anomalies", [])) > 0
                and verified.get("affected_service") == target_svc
            )
            crew_rca_pass = (
                float(verified.get("confidence_score", 0.0)) >= 0.85
                and len(verified.get("evidence", [])) >= 1
            )
            is_safe, _ = validate_remediation_safety(
                verified.get("recommended_action", ""), target_svc
            )
            crew_rem_pass = is_safe and bool(verified.get("recommended_action"))
            adk_ver_pass = bool(verified.get("is_resolved")) and verified.get("verification_status") == "Resolved"

            passed_checks = sum([adk_mon_pass, crew_rca_pass, crew_rem_pass, adk_ver_pass])
            scenario_score = round((passed_checks / 4.0) * 100, 1)

            agent_latencies = {
                entry.get("agent", "unknown"): entry.get("duration_ms", 0.0)
                for entry in verified.get("agent_logs", [])
            }

            results.append({
                "scenario": scenario_key,
                "title": meta.get("name", scenario_key),
                "service": target_svc,
                "frameworks": ["Google ADK", "CrewAI"],
                "checks": {
                    "adk_monitoring_passed": adk_mon_pass,
                    "crewai_rca_passed": crew_rca_pass,
                    "crewai_remediation_passed": crew_rem_pass,
                    "adk_verification_passed": adk_ver_pass,
                },
                "confidence_score": verified.get("confidence_score", 0.0),
                "recommended_action": verified.get("recommended_action", ""),
                "score_percent": scenario_score,
                "passed": passed_checks == 4,
                "total_latency_ms": total_ms,
                "agent_latencies_ms": agent_latencies,
            })
    finally:
        simulation_engine.reset()

    total_duration_ms = round((time.perf_counter() - total_start) * 1000, 2)
    passed_count = sum(1 for r in results if r["passed"])
    pass_rate = round((passed_count / max(len(results), 1)) * 100, 1)
    avg_latency = round(sum(r["total_latency_ms"] for r in results) / max(len(results), 1), 2)
    avg_confidence = round(sum(r["confidence_score"] for r in results) / max(len(results), 1) * 100, 1)

    _LATEST_EVALUATION = {
        "evaluated_at": datetime.now(timezone.utc).isoformat(),
        "frameworks": ["CrewAI", "Google ADK"],
        "scenarios_tested": len(results),
        "scenarios_passed": passed_count,
        "overall_pass_rate_percent": pass_rate,
        "avg_pipeline_latency_ms": avg_latency,
        "avg_rca_confidence_percent": avg_confidence,
        "total_benchmark_ms": total_duration_ms,
        "results": results,
    }
    return _LATEST_EVALUATION


def get_latest_evaluation() -> Dict[str, Any]:
    if _LATEST_EVALUATION is None:
        return run_live_agent_evaluation()
    return _LATEST_EVALUATION


def get_grafana_observability_snapshot(db: Session) -> Dict[str, Any]:
    """Return Grafana-style panel metrics for services, agents, evaluation, and cost."""
    services = simulation_engine.get_services_snapshot()
    eval_data = get_latest_evaluation()
    cost_data = estimate_costs(db)

    avg_lat = db.query(func.avg(AgentExecution.duration_ms)).scalar() or 0.0
    total_execs = db.query(AgentExecution).count()

    # Per-agent latency breakdown from DB
    agent_rows = (
        db.query(
            AgentExecution.agent_name,
            func.count(AgentExecution.id).label("runs"),
            func.avg(AgentExecution.duration_ms).label("avg_ms"),
        )
        .group_by(AgentExecution.agent_name)
        .all()
    )
    agent_metrics = [
        {
            "agent": row.agent_name,
            "runs": row.runs,
            "avg_latency_ms": round(float(row.avg_ms or 0.0), 2),
        }
        for row in agent_rows
    ]

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "frameworks": ["CrewAI", "Google ADK"],
        "prometheus_endpoint": "/metrics",
        "kpis": {
            "eval_pass_rate_percent": eval_data["overall_pass_rate_percent"],
            "avg_agent_latency_ms": round(float(avg_lat), 2) if total_execs else eval_data["avg_pipeline_latency_ms"],
            "total_agent_executions": total_execs,
            "estimated_actual_cost_usd": cost_data["actual_spend_usd"],
            "projected_1k_monthly_usd": cost_data["projected_monthly"]["hybrid_if_llm_enabled_usd"],
        },
        "service_series": [
            {
                "service": s["service_id"],
                "cpu_percent": s["cpu_usage"],
                "memory_percent": s["memory_usage"],
                "latency_ms": s["response_time_ms"],
                "error_rate_percent": s["error_rate"],
                "status": s["status"],
            }
            for s in services
        ],
        "agent_metrics": agent_metrics,
        "evaluation": eval_data,
        "cost": cost_data,
    }


def get_prometheus_metrics(db: Session) -> str:
    """Render Prometheus text-format metrics for Grafana scraping at GET /metrics."""
    snap = get_grafana_observability_snapshot(db)
    total_incidents = db.query(Incident).count()
    lines = [
        "# HELP tracemind_agent_eval_pass_rate Overall live agent evaluation pass rate percentage",
        "# TYPE tracemind_agent_eval_pass_rate gauge",
        f"tracemind_agent_eval_pass_rate {snap['kpis']['eval_pass_rate_percent']}",
        "# HELP tracemind_incidents_total Total incidents recorded",
        "# TYPE tracemind_incidents_total counter",
        f"tracemind_incidents_total {total_incidents}",
        "# HELP tracemind_estimated_cost_usd Estimated actual LLM spend in USD",
        "# TYPE tracemind_estimated_cost_usd gauge",
        f"tracemind_estimated_cost_usd {snap['kpis']['estimated_actual_cost_usd']}",
        "# HELP tracemind_agent_latency_ms_avg Average agent execution latency in ms",
        "# TYPE tracemind_agent_latency_ms_avg gauge",
        f"tracemind_agent_latency_ms_avg {snap['kpis']['avg_agent_latency_ms']}",
        "# HELP tracemind_service_cpu_percent Current CPU utilization per microservice",
        "# TYPE tracemind_service_cpu_percent gauge",
    ]
    for svc in snap["service_series"]:
        lines.append(f'tracemind_service_cpu_percent{{service="{svc["service"]}"}} {svc["cpu_percent"]}')
    lines.append("# HELP tracemind_service_latency_ms Current response latency per microservice")
    lines.append("# TYPE tracemind_service_latency_ms gauge")
    for svc in snap["service_series"]:
        lines.append(f'tracemind_service_latency_ms{{service="{svc["service"]}"}} {svc["latency_ms"]}')
    return "\n".join(lines) + "\n"
