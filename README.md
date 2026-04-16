# Anthropic Core Workflow RL Environment

This delivery is a greenfield RL environment that models a compact Anthropic-style workflow: triage tasks, inspect details, change status, assign ownership, add notes, and reset to a seeded baseline.

## What is included

- A zero-dependency Python web app in `app.py`
- Static UI in `static/index.html`
- Seeded state in `data/seed_state.json`
- An OpenAPI contract in `api/openapi.yaml`
- Delivery instructions and agent rules in `AGENTS.md`

## Local run

```bash
cd /Users/aglit/Projects/anthropic-aglit/deliveries/anthropic-core-workflow-rl-20260416
python3 app.py
```

Then open the printed local URL. The app prefers `8016` and automatically falls forward to the next open port if that port is busy.

## Core flows

- View seeded work items
- Filter work by status and priority
- Open a work item detail panel
- Update status, assignee, and notes
- Reset the environment to the original seeded state
- Retrieve state snapshots through the API for evaluation and restore flows

## Validation

Run:

```bash
python3 app.py
```

Then verify:

- `GET /api/state`
- `POST /api/tasks/<id>/transition`
- `POST /api/reset`

## Deployment target

Default hosting target is Vercel. If Vercel CLI is unavailable, deploy through the Vercel web flow.
