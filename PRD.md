# PRD: Anthropic Core Workflow RL Environment

## Product Summary

This delivery chooses the default target workflow: Anthropic's core workflow, modeled as a compact task-operations environment for RL training and evaluation. The environment focuses on triaging work items, inspecting details, applying state transitions, assigning ownership, adding audit notes, and resetting back to a deterministic seed.

## Environment Goal

Provide a production-ready RL environment with:

- Real task state transitions
- Deterministic seeded fixtures
- Replayable transition history
- Explicit OpenAPI ownership
- A local launch path and deployable web surface

## User Persona and Task Objective

- Persona: operations agent or internal workflow coordinator
- Objective: move work items through the queue accurately while preserving auditability and reset semantics

## Boundaries and Exclusions

Included:

- Task list view
- Task detail view
- Status changes
- Assignee changes
- Note appends
- Reset to seeded baseline
- Environment snapshot retrieval

Excluded in this first slice:

- Authentication
- Multi-user concurrency
- File attachments
- Notification delivery
- External database service

## Reset Conditions and Seeded Starting State

Seeded state is defined in `data/seed_state.json` and contains:

- Environment metadata
- Three representative work items across queued, in-progress, and blocked states
- Empty transition log

`POST /api/reset` restores the exact seed.

## State Model and Restore Strategy

State model:

- `environment`
- `tasks[]`
- `transitionLog[]`

Every meaningful action mutates the working copy and appends a log entry with timestamp, task id, assignee, status, and note. Restore is deterministic because the runtime can reload the seed and replay transitions in order.

## Observation Space

Agent-observable data:

- Task ids, titles, status, priority, assignee, notes
- Full environment snapshot from `GET /api/state`
- UI state rendered from the same backing data

## Action Space

Primary actions:

- Select task
- Change task status
- Change assignee
- Append note
- Reset environment

API actions:

- `GET /api/state`
- `POST /api/tasks/{taskId}/transition`
- `POST /api/reset`

## Reward Model

Positive reward:

- Moving blocked or queued items to completed
- Adding a note when required for audit context
- Recovering the environment correctly with reset

Negative reward:

- Invalid or unnecessary transitions
- Reassignments that contradict the task objective
- State changes that omit required context

## Termination Conditions

- Episode success: all target tasks reach their requested terminal state
- Episode failure: invalid mutation budget exceeded or evaluation time limit reached
- Episode reset: explicit reset action

## API Surface and OpenAPI Ownership

The source of truth for the environment API is `api/openapi.yaml`. Every API change must update this contract in the same change set.

## Backend and Data Model Requirements

- Zero-dependency Python server for local reliability
- Canonical seed fixture in `data/seed_state.json`
- In-memory working state for local/dev/demo use
- Transition log for replay and audit
- Reset path that fully restores seed state

## Repository Structure

Required root:

- `AGENTS.md`
- `README.md`
- `PRD.md`
- `app.py`
- `api/openapi.yaml`
- `data/seed_state.json`
- `static/index.html`

## Local Development and Launch

Local launch command:

```bash
python3 app.py
```

The server prefers port `8016` and falls forward automatically if the port is already occupied.

## Hosting and Deployment Plan

- Preferred host: Vercel
- If CLI is unavailable, use Vercel web import and configure Python entry handling or static proxy routing as needed

## Instrumentation and Data Requirements

- Snapshot endpoint for evaluator reads
- Transition log for replayability
- Deterministic seed fixture for reset-based episode setup

## Evaluation Scenarios

- Complete a queued review task
- Reassign an in-progress implementation task
- Recover from a bad transition using reset
- Add note context before closing a task

## QA Plan

- Local API validation for state, transition, and reset
- Browser walkthrough of seeded environment
- Recorded QA artifact showing one successful transition and reset
- Post-deploy smoke check on the hosted URL

## Major Risks and Open Questions

- Vercel Python runtime specifics may require lightweight routing glue
- Google Docs and GitHub publishing depend on authenticated browser or API access
- Richer workflow fidelity may require additional seeded entities in a later phase
