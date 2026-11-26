import time
import random
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional

def utc_now():
    return datetime.now(timezone.utc)

class ServiceState:
    def __init__(self, service_id: str, name: str, base_cpu: float, base_mem: float, base_lat: float):
        self.service_id = service_id
        self.name = name
        self.base_cpu = base_cpu
        self.base_mem = base_mem
        self.base_lat = base_lat
        self.cpu = base_cpu
        self.mem = base_mem
        self.latency = base_lat
        self.requests = 120
        self.errors = 0
        self.status = "HEALTHY"

class SimulationEngine:
    """
    Controlled Incident Simulation Engine for TraceMind AI.
    Provides deterministic and reproducible telemetry for 5 real-world distributed failure scenarios.
    """
    
    SCENARIOS = {
        "high_cpu": {
            "name": "High CPU Overload",
            "service_id": "order-processing-service",
            "description": "Simulates an uncontrolled background batch calculation driving CPU past 90%",
            "severity": "HIGH",
            "risk_level": "MEDIUM",
            "recommended_action": "scale_down_workload"
        },
        "memory_exhaustion": {
            "name": "Memory Leak / Cache Exhaustion",
            "service_id": "inventory-service",
            "description": "Simulates memory retention in unevicted cache buffer causing memory pressure",
            "severity": "CRITICAL",
            "risk_level": "MEDIUM",
            "recommended_action": "clear_service_cache"
        },
        "db_failure": {
            "name": "Database Connection Pool Exhaustion",
            "service_id": "payment-service",
            "description": "Simulates exhausted connection pool causing queries to time out with 500s",
            "severity": "CRITICAL",
            "risk_level": "HIGH",
            "recommended_action": "reset_db_connection_pool"
        },
        "api_latency": {
            "name": "Downstream API Latency",
            "service_id": "api-gateway",
            "description": "Simulates downstream thread pool saturation causing API response times to spike past 3000ms",
            "severity": "MEDIUM",
            "risk_level": "LOW",
            "recommended_action": "enable_circuit_breaker"
        },
        "http_500": {
            "name": "High HTTP 500 Error Rate",
            "service_id": "auth-service",
            "description": "Simulates recurring null-pointer exceptions after a corrupted config deployment",
            "severity": "HIGH",
            "risk_level": "MEDIUM",
            "recommended_action": "rollback_bad_configuration"
        }
    }

    def __init__(self):
        self.mode = "normal"  # normal, incident, recovery
        self.active_scenario: Optional[str] = None
        self.scenario_start_time: Optional[datetime] = None
        self.recent_logs: List[Dict[str, Any]] = []
        self.history_metrics: List[Dict[str, Any]] = []
        self.init_services()
        self.generate_initial_history()

    def init_services(self):
        self.services: Dict[str, ServiceState] = {
            "order-processing-service": ServiceState("order-processing-service", "Order Processing Service", 24.5, 42.0, 140.0),
            "inventory-service": ServiceState("inventory-service", "Inventory Service", 18.0, 39.5, 95.0),
            "payment-service": ServiceState("payment-service", "Payment Gateway Service", 28.0, 48.0, 180.0),
            "api-gateway": ServiceState("api-gateway", "API Gateway Ingress", 32.0, 45.0, 65.0),
            "auth-service": ServiceState("auth-service", "Authentication Service", 15.0, 36.0, 80.0)
        }

    def reset(self):
        """Reset simulation back to normal baseline."""
        self.mode = "normal"
        self.active_scenario = None
        self.scenario_start_time = None
        self.init_services()
        self.add_log("INFO", "api-gateway", "Simulation reset to normal baseline state. All services healthy.")
        return {"status": "success", "message": "Simulation reset to normal state."}

    def trigger_scenario(self, scenario_key: str) -> Dict[str, Any]:
        """Trigger one of the 5 controlled incident scenarios."""
        if scenario_key not in self.SCENARIOS:
            raise ValueError(f"Unknown scenario: {scenario_key}. Must be one of {list(self.SCENARIOS.keys())}")
        
        self.mode = "incident"
        self.active_scenario = scenario_key
        self.scenario_start_time = utc_now()
        meta = self.SCENARIOS[scenario_key]
        service = self.services[meta["service_id"]]
        
        if scenario_key == "high_cpu":
            service.cpu = 94.8
            service.latency = 2450.0
            service.status = "DEGRADED"
            service.requests = 480
            service.errors = 28
            self.add_log("WARN", service.service_id, "Thread pool saturation: CPU utilization exceeded 90% threshold (Current: 94.8%)")
            self.add_log("ERROR", service.service_id, "Order worker thread timeout: batch calculation task #4928 blocked for 3500ms")

        elif scenario_key == "memory_exhaustion":
            service.mem = 92.4
            service.latency = 1850.0
            service.status = "DEGRADED"
            service.requests = 310
            service.errors = 18
            self.add_log("WARN", service.service_id, "Heap usage threshold exceeded: 92.4% memory allocated in cache partition")
            self.add_log("ERROR", service.service_id, "java.lang.OutOfMemoryError: GC overhead limit exceeded during inventory sync")

        elif scenario_key == "db_failure":
            service.status = "UNHEALTHY"
            service.latency = 4200.0
            service.requests = 250
            service.errors = 105
            self.add_log("ERROR", service.service_id, "FATAL: Connection pool 'db-pool-main' exhausted (active: 50/50, queued: 128)")
            self.add_log("ERROR", service.service_id, "psycopg2.OperationalError: could not connect to server: Connection timed out")

        elif scenario_key == "api_latency":
            service.latency = 3450.0
            service.cpu = 62.0
            service.status = "DEGRADED"
            service.requests = 620
            service.errors = 35
            self.add_log("WARN", service.service_id, "Upstream response deadline exceeded: average latency reached 3450ms")
            self.add_log("ERROR", service.service_id, "Gateway Timeout 504: downstream dependency 'recommendation-v2' failed to respond in 3000ms")

        elif scenario_key == "http_500":
            service.status = "UNHEALTHY"
            service.requests = 400
            service.errors = 152
            service.latency = 310.0
            self.add_log("ERROR", service.service_id, "HTTP 500 Internal Server Error on POST /v1/auth/tokens - NullPointer in JWT claim parser")
            self.add_log("ERROR", service.service_id, "Stack trace: NullPointerException at AuthValidator.validateSignature(AuthValidator.py:84)")

        return {
            "scenario": scenario_key,
            "name": meta["name"],
            "affected_service": meta["service_id"],
            "severity": meta["severity"],
            "mode": self.mode,
            "timestamp": self.scenario_start_time.isoformat()
        }

    def execute_remediation(self, action_name: str, target_service: str) -> Dict[str, Any]:
        """Apply the simulated recovery action and transition to recovery mode."""
        self.mode = "recovery"
        service = self.services.get(target_service)
        if not service:
            raise ValueError(f"Service {target_service} not found")

        log_msg = f"Remediation '{action_name}' executed on service '{target_service}'"
        
        if action_name == "scale_down_workload":
            service.cpu = 28.2
            service.latency = 155.0
            service.errors = 0
            service.status = "HEALTHY"
            self.add_log("INFO", target_service, "Background batch worker throttling enabled (concurrency dropped from 32 to 4).")
            self.add_log("INFO", target_service, "CPU normalized to 28.2%. Response time recovered.")

        elif action_name == "clear_service_cache":
            service.mem = 41.5
            service.latency = 110.0
            service.errors = 0
            service.status = "HEALTHY"
            self.add_log("INFO", target_service, "Evicted 1.8GB unreferenced objects from cache partition.")
            self.add_log("INFO", target_service, "Memory pressure relieved: current memory usage 41.5%.")

        elif action_name == "reset_db_connection_pool":
            service.latency = 190.0
            service.errors = 0
            service.status = "HEALTHY"
            self.add_log("INFO", target_service, "Database connection pool flushed and re-initialized (50 idle sockets established).")
            self.add_log("INFO", target_service, "Database health probe: OK (latency: 4ms). Zero active connection errors.")

        elif action_name == "enable_circuit_breaker":
            service.latency = 85.0
            service.errors = 2
            service.cpu = 34.0
            service.status = "HEALTHY"
            self.add_log("INFO", target_service, "Circuit breaker OPEN for slow downstream service; fallback cache served.")
            self.add_log("INFO", target_service, "Ingress latency dropped to 85ms.")

        elif action_name == "rollback_bad_configuration":
            service.errors = 0
            service.status = "HEALTHY"
            self.add_log("INFO", target_service, "Rolled back configuration rev-492 to known stable rev-491.")
            self.add_log("INFO", target_service, "HTTP 500 error rate dropped to 0.0%. All auth tokens parsing successfully.")
            
        else:
            # Fallback action
            service.status = "HEALTHY"
            service.errors = 0
            service.cpu = service.base_cpu
            service.mem = service.base_mem
            service.latency = service.base_lat
            self.add_log("INFO", target_service, f"Service restarted safely: status restored to HEALTHY.")

        self.active_scenario = None
        return {
            "status": "success",
            "action": action_name,
            "target_service": target_service,
            "message": log_msg,
            "timestamp": utc_now().isoformat()
        }

    def get_services_snapshot(self) -> List[Dict[str, Any]]:
        result = []
        now = utc_now()
        for s in self.services.values():
            # Add minor natural jitter in normal mode
            jitter_cpu = round(s.cpu + (random.uniform(-1.0, 1.0) if self.mode == "normal" else 0.0), 1)
            jitter_lat = round(s.latency + (random.uniform(-5.0, 5.0) if self.mode == "normal" else 0.0), 1)
            error_rate = round((s.errors / max(s.requests, 1)) * 100, 2)
            result.append({
                "service_id": s.service_id,
                "name": s.name,
                "status": s.status,
                "cpu_usage": max(5.0, min(100.0, jitter_cpu)),
                "memory_usage": s.mem,
                "response_time_ms": max(10.0, jitter_lat),
                "request_count": s.requests,
                "error_count": s.errors,
                "error_rate": error_rate,
                "last_updated": now.isoformat()
            })
        return result

    def get_service(self, service_id: str) -> Optional[Dict[str, Any]]:
        for item in self.get_services_snapshot():
            if item["service_id"] == service_id:
                return item
        return None

    def add_log(self, level: str, service_id: str, message: str):
        entry = {
            "timestamp": utc_now().isoformat(),
            "level": level,
            "service_id": service_id,
            "message": message
        }
        self.recent_logs.append(entry)
        if len(self.recent_logs) > 100:
            self.recent_logs.pop(0)

    def get_recent_logs(self, limit: int = 50) -> List[Dict[str, Any]]:
        return self.recent_logs[-limit:]

    def generate_initial_history(self):
        """Seed initial realistic metric timeline for graphs."""
        now_ts = int(time.time())
        for i in range(20, 0, -1):
            t = now_ts - (i * 30)
            iso_time = datetime.fromtimestamp(t, tz=timezone.utc).strftime("%H:%M:%S")
            self.history_metrics.append({
                "time": iso_time,
                "cpu_usage": round(25.0 + random.uniform(-3.0, 4.0), 1),
                "memory_usage": round(42.0 + random.uniform(-2.0, 2.0), 1),
                "response_time_ms": round(120.0 + random.uniform(-15.0, 20.0), 1),
                "error_rate": round(random.uniform(0.0, 0.4), 2)
            })

    def get_metrics_timeline(self) -> List[Dict[str, Any]]:
        """Return metric trend history with the latest snapshot appended."""
        now_iso = utc_now().strftime("%H:%M:%S")
        services = self.get_services_snapshot()
        avg_cpu = round(sum(s["cpu_usage"] for s in services) / len(services), 1)
        avg_mem = round(sum(s["memory_usage"] for s in services) / len(services), 1)
        avg_lat = round(sum(s["response_time_ms"] for s in services) / len(services), 1)
        avg_err = round(sum(s["error_rate"] for s in services) / len(services), 2)

        point = {
            "time": now_iso,
            "cpu_usage": avg_cpu,
            "memory_usage": avg_mem,
            "response_time_ms": avg_lat,
            "error_rate": avg_err
        }
        
        # Keep window of 25 points
        if len(self.history_metrics) >= 25:
            self.history_metrics.pop(0)
        self.history_metrics.append(point)
        return list(self.history_metrics)

simulation_engine = SimulationEngine()
