# AGENTS

## Purpose

This delivery implements a production-oriented RL environment for a compact Anthropic core workflow. The environment is designed for local execution, seeded resettable state, and deterministic API-backed task transitions.

## Repository Layout

- `app.py`: local web server and API implementation
- `api/openapi.yaml`: owned API contract for all environment actions
- `data/seed_state.json`: canonical seeded state and reset source
- `static/index.html`: lightweight UI for local demo and QA

## Local Commands

Run locally:

```bash
python3 app.py
```

The app prefers port `8016` and automatically falls forward to the next open local port if needed.

## Test Commands

Smoke test with curl once the server is running:

```bash
curl http://127.0.0.1:8000/api/state
curl -X POST http://127.0.0.1:8016/api/reset
```

## Agent Rules

- Keep `api/openapi.yaml` aligned with the running server behavior.
- Every user-visible mutation must correspond to a restorable state transition.
- Seed state must remain deterministic and reusable through `POST /api/reset`.
- Prefer low-dependency changes unless the user explicitly asks for a richer stack.
- Preserve a clear local launch path at all times.

## Restore and Reset

- The runtime keeps an in-memory working copy of `data/seed_state.json`.
- `POST /api/reset` restores the seeded baseline.
- `POST /api/tasks/<id>/transition` records a transition event and mutates the working state.
- Evaluation can reconstruct state from the current snapshot plus `transitionLog`.
