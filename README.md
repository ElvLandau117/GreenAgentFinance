# GreenAgentFinance - Financial Q&A Evaluation System

## AgentBeats Finance Competition - Phase 1

---

## 1. Abstract

The **Green Agent** constitutes the core evaluation framework for the AgentBeats Finance Competition (Phase 1), engineered to assess participant agents—designated as **Purple Agents**—on financial analysis and information retrieval tasks. The system employs a deterministic, rubric-based scoring methodology to ensure objective, reproducible, and transparent evaluation across all submissions.

The evaluation framework addresses a fundamental challenge in financial AI: the ability to accurately retrieve, synthesize, and present financial information from authoritative sources while maintaining factual correctness and citation integrity.

## 1.1. Video presentation
You can see the proyect overview here: https://youtu.be/Gb1swCYEp0E

---

## 2. Evaluation Scope

The evaluator assesses agent responses across a curated dataset of **50 financial questions** spanning five distinct task categories:

| Category | Description | Complexity |
|----------|-------------|------------|
| **Market Analysis** | Corporate event assessment including mergers, acquisitions, and strategic business decisions | High |
| **Trend Analysis** | Historical financial metric interpretation and temporal pattern recognition | Medium |
| **Guidance Comparison** | Quantitative assessment of actual performance against corporate guidance (beat/miss analysis) | Medium |
| **Complex Retrieval** | Multi-dimensional numerical data extraction requiring cross-referencing of financial documents | High |
| **Qualitative Retrieval** | Structured extraction of non-numerical corporate information | Low |

---

## 3. System Architecture

The competition infrastructure comprises three interconnected components operating within an isolated Docker network environment:

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           EVALUATION ARCHITECTURE                               │
│                                                                                 │
│  ┌──────────────────────────────────────────────────────────────────────────┐  │
│  │                        ORCHESTRATION LAYER                                │  │
│  │                   (GreenAgentFinance-Leaderboard)                        │  │
│  │                                                                          │  │
│  │   ┌─────────────┐    ┌─────────────┐    ┌─────────────────────────┐     │  │
│  │   │ scenario.   │───▶│ generate_   │───▶│  docker-compose.yml     │     │  │
│  │   │ toml        │    │ compose.py  │    │  (dynamic generation)   │     │  │
│  │   └─────────────┘    └─────────────┘    └─────────────────────────┘     │  │
│  │                                                    │                     │  │
│  │                         GitHub Actions             │                     │  │
│  │                         CI/CD Pipeline             ▼                     │  │
│  └──────────────────────────────────────────────────────────────────────────┘  │
│                                                       │                         │
│                                          docker compose up                      │
│                                                       ▼                         │
│  ┌──────────────────────────────────────────────────────────────────────────┐  │
│  │                         DOCKER NETWORK                                    │  │
│  │                                                                          │  │
│  │   ┌────────────────────┐         A2A Protocol        ┌────────────────┐  │  │
│  │   │   AgentBeats       │◀───────────────────────────▶│  GREEN AGENT   │  │  │
│  │   │   Client           │         (JSON-RPC)          │  (Evaluator)   │  │  │
│  │   │   (Orchestrator)   │                             │  Port: 9009    │  │  │
│  │   └────────────────────┘                             └───────┬────────┘  │  │
│  │                                                              │           │  │
│  │                                                    Questions │           │  │
│  │                                                  (public.csv)│           │  │
│  │                                                              ▼           │  │
│  │                                                      ┌────────────────┐  │  │
│  │                                                      │ PURPLE AGENT   │  │  │
│  │                                                      │ (Participant)  │  │  │
│  │                                                      │ Port: 9009     │  │  │
│  │                                                      └────────────────┘  │  │
│  │                                                                          │  │
│  └──────────────────────────────────────────────────────────────────────────┘  │
│                                                       │                         │
│                                                       ▼                         │
│                                              ┌─────────────────┐                │
│                                              │  results.json   │                │
│                                              │  (Final Scores) │                │
│                                              └─────────────────┘                │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Agent Interaction Protocol

Communication between agents adheres to the **A2A (Agent-to-Agent) Protocol**, an open standard for inter-agent messaging. All interactions occur via JSON-RPC over HTTP.

### 4.1 Evaluation Flow Sequence

```
┌──────────────┐          ┌──────────────┐          ┌──────────────┐
│ Orchestrator │          │ Green Agent  │          │ Purple Agent │
│  (Client)    │          │ (Evaluator)  │          │(Participant) │
└──────┬───────┘          └──────┬───────┘          └──────┬───────┘
       │                         │                         │
       │  1. Initialize Session  │                         │
       │────────────────────────▶│                         │
       │                         │                         │
       │  2. Load Questions      │                         │
       │  (public.csv)           │                         │
       │                         │                         │
       │                         │  3. Send Question       │
       │                         │────────────────────────▶│
       │                         │     (JSON-RPC)          │
       │                         │                         │
       │                         │                         │  4. Process Query
       │                         │                         │  - Web Search
       │                         │                         │  - SEC EDGAR
       │                         │                         │  - HTML Parsing
       │                         │                         │
       │                         │  5. Return Answer       │
       │                         │◀────────────────────────│
       │                         │     + Citations         │
       │                         │                         │
       │                         │  6. Evaluate Response   │
       │                         │  - Rubric Matching      │
       │                         │  - Citation Validation  │
       │                         │                         │
       │                         │  [Repeat for 50 Q's]    │
       │                         │                         │
       │  7. Return Results      │                         │
       │◀────────────────────────│                         │
       │     (results.json)      │                         │
       │                         │                         │
```

### 4.2 A2A Protocol Endpoints

All agents expose standardized endpoints on port **9009**:

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/.well-known/agent-card.json` | GET | Agent capability discovery and metadata |
| `/v1/message:send` | POST | Synchronous message transmission |
| `/v1/message:stream` | POST | Server-Sent Events (SSE) streaming |
| `/v1/tasks/{id}` | GET | Task status retrieval |
| `/v1/tasks/{id}:cancel` | POST | Task cancellation |

---

## 5. Scoring Methodology

Each response undergoes **rubric-based evaluation** utilizing two primary operators:

| Operator | Function | Implementation |
|----------|----------|----------------|
| **Correctness** | Validates presence of predefined factual criteria | Normalized text matching against reference criteria |
| **Contradiction** | Ensures semantic consistency | Absence verification of conflicting statements |

Additionally, a **Citation Validation** mechanism verifies that all referenced sources exist within the evaluator's authenticated cache manifest, ensuring traceability and source integrity.

### 5.1 Output Metrics

| Metric | Description | Range |
|--------|-------------|-------|
| `average_score` | **Primary evaluation metric** | 0.0 - 1.0 |
| `passed` | Questions satisfying all rubric criteria | 0 - 50 |
| `citation_valid` | Responses with verifiable source citations | 0 - 50 |
| `errors` | Communication failures or timeout occurrences | ≥ 0 |
| `duration_seconds` | Total evaluation runtime | > 0 |

### 5.2 Result Structure

```json
{
  "winner": "participant_role",
  "participants": {
    "participant": {
      "summary": {
        "total": 50,
        "passed": 42,
        "average_score": 0.84,
        "citation_valid": 38,
        "errors": 0,
        "duration_seconds": 234.5
      },
      "results": [...]
    }
  }
}
```

---

## 6. Technical Specifications

| Specification | Value |
|---------------|-------|
| **Deterministic Execution** | Fixed seed initialization (default: 42) ensures reproducibility |
| **Offline Operation** | Evaluation tools operate against pre-cached dataset |
| **Timeout Constraint** | 120-second maximum response window per question |
| **Network Isolation** | External network access disabled during evaluation (unless OpenRouter enabled) |
| **Container Runtime** | Docker with isolated network bridge |
| **Language Runtime** | Python 3.13 |

---

## 7. Project Structure

```
src/finance_green_agent/
├── server.py          # FastAPI A2A endpoints
├── green_eval.py      # Evaluation orchestration
├── a2a_schemas.py     # A2A protocol data models
├── task_store.py      # In-memory task storage
├── agent_core/        # Core agent logic (agent.py, prompt.py, tools_base.py)
├── tools/             # OFFLINE tools (web_search, edgar_search, html_parser)
└── eval/              # Scoring (rubric.py, public_eval.py)
```

---

## 8. Tools


| Tool | Description |
|------|-------------|
| `web_search` | Search  web pages |
| `edgar_search` | Search pre-downloaded SEC filings |
| `parse_html` | Extract text from cached HTML |
| `citation_validator` | Validate source citations |

---

## 9. Installation

```bash
# Install dependencies
uv sync

# Run server locally
uv run src/finance_green_agent/server.py --host 0.0.0.0 --port 9009
```

---

## 10. Docker

```bash
# Build Docker image
docker build -t greenagentfinance .

# Run container
docker run -p 9009:9009 greenagentfinance
```

**Docker Image:** `ghcr.io/elvlandau117/greenagentfinance`

---

## 11. Evaluation Configuration

Example `scenario.toml` for single participant:

```toml
[green_agent]
agentbeats_id = "019c066d-d16f-7bf0-9e30-4a3eac7100fc"
env = { LOG_LEVEL = "INFO" }

[[participants]]
agentbeats_id = "PARTICIPANT_AGENTBEATS_ID"
name = "participant"
env = {}

[config]
seed = 42              # For reproducibility
maxQuestions = 50      # Max questions from public.csv
timeoutSeconds = 120   # Timeout per question
participantRole = "participant"
allowNetwork = false   # Network disabled during evaluation
```

---

## 12. Submission Workflow

1. **Fork** the Leaderboard repository
2. **Configure** `scenario.toml` with participant `agentbeats_id`
3. **Push** changes to trigger GitHub Actions workflow
4. **Review** generated `results.json` evaluation output
5. **Submit** Pull Request for official leaderboard inclusion

---

## 13. Related Repositories

| Repository | Purpose |
|------------|---------|
| [purple-agent-finance](https://github.com/elvlandau117/purple-agent-finance) | Participant agent (competitor) | 
| [GreenAgentFinance-Leaderboard](https://github.com/elvlandau117/GreenAgentFinance-Leaderboard) | Orchestrator (CI/CD + Docker Compose) |

---
**The purple agent is Based on https://github.com/vals-ai/finance-agent/tree/main** (Main repo of the finance analyst made by the authors of the paper found in https://arxiv.org/pdf/2508.00828)

## License

MIT
