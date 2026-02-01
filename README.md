# GreenAgentFinance - Evaluator Agent

Evaluator agent for the **AgentBeats Finance Competition (Phase 1)**. This agent evaluates participant agents against a financial Q&A dataset using offline tools and rubric-based scoring.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              EVALUATION FLOW                                │
│                                                                             │
│   Participant        GreenAgentFinance-Leaderboard         Docker Network   │
│       │                        │                                │           │
│       │  Fork + Edit           │                                │           │
│       │  scenario.toml         │                                │           │
│       │───────────────────────>│                                │           │
│       │                        │  GitHub Actions                │           │
│       │                        │  docker compose up             │           │
│       │                        │───────────────────────────────>│           │
│       │                        │                                │           │
│       │                        │     ┌──────────────────────────┴─────┐    │
│       │                        │     │  ┌─────────────────────────┐   │    │
│       │                        │     │  │  AgentBeats Client      │   │    │
│       │                        │     │  │  (Orchestrator)         │   │    │
│       │                        │     │  └───────────┬─────────────┘   │    │
│       │                        │     │              │                 │    │
│       │                        │     │              │ A2A Protocol    │    │
│       │                        │     │              ▼                 │    │
│       │                        │     │  ┌─────────────────────────┐   │    │
│       │                        │     │  │  Green Agent :9009      │   │    │
│       │                        │     │  │  (Evaluator)            │   │    │
│       │                        │     │  └───────────┬─────────────┘   │    │
│       │                        │     │              │                 │    │
│       │                        │     │              │ Questions       │    │
│       │                        │     │              │ (public.csv)    │    │
│       │                        │     │              ▼                 │    │
│       │                        │     │  ┌─────────────────────────┐   │    │
│       │                        │     │  │  Purple Agent :9009     │   │    │
│       │                        │     │  │  (Participant)          │   │    │
│       │                        │     │  └─────────────────────────┘   │    │
│       │                        │     └────────────────────────────────┘    │
│       │                        │                                │           │
│       │                        │<───────────────────────────────│           │
│       │                        │         results.json           │           │
│       │                        │                                │           │
│       │  PR with results       │                                │           │
│       │<───────────────────────│                                │           │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Project Structure

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

## Tech Stack

- Python 3.13
- FastAPI + Uvicorn
- Custom A2A protocol implementation
- model-library for LLM abstraction

## Offline Tools

All tools use a local cache for deterministic evaluation:

| Tool | Description |
|------|-------------|
| `offline_web_search` | Search pre-downloaded web pages |
| `offline_edgar_search` | Search pre-downloaded SEC filings |
| `parse_cached_html` | Extract text from cached HTML |
| `citation_validator` | Validate source citations |

## A2A Protocol Endpoints

All endpoints are exposed on port **9009**:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/.well-known/agent-card.json` | GET | Agent metadata (capabilities, skills) |
| `/v1/message:send` | POST | Send message (blocking) |
| `/v1/message:stream` | POST | Send message (SSE streaming) |
| `/v1/tasks/{id}` | GET | Get task status |
| `/v1/tasks/{id}:cancel` | POST | Cancel task |

## Scoring System

**Primary Metric:** `average_score` (0.0 - 1.0) - higher is better

**Criteria per question:**
- `correctness` - Is the answer factually correct?
- `contradiction` - Are there internal contradictions?
- `citations` - Are cited sources valid?

**Result Structure:**
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

## Installation

```bash
# Install dependencies
uv sync

# Run server locally
uv run src/finance_green_agent/server.py --host 0.0.0.0 --port 9009
```

## Docker

```bash
# Build Docker image
docker build -t greenagentfinance .

# Run container
docker run -p 9009:9009 greenagentfinance
```

**Docker Image:** `ghcr.io/elvlandau117/greenagentfinance`

## Related Repositories

| Repository | Purpose |
|------------|---------|
| [purple-agent-finance](https://github.com/elvlandau117/purple-agent-finance) | Participant agent (competitor) |
| [GreenAgentFinance-Leaderboard](https://github.com/elvlandau117/GreenAgentFinance-Leaderboard) | Orchestrator (CI/CD + Docker Compose) |

## Evaluation Configuration

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

## Submission Flow

1. **Fork** the Leaderboard repository
2. **Edit** `scenario.toml` with your `agentbeats_id`
3. **Push** to trigger GitHub Actions
4. **Review** generated `results.json`
5. **Create PR** to submit results

## License

MIT
