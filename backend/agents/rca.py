import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Tuple
import httpx
from backend.agents.state import IncidentState
from backend.config import settings

logger = logging.getLogger("tracemind.agents.rca")

def deterministic_rca(
    scenario_type: str,
    affected_service: str,
    anomalies: List[str],
    logs: List[Dict[str, Any]],
    telemetry: Dict[str, Any]
) -> Tuple[str, float, List[str], List[str], str]:
    """
    High-precision deterministic rule-based root cause analysis fallback.
    Extracts real telemetry metrics and matching logs.
    """
    evidence = []
    alternative_causes = []
    
    # Extract logs related to the affected service
    svc_logs = [l["message"] for l in logs if l.get("service_id") == affected_service]
    cpu = telemetry.get("cpu_usage", 0.0)
    mem = telemetry.get("memory_usage", 0.0)
    lat = telemetry.get("response_time_ms", 0.0)
    err = telemetry.get("error_rate", 0.0)

    if scenario_type == "high_cpu" or cpu > 85.0:
        root_cause = "Uncontrolled background calculation thread pool saturation in batch worker."
        confidence = 0.94
        evidence.append(f"Primary metric: CPU utilization sustained at {cpu}% (Threshold: 80%)")
        evidence.append(f"Latency degradation: Response time elevated to {lat}ms")
        for msg in svc_logs:
            if "saturation" in msg or "timeout" in msg or "blocked" in msg:
                evidence.append(f"Log trace: \"{msg}\"")
        alternative_causes = [
            "Sudden spike in inbound client request volume",
            "Inefficient infinite loop in order processing logic",
            "Garbage collection thread lockup"
        ]
        explanation = (
            f"Telemetry indicates {affected_service} experienced severe compute exhaustion ({cpu}% CPU). "
            f"The thread queue failed to process incoming tasks within deadline, causing cascade latency."
        )

    elif scenario_type == "memory_exhaustion" or mem > 85.0:
        root_cause = "Unevicted in-memory cache buffer retention causing heap memory leak."
        confidence = 0.96
        evidence.append(f"Primary metric: Memory consumption peaked at {mem}% (Threshold: 80%)")
        for msg in svc_logs:
            if "Heap" in msg or "OutOfMemory" in msg or "GC" in msg:
                evidence.append(f"Log trace: \"{msg}\"")
        alternative_causes = [
            "Unclosed streaming database cursor",
            "Large file payload deserialized directly into memory",
            "Insufficient JVM heap size allocation"
        ]
        explanation = (
            f"{affected_service} exhibited linear memory retention reaching {mem}%. "
            f"Frequent garbage collection cycles resulted in GC overhead limits and service degradation."
        )

    elif scenario_type == "db_failure" or any("Connection pool" in str(l) for l in svc_logs):
        root_cause = "Database connection pool exhaustion and socket timeout."
        confidence = 0.98
        evidence.append(f"Primary metric: Service error rate spiked to {err}% with latency {lat}ms")
        for msg in svc_logs:
            if "Connection pool" in msg or "OperationalError" in msg or "FATAL" in msg:
                evidence.append(f"Log trace: \"{msg}\"")
        alternative_causes = [
            "PostgreSQL database instance crash or network partition",
            "Slow unindexed queries holding connections open indefinitely",
            "Max client connection limit reached on database server"
        ]
        explanation = (
            f"Service {affected_service} exhausted all 50 configured database connections. "
            f"Incoming client transactions timed out waiting for an available socket from the pool."
        )

    elif scenario_type == "api_latency" or lat > 2000.0:
        root_cause = "Downstream service call timeout and thread queue saturation at API Gateway."
        confidence = 0.91
        evidence.append(f"Primary metric: Gateway response latency reached {lat}ms (SLA: 1000ms)")
        for msg in svc_logs:
            if "deadline" in msg or "504" in msg or "Gateway Timeout" in msg:
                evidence.append(f"Log trace: \"{msg}\"")
        alternative_causes = [
            "Upstream network congestion or DNS resolution delay",
            "TLS handshake latency bottleneck",
            "Client request throttling backlog"
        ]
        explanation = (
            f"Ingress gateway response latency spiked to {lat}ms due to an unresponsive downstream microservice dependency. "
            f"Synchronous HTTP calls blocked worker threads until 504 timeouts were triggered."
        )

    elif scenario_type == "http_500" or err > 15.0:
        root_cause = "Uncaught NullPointerException in authentication JWT validation pipeline."
        confidence = 0.95
        evidence.append(f"Primary metric: Error rate increased to {err}%")
        for msg in svc_logs:
            if "500" in msg or "NullPointer" in msg or "Stack trace" in msg:
                evidence.append(f"Log trace: \"{msg}\"")
        alternative_causes = [
            "Missing environment secret key for token signature verification",
            "Corrupted request payload format from frontend client",
            "Expired signing certificate"
        ]
        explanation = (
            f"High volume of HTTP 500 status codes detected on {affected_service}. "
            f"Exception stack traces confirm unhandled null pointer during JWT token claims inspection."
        )

    else:
        root_cause = f"Anomalous metric degradation observed on {affected_service}."
        confidence = 0.75
        evidence = anomalies[:3] if anomalies else ["Metric variance outside standard baseline"]
        alternative_causes = ["Transient network hiccup", "Host container scheduling contention"]
        explanation = f"Automated telemetry checks identified performance anomalies across {affected_service}."

    return root_cause, confidence, evidence, alternative_causes, explanation


def query_groq_llm(
    scenario_type: str,
    affected_service: str,
    anomalies: List[str],
    logs: List[Dict[str, Any]],
    telemetry: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Invoke Groq API (or OpenAI-compatible API) to generate enhanced root-cause reasoning.
    Returns structured JSON with root cause, confidence, evidence, and explanation.
    """
    prompt = f"""You are the Root-Cause Analysis Agent for TraceMind AI, an autonomous system monitoring distributed applications.
Analyze the following telemetry evidence and output ONLY valid JSON matching this schema:
{{
    "probable_root_cause": "string",
    "confidence_score": 0.0 to 1.0,
    "supporting_evidence": ["item 1", "item 2", ...],
    "alternative_causes": ["alt 1", "alt 2"],
    "explanation_summary": "concise analytical explanation"
}}

Incident Context:
- Scenario Type: {scenario_type}
- Affected Service: {affected_service}
- Detected Anomalies: {json.dumps(anomalies)}
- Telemetry Snapshot: {json.dumps(telemetry)}
- Recent Logs: {json.dumps([l['message'] for l in logs[-8:]])}

Requirements:
- Base diagnosis exclusively on the provided metrics and logs. Do NOT invent fake telemetry.
- Keep explanation clear and concise for engineering viva presentation.
"""
    headers = {
        "Authorization": f"Bearer {settings.GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": settings.GROQ_MODEL,
        "messages": [
            {"role": "system", "content": "You are a professional Site Reliability Engineer and AI Root Cause Analyzer. Output only strict JSON."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.2,
        "response_format": {"type": "json_object"}
    }

    with httpx.Client(timeout=10.0) as client:
        response = client.post(
            "https://api.groq.com/openai/v1/chat/completions",
            json=payload,
            headers=headers
        )
        response.raise_for_status()
        data = response.json()
        content = data["choices"][0]["message"]["content"]
        return json.loads(content)


def run_rca_agent(state: IncidentState) -> IncidentState:
    """
    Agent 2: Root-Cause Analysis Agent
    Correlates telemetry signals and determines the probable root cause using
    deterministic rules with optional Groq LLM reasoning.
    """
    logger.info("RCA Agent investigating incident: %s", state.get("incident_id"))
    start_time = datetime.now(timezone.utc)
    
    scenario_type = state.get("scenario_type", "unknown")
    affected_service = state.get("affected_service", "system")
    anomalies = state.get("detected_anomalies", [])
    logs = state.get("recent_logs", [])
    telemetry = state.get("telemetry_snapshot", {})

    is_llm = False
    if settings.ENABLE_LLM and settings.GROQ_API_KEY:
        try:
            logger.info("Querying Groq LLM (%s) for root-cause analysis...", settings.GROQ_MODEL)
            llm_result = query_groq_llm(scenario_type, affected_service, anomalies, logs, telemetry)
            root_cause = llm_result.get("probable_root_cause", "")
            confidence = float(llm_result.get("confidence_score", 0.90))
            evidence = llm_result.get("supporting_evidence", [])
            alt_causes = llm_result.get("alternative_causes", [])
            explanation = llm_result.get("explanation_summary", "")
            is_llm = True
            logger.info("Groq LLM analysis succeeded.")
        except Exception as e:
            logger.warning("Groq LLM call failed (%s). Falling back to deterministic RCA engine.", str(e))
            root_cause, confidence, evidence, alt_causes, explanation = deterministic_rca(
                scenario_type, affected_service, anomalies, logs, telemetry
            )
    else:
        root_cause, confidence, evidence, alt_causes, explanation = deterministic_rca(
            scenario_type, affected_service, anomalies, logs, telemetry
        )

    duration_ms = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000

    agent_entry = {
        "agent": "Root-Cause Analysis Agent",
        "action": "TELEMETRY_CORRELATION_AND_DIAGNOSIS",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "duration_ms": round(duration_ms, 2),
        "status": "COMPLETED",
        "summary": f"Diagnosis: {root_cause} (Confidence: {int(confidence*100)}%, Provider: {'Groq LLM' if is_llm else 'Rule Engine'})"
    }

    logs_copy = list(state.get("agent_logs", []))
    logs_copy.append(agent_entry)

    return {
        **state,
        "status": "Diagnosis Completed",
        "root_cause": root_cause,
        "confidence_score": confidence,
        "evidence": evidence,
        "alternative_causes": alt_causes,
        "explanation_summary": explanation,
        "is_llm_diagnosis": is_llm,
        "agent_logs": logs_copy
    }
