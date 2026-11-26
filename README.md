# TraceMind AI: Autonomous Root-Cause Analysis and Self-Healing System for Distributed Applications

An end-to-end, multi-agent AI engineering project designed for autonomous observability, telemetry correlation, root-cause analysis (RCA), safety-checked self-healing remediation, and health verification across distributed microservices.

Built as an academic B.Tech Computer Science capstone project demonstrating production SRE (Site Reliability Engineering) concepts with LangGraph agent orchestration, FastAPI, React, and PostgreSQL.

---

## 1. Project Title
**TraceMind AI: Autonomous Root-Cause Analysis and Self-Healing System for Distributed Applications**

## 2. Project Overview
Modern distributed architectures and cloud microservices generate millions of logs, time-series metrics, and error traces. When a service degrades or fails, on-call engineers spend critical minutes or hours correlating disparate dashboards to locate the defect. 

**TraceMind AI** solves this operational bottleneck using a coordinated 4-agent autonomous pipeline. The system continuously ingests telemetry, detects statistical and threshold anomalies, investigates root causes using real telemetry evidence, suggests whitelisted remediation actions, enforces safety guardrails and human approval gates, safely applies approved fixes in a controlled simulation environment, and verifies metric recovery before generating post-mortem incident reports.

## 3. Problem Statement
In distributed cloud applications:
1. **Alert Fatigue & Fragmented Telemetry:** Disconnected logs, metrics, and traces make diagnosing cascading failures slow and manual.
2. **Delayed Mean Time to Recovery (MTTR):** Diagnosis delays cause prolonged downtime and SLA breaches.
3. **Risky Unchecked Remediation:** Blind automated execution or arbitrary LLM-generated shell commands can cause severe unintended damage.
4. **Lack of Auditability:** Ad-hoc fixes leave no structured post-mortem trail or metrics verification.

TraceMind AI addresses these challenges with automated correlation, explainable AI diagnosis, safety-gated remediation, and rigorous metric delta verification.

## 4. Project Objectives
- Ingest and visualize real-time microservice telemetry (CPU, memory, latency, request volume, error rates, and log streams).
- Perform deterministic threshold-based anomaly detection without relying on costly LLM comparisons.
- Implement specialized multi-agent workflows using LangGraph.
- Provide explainable root-cause diagnosis backed strictly by actual telemetry and log signatures.
- Provide deterministic rule-based fallbacks so the system functions 100% offline without API keys, with optional Groq LLM integration.
- Implement a strict Remediation Registry preventing execution of arbitrary or unsafe commands.
- Provide a Human-in-the-Loop (HITL) approval gate for high-risk recovery actions.
- Execute controlled recovery actions in a reproducible simulation engine.
- Verify recovery by comparing pre-action and post-action metrics against health criteria.
- Persist incident history and generate downloadable post-mortem audit reports.

## 5. Key Features
- **4 Autonomous Specialized AI Agents:** Monitoring, Root-Cause Analysis, Remediation, and Verification.
- **5 Controlled Failure Scenarios:** High CPU Overload, Memory Leak / Cache Exhaustion, Database Connection Pool Failure, Downstream API Latency, and High HTTP 500 Error Rate.
- **Deterministic Anomaly Detection:** Real Python calculations and rolling window thresholds.
- **Optional Groq LLM Integration:** Uses LLaMA 3.3 70B for analytical reasoning while falling back seamlessly to deterministic rules if no API key is provided.
- **Remediation Action Registry:** Whitelisted, bounded operations classified by risk (`LOW`, `MEDIUM`, `HIGH`).
- **Human-in-the-Loop Safety Barrier:** Disruptive actions require explicit human operator approval.
- **Post-Recovery Verification:** Compares before/after metric deltas (delta %, latency drop, error rate drop).
- **Post-Mortem Markdown Reports:** Automatic report generation and direct `.md` file download.
- **Real-Time React Dashboard:** Clean, functional CSE student engineering dashboard built with Vite, Recharts, and Lucide React.
- **Dual Deployment Modes:** Run via Docker Compose (PostgreSQL container) or standalone local dev (automatic SQLite fallback).

## 6. How TraceMind AI Works
1. **Telemetry Collection:** Simulated microservices continuously emit metrics (CPU, RAM, latency, error count) and structured logs.
2. **Monitoring Agent:** Evaluates metrics against SLAs (CPU > 80%, RAM > 80%, Latency > 1000ms, Error rate > 5%). When an anomaly is detected, it logs an Anomaly Report and creates an incident.
3. **RCA Agent:** Correlates log traces and metrics to deduce the probable root cause, assigns a confidence score, extracts evidence quotes, and formulates alternative hypotheses.
4. **Remediation Agent:** Queries the whitelisted Remediation Registry, matches the diagnosis to a safe recovery action, classifies risk, and checks if operator approval is required.
5. **Approval Gate:** If the action has `MEDIUM` or `HIGH` risk, execution pauses at `Awaiting Approval` until an operator approves or rejects it in the UI.
6. **Controlled Execution:** Once approved, the remediation action is safely dispatched to the simulation engine.
7. **Verification Agent:** Gathers post-remediation telemetry, checks if metrics returned to safe ranges, calculates improvement deltas, and marks the incident as `Resolved`.
8. **Incident Report:** Compiles a full audit report detailing root cause, approval record, and metric comparison table.

## 7. Four-Agent Architecture

| Agent | Responsibility | Key Inputs | Processing Logic | Output |
|---|---|---|---|---|
| **1. Monitoring Agent** | Telemetry ingestion & anomaly detection | CPU, Memory, Latency, Error Rate, Logs | Rolling threshold analysis & error signature scanning | Anomaly Report, Severity Rating |
| **2. RCA Agent** | Root-cause identification & correlation | Anomaly Report, Logs, Metrics, Topology | Log signature matching, rule engine, optional Groq LLM | Root Cause, Confidence (0-100%), Telemetry Evidence |
| **3. Remediation Agent** | Safe recovery recommendation & safety checks | Root Cause, Risk Matrix, Approval Status | Whitelisted Action Registry, Risk Classification | Recommended Action, Risk Level, Approval Status |
| **4. Verification Agent** | Health validation & metrics delta comparison | Pre/Post Metrics, Health Probes | Metric delta calculation, SLA compliance check | Verification Status (`Resolved`/`Failed`), Delta Table |

## 8. System Architecture Diagram

```mermaid
flowchart TD
    subgraph S1["Telemetry & Services"]
        SIM["Simulation Engine\n(5 Microservices)"]
        METRICS["Metrics Stream\n(CPU, Mem, Latency, Errors)"]
        LOGS["Structured Log Stream\n(INFO, WARN, ERROR)"]
        SIM --> METRICS
        SIM --> LOGS
    end

    subgraph S2["TraceMind AI Multi-Agent Workflow"]
        A1["Agent 1: Monitoring Agent\n(Threshold & Pattern Detection)"]
        A2["Agent 2: Root-Cause Analysis Agent\n(Rules / Groq LLM Analysis)"]
        A3["Agent 3: Remediation Agent\n(Whitelisted Action Registry)"]
        GATE{"Requires\nHuman Approval?"}
        HUMAN["Human-in-the-Loop\nApproval Gate"]
        EXEC["Remediation Execution\n(Controlled Simulation)"]
        A4["Agent 4: Verification Agent\n(Before/After Delta Check)"]

        METRICS --> A1
        LOGS --> A1
        A1 -->|Detected Anomaly| A2
        A2 -->|Diagnosis & Evidence| A3
        A3 --> GATE
        GATE -->|Yes (High/Med Risk)| HUMAN
        GATE -->|No (Low Risk)| EXEC
        HUMAN -->|Approved| EXEC
        HUMAN -->|Rejected| STOP["Incident Aborted"]
        EXEC --> A4
        A4 -->|Verified Recovery| RESOLVED["Incident Resolved\n& Report Generated"]
    end

    subgraph S3["Persistence & UI"]
        DB[("PostgreSQL / SQLite\nDatabase")]
        UI["React + Vite Dashboard\n(8 Views & Recharts)"]

        A1 -.-> DB
        A2 -.-> DB
        A3 -.-> DB
        A4 -.-> DB
        DB <--> UI
        UI -->|Trigger Fault| SIM
        UI -->|Approve/Reject| HUMAN
    end
```

## 9. Technology Stack
- **Backend:** Python 3.11/3.12/3.13, FastAPI, Uvicorn, Pydantic v2, SQLAlchemy 2.0, PostgreSQL (with SQLite zero-dependency fallback).
- **Agent Orchestration:** LangGraph (StateGraph, conditional edges, structured incident state).
- **AI / LLM Integration:** Optional Groq API (`llama-3.3-70b-versatile` / OpenAI-compatible API) with high-precision deterministic rule fallback.
- **Frontend:** React 18, Vite, JavaScript, CSS3, Recharts, Lucide React icons.
- **Infrastructure:** Docker, Docker Compose, Nginx, PostgreSQL 16 container.
- **Testing:** pytest, FastAPI TestClient.

## 10. Project Directory Structure
```
TraceMind-AI/
├── backend/
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── state.py            # LangGraph shared incident state schema
│   │   ├── monitoring.py       # Agent 1: Monitoring & anomaly detection
│   │   ├── rca.py              # Agent 2: Root-cause analysis (rules + Groq LLM)
│   │   ├── remediation.py      # Agent 3: Whitelisted registry & safety validation
│   │   ├── verification.py     # Agent 4: Post-recovery health verification
│   │   └── workflow.py         # LangGraph StateGraph coordination
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes.py           # FastAPI REST API endpoints
│   ├── tests/
│   │   ├── __init__.py
│   │   └── test_system.py      # Comprehensive pytest test suite
│   ├── app.py                  # FastAPI entry point & CORS configuration
│   ├── config.py               # Application settings & environment variables
│   ├── database.py             # SQLAlchemy database setup & engine fallback
│   ├── models.py               # SQLAlchemy ORM database models
│   ├── schemas.py              # Pydantic schemas for APIs & state
│   ├── simulation.py           # Incident simulation engine (5 scenarios)
│   ├── requirements.txt        # Python backend dependencies
│   └── Dockerfile              # Backend container build specification
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── DashboardOverview.jsx   # Page A: KPIs & Recharts telemetry
│   │   │   ├── ServicesMonitoring.jsx  # Page B: Service topology & health
│   │   │   ├── IncidentManagement.jsx  # Page C: Incident table & status
│   │   │   ├── IncidentDetails.jsx     # Page D: 4 agents findings breakdown
│   │   │   ├── AgentActivity.jsx       # Page E: Agent journal & descriptions
│   │   │   ├── SimulationCenter.jsx    # Page F: 5 Fault triggers & logs
│   │   │   ├── RemediationApproval.jsx # Page G: Human approval decision gate
│   │   │   └── IncidentReports.jsx     # Page H: Post-mortem reports & download
│   │   ├── api.js              # Fetch client for backend endpoints
│   │   ├── App.jsx             # Main layout, sidebar navigation, status bar
│   │   ├── main.jsx            # React root mount
│   │   └── styles.css          # Clean engineering student visual styling
│   ├── index.html              # HTML entry point
│   ├── nginx.conf              # Nginx reverse proxy configuration for Docker
│   ├── package.json            # Node.js dependencies
│   ├── vite.config.js          # Vite config & API proxying
│   └── Dockerfile              # Frontend container build specification
│
├── docker-compose.yml          # Multi-container orchestration (DB, Backend, Frontend)
├── .env.example                # Template configuration variables
├── .gitignore                  # Git ignore rules
└── README.md                   # Comprehensive project documentation
```

## 11. System Requirements
- **Operating System:** macOS (Apple Silicon M1/M2/M3/M4 or Intel), Windows 10/11, or Linux (Ubuntu 20.04+).
- **RAM:** Minimum 4 GB (8 GB recommended).
- **Disk Space:** ~2 GB for Docker images or ~500 MB for manual local install.
- **Architecture:** `x86_64` or `arm64`.

## 12. Prerequisites
- **Git** installed: `git --version`
- **Docker & Docker Compose** (Recommended): `docker --version` and `docker compose version`
- *Or for manual running without Docker:*
  - **Python 3.11, 3.12, or 3.13**: `python3 --version`
  - **Node.js (v18 or v20+) & npm**: `node --version && npm --version`

---

## 13. Installation on macOS

### Option A: Using Docker Desktop (Recommended)
1. Install [Docker Desktop for Mac](https://www.docker.com/products/docker-desktop/) (select Apple Silicon or Intel).
2. Open Terminal and clone the repository:
   ```bash
   git clone <repository-url>
   cd TraceMind-AI
   ```
3. Copy environment configuration:
   ```bash
   cp .env.example .env
   ```
4. Start all services using Docker Compose:
   ```bash
   docker compose up --build
   ```
5. Open your browser:
   - **Frontend Dashboard:** [http://localhost:3000](http://localhost:3000)
   - **Backend API & Swagger Docs:** [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 14. Installation on Windows

### Option A: Using Docker Desktop (Recommended)
1. Install [Docker Desktop for Windows](https://www.docker.com/products/docker-desktop/) with WSL2 backend enabled.
2. Open PowerShell or Command Prompt as Administrator and clone the repository:
   ```powershell
   git clone <repository-url>
   cd TraceMind-AI
   ```
3. Copy the environment file:
   ```powershell
   Copy-Item .env.example .env
   ```
4. Build and start containers:
   ```powershell
   docker compose up --build
   ```
5. Access the application in your browser at [http://localhost:3000](http://localhost:3000).

---

## 15. Docker Installation and Setup
Docker Compose orchestrates three containers:
- `tracemind-db`: PostgreSQL 16 on port `5432` with volume `postgres_data` ensuring persistence across restarts.
- `tracemind-backend`: FastAPI on port `8000` with automated database healthcheck dependencies.
- `tracemind-frontend`: Production Nginx web server on port `3000` reverse-proxying `/api/` calls to the backend container.

### Useful Docker Commands:
- **Start containers in background:** `docker compose up -d`
- **View live logs:** `docker compose logs -f`
- **Stop containers safely:** `docker compose down`
- **Reset database data completely:** `docker compose down -v`
- **Rebuild images:** `docker compose build --no-cache`

---

## 16. Running the Project Using Docker
```bash
# 1. Clone repository
git clone <repo-url> && cd TraceMind-AI

# 2. Configure environment
cp .env.example .env

# 3. Launch stack
docker compose up --build
```
- Dashboard: [http://localhost:3000](http://localhost:3000)
- API Health: [http://localhost:8000/api/health](http://localhost:8000/api/health)

---

## 17. Running Backend Manually (Without Docker)
If you prefer not to use Docker, the backend automatically falls back to an embedded SQLite database (`sqlite:///./tracemind.db`) without requiring local PostgreSQL installation!

```bash
# 1. Navigate to backend directory
cd backend

# 2. Create and activate a Python virtual environment
python3 -m venv venv
source venv/bin/activate       # On Windows: .\venv\Scripts\activate

# 3. Install requirements
pip install -r requirements.txt

# 4. Start the FastAPI development server
cd ..
PYTHONPATH=. ./backend/venv/bin/uvicorn backend.app:app --host 127.0.0.1 --port 8000 --reload
```
The backend API is now running at [http://localhost:8000](http://localhost:8000).

---

## 18. Running Frontend Manually (Without Docker)
In a separate terminal window:
```bash
# 1. Navigate to frontend directory
cd frontend

# 2. Install dependencies
npm install

# 3. Start Vite development server
npm run dev
```
Open [http://localhost:5173](http://localhost:5173) in your browser. Vite proxies `/api` requests directly to `http://localhost:8000`.

---

## 19. Environment Variables
Stored in `.env`:

| Variable | Default Value | Description |
|---|---|---|
| `DATABASE_URL` | `postgresql://tracemind:tracemind123@db:5432/tracemind_db` | PostgreSQL connection string (falls back to SQLite locally) |
| `POSTGRES_USER` | `tracemind` | PostgreSQL container username |
| `POSTGRES_PASSWORD` | `tracemind123` | PostgreSQL container password |
| `POSTGRES_DB` | `tracemind_db` | Database name |
| `GROQ_API_KEY` | *(blank)* | Optional Groq API key for LLM diagnosis |
| `GROQ_MODEL` | `llama-3.3-70b-versatile` | LLM model identifier |
| `DEBUG` | `True` | Enables verbose logging |

---

## 20. Optional Groq API Configuration
TraceMind AI works **100% out-of-the-box without an API key** using its built-in deterministic rule and template engine.

To enable LLM-enhanced root-cause reasoning:
1. Sign up for free at [console.groq.com](https://console.groq.com) and generate an API key.
2. In your `.env` file, add:
   ```env
   GROQ_API_KEY=gsk_your_groq_api_key_here
   GROQ_MODEL=llama-3.3-70b-versatile
   ```
3. Restart the backend or run `docker compose up --build`.
4. The system will now invoke Groq for natural language correlation and highlight `Provider: Groq LLM` on incident cards. If Groq times out or reaches quota, it falls back seamlessly to deterministic rules.

---

## 21. Database Setup
- Tables are initialized automatically on application startup via SQLAlchemy `init_db()`.
- Managed tables:
  1. `incidents`: Full incident state, diagnosis, and metrics snapshot.
  2. `telemetry_records`: Historical metrics and log signatures.
  3. `agent_executions`: Agent execution timestamps, durations, and outputs.
  4. `remediation_actions`: Whitelisted action specs, risk levels, and approvals.
  5. `verification_results`: Before/after metric comparisons and SLA verification.
- **Persistence:** In Docker, PostgreSQL volume `postgres_data` persists data even if containers are stopped or rebuilt.

---

## 22. API Documentation
Interactive Swagger UI is available at `http://localhost:8000/docs`.

### Core Endpoints:
- `GET /api/health`: Health status, app version, and LLM mode.
- `GET /api/system/status`: Overall cluster health and active incident count.
- `GET /api/dashboard/summary`: Aggregated KPIs for cards and charts.
- `GET /api/dashboard/metrics`: 25-point rolling time series for Recharts.
- `GET /api/services`: List of simulated microservices and real-time telemetry.
- `GET /api/simulation/scenarios`: Returns the 5 available failure scenarios.
- `POST /api/simulation/trigger/{scenario}`: Injects a controlled failure and triggers autonomous investigation.
- `POST /api/simulation/reset`: Normalizes all microservices to baseline parameters.
- `GET /api/simulation/logs`: Real-time synthetic log stream.
- `GET /api/incidents`: List of all logged incidents.
- `GET /api/incidents/{incident_id}`: Comprehensive incident breakdown with all 4 agents' output.
- `POST /api/remediation/{incident_id}/approve`: Approves a pending action and immediately executes remediation & verification.
- `POST /api/remediation/{incident_id}/reject`: Rejects the recommended action.
- `GET /api/verification/{incident_id}`: Metric delta comparisons and health check results.
- `GET /api/reports`: List of resolved incident post-mortems.
- `GET /api/reports/{incident_id}/download`: Downloads a structured Markdown (`.md`) audit report.

---

## 23. Available Incident Scenarios

| Scenario Key | Failure Name | Target Service | Severity | Injected Anomaly | Expected Safe Recovery Action |
|---|---|---|---|---|---|
| `high_cpu` | High CPU Overload | `order-processing-service` | `HIGH` | CPU spikes to ~95%, response time to ~2450ms | `scale_down_workload` (throttle background concurrency) |
| `memory_exhaustion` | Memory Leak / Cache Saturation | `inventory-service` | `CRITICAL` | Memory consumption exceeds 92%, GC overhead | `clear_service_cache` (purge cache & force GC) |
| `db_failure` | Database Connection Pool Failure | `payment-service` | `CRITICAL` | Connection pool exhausted (50/50), timeouts | `reset_db_connection_pool` (flush sockets & re-init pool) |
| `api_latency` | Downstream API Latency | `api-gateway` | `MEDIUM` | Gateway response time spikes past 3400ms | `enable_circuit_breaker` (trip circuit to fallback cache) |
| `http_500` | High HTTP 500 Error Rate | `auth-service` | `HIGH` | Repeated NullPointer exceptions in JWT claims | `rollback_bad_configuration` (revert to rev-491) |

---

## 24. How to Trigger an Incident
1. Open the dashboard at [http://localhost:3000](http://localhost:3000) (or `http://localhost:5173`).
2. Click **Simulation Center** in the sidebar.
3. Choose one of the 5 cards (e.g., *Database Connection Pool Exhaustion*).
4. Click **Trigger Incident**.
5. Within 500ms, the Monitoring and RCA agents execute, and an alert banner appears with a direct link to the incident.

---

## 25. How to Approve Remediation
1. When an incident with `MEDIUM` or `HIGH` risk is diagnosed, its status becomes `Awaiting Approval`.
2. Navigate to **Remediation Approval** in the sidebar (indicated by an amber badge).
3. Review the proposed action, potential blast radius, and root cause diagnosis.
4. Click **Approve & Execute**.
5. The Remediation Agent safely applies the fix in the simulation, and the Verification Agent immediately executes.

---

## 26. How to Verify Recovery
1. Open the incident in **Incident Management** or click **Inspect Details**.
2. Scroll to the **Agent 4: Health Verification & Metric Deltas** section.
3. Review the live comparison table:
   - **Before vs After:** Demonstrates exact metric recovery (e.g., CPU 94.8% -> 28.2%, Latency 2450ms -> 155ms).
   - **Improvement Delta:** Displays delta percentage and recovery duration in seconds.
   - **Health Check Status:** Confirms all 5 services have returned to green.

---

## 27. How to Generate Reports
1. Navigate to **Incident Reports** in the sidebar.
2. Select any resolved incident from the left-hand log.
3. Preview the post-mortem report containing the executive summary, root cause evidence, approval details, and telemetry delta table.
4. Click **Download Markdown (.md)** to save a copy locally for presentation or viva evaluation.

---

## 28. Troubleshooting
- **Frontend shows "Backend Disconnected":** Ensure the backend server is running on port 8000 (`curl http://localhost:8000/api/health`).
- **Port 5432 or 8000 already in use:** Stop existing instances with `lsof -i :8000` or run Docker with mapped alternative ports in `docker-compose.yml`.
- **Database error on manual startup:** If PostgreSQL is not installed locally, TraceMind AI automatically connects to SQLite (`tracemind.db`). No manual action needed.

---

## 29. Common Errors and Their Solutions
- `ModuleNotFoundError: No module named 'backend'`: Always run python commands with `PYTHONPATH=.` from the project root.
- `OperationalError: could not connect to server`: The backend handles this gracefully by switching to local SQLite if PostgreSQL is unavailable.
- `vite: command not found`: Run `npm install` inside the `frontend/` directory before `npm run dev`.

---

## 30. Testing Instructions
The project includes a comprehensive automated test suite testing anomaly detection, RCA evidence generation, safety validation, the approval gate, and all 5 failure scenarios.

Run tests using pytest:
```bash
# Run pytest from project root
PYTHONPATH=. ./backend/venv/bin/pytest backend/tests/test_system.py -v
```

Expected output:
```
backend/tests/test_system.py::test_health_and_system_status PASSED
backend/tests/test_system.py::test_services_monitoring PASSED
backend/tests/test_system.py::test_simulation_scenarios_and_reset PASSED
backend/tests/test_system.py::test_monitoring_agent_detection PASSED
backend/tests/test_system.py::test_rca_agent_evidence_generation PASSED
backend/tests/test_system.py::test_remediation_safety_validation PASSED
backend/tests/test_system.py::test_full_incident_lifecycle_workflow PASSED
backend/tests/test_system.py::test_all_five_scenarios_trigger PASSED

8 passed in 0.3s
```

Frontend build test:
```bash
cd frontend && npm run build
```

---

## 31. Security Limitations
- **Simulation Environment:** Remediation actions are executed against a controlled simulation engine and do not execute arbitrary OS shell commands or modify physical infrastructure.
- **No Arbitrary LLM Execution:** The LLM is strictly used for analytical explanation. Remediation actions are selected exclusively from a hardcoded, whitelisted registry (`REMEDIATION_REGISTRY`).
- **No Hardcoded Credentials:** Secrets are managed via `.env` and environment variables.

---

## 32. Current Project Limitations
- Focuses on a 5-microservice simulated distributed cluster rather than large-scale enterprise Kubernetes clusters.
- Telemetry is generated deterministically by the simulation engine to ensure reliable, reproducible evaluation during university presentations.
- Distributed tracing spans follow OpenTelemetry concepts through trace IDs and log correlation, rather than a full Jaeger/Zipkin deployment.

---

## 33. Future Improvements
- Kubernetes Operator integration to apply approved remediations directly via Kubernetes Custom Resource Definitions (CRDs).
- eBPF-based kernel telemetry collection for real-world network packet inspection.
- Vector database (e.g. Chroma/Qdrant) integration for historical incident post-mortem retrieval (RAG).
- Slack/PagerDuty webhook integrations for real-time human operator approval notifications.

---

## 34. Team Member Contribution Section
*(University B.Tech Capstone Project)*

- **Backend & Multi-Agent Architecture:** Designed LangGraph state machine, 4 specialized agents, and FastAPI REST endpoints.
- **Simulation & Observability Engine:** Implemented reproducible fault-injection scenarios, synthetic telemetry streams, and metric calculation algorithms.
- **Frontend & Visualization:** Developed React dashboard, Recharts telemetry visualizations, human-in-the-loop approval interface, and markdown report generator.
- **DevOps & Testing:** Implemented Docker multi-stage builds, Docker Compose, automated pytest suite, and cross-platform compatibility.

---
**TraceMind AI** — Autonomous Root-Cause Analysis and Self-Healing Telemetry.
