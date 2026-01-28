# Finance Green Agent — Cycle Log

## Cycle 0
**Context:** Initial scaffolding for offline-first, manual A2A server with strict replicability.

**Objectives:**
- Pure FastAPI A2A endpoints (/manifest, /start_task, /message)
- Offline cache-backed tools (web + EDGAR)
- Evaluation harness for `public.csv`
- Ralph gate runner (16+ iterations)

**Requirements (AgentBeats + user):**
- No `a2a-sdk`
- Offline-default behavior with graceful cache-miss handling
- Citations must reference cache IDs
- Strict determinism (fixed seeds, pinned deps, logs)
- Ralph gate with `passes: false` at start

**Status:** Core scaffold implemented

**Compliance checks:**
- A2A manual endpoints: implemented (FastAPI)
- Offline cache tools: implemented (web + EDGAR + local parse)
- Replicability: deterministic seed hook + pinned deps
- Ralph gate: Python runner added (16+ iterations supported)
