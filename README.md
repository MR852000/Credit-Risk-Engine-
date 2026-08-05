# Credit Engine — Real-Time Developer Services Dashboard

A live, in-browser control panel that gives engineers a single place to **monitor a polyglot (Python + Java) credit-decisioning platform** and **launch the tools they need to work on it** — IDEs, cloud consoles, and data-layer diagnostics — without leaving the browser.

Built with **FastAPI** + **ReactPy** (server-rendered React components in pure Python), so the entire UI, state management, and real-time update loop live in one Python codebase — no separate frontend build step required.

---

## What this is

This dashboard is a "Developer-as-a-Service" style workbench. Instead of a static internal wiki with a list of links, it's a live application that:

- Streams **real-time system telemetry** (latency, throughput, rule-engine stats, event logs) via an `asyncio` background loop, pushed straight into the UI.
- Lets a developer **one-click launch a local IDE** (PyCharm, IntelliJ, VS Code, Spyder) pointed at the codebase, spawned as a detached OS process.
- Provides **quick-access login links** to cloud provider consoles (IBM Cloud, Oracle Cloud, AWS).
- Surfaces **live status panels** for the data/messaging layer (PostgreSQL, MySQL, Redis, Kafka) on demand.
- Visualizes the **Python ↔ Java protocol boundary** (gRPC/REST throughput, Drools business-rule evaluation, workflow orchestration) as it happens.

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                      TopHeader                           │
│   Search · Region selector · Settlement volume · UTC     │
├───────────────┬───────────────────────────┬─────────────┤
│  LeftSidebar   │      MainDashboard        │ RightSidebar│
│  ─────────────  │  ───────────────────────  │ ───────────│
│  Cloud logins  │  System health cards      │ Data conn.  │
│  IDE launchers │  KPI metric tiles         │  panel      │
│                │  gRPC/REST inspector      │ (Postgres,  │
│                │  Drools rules engine      │  MySQL,     │
│                │  Event log stream         │  Redis,     │
│                │  Workflow pipeline list   │  Kafka)     │
└───────────────┴───────────────────────────┴─────────────┘
```

Everything is composed as ReactPy `@component` functions rendered server-side and streamed to the client over a persistent connection — state updates (`use_state`) triggered by an `asyncio` loop (`use_effect`) push new data to the browser automatically, no polling required.

### Key components

| Component | Responsibility |
|---|---|
| `TopHeader` | Global nav bar — search, region selector, live settlement volume, UTC clock |
| `LeftSidebar` | Collapsible menu: cloud provider logins + local IDE launch buttons |
| `RightSidebar` | Collapsible menu: data/messaging connection status panels |
| `MainDashboard` | Central view — system health, KPIs, protocol inspector, rules engine stats, live log stream, workflow pipeline |
| `DeveloperDashboard` | Root component wiring layout, shared state, and the real-time simulation loop |

### Real-time engine

A background `asyncio` task (started in `use_effect`) ticks every ~2 seconds and refreshes:
- Decision latency (p95), decisions/min, Kafka consumer lag, active workflow count
- gRPC throughput, Drools rule evaluations/sec, rule pass rate
- A rolling event/telemetry log (Python + Java service traces)
- Live settlement volume and UTC clock in the header

### Local tool launching

`launch_ide()` resolves known install paths for PyCharm, IntelliJ, VS Code, and Spyder (with a `PATH` fallback via `shutil.which`), then spawns the executable as a **detached background process** using a dedicated `ThreadPoolExecutor` so the UI thread is never blocked.

---

## Tech stack

- **Backend / UI framework:** [FastAPI](https://fastapi.tiangolo.com/) + [ReactPy](https://reactpy.dev/) (`reactpy.backend.fastapi.configure`)
- **Concurrency:** `asyncio` for the live-update loop, `concurrent.futures.ThreadPoolExecutor` for non-blocking IDE process spawning
- **Static assets:** served via FastAPI's `StaticFiles` from `/static`
- **Styling:** inline CSS-in-Python (no separate CSS build), custom "navy" dark theme

---

## Getting started

### Requirements
```bash
pip install fastapi reactpy uvicorn
```

### Project structure
```
.
├── main.py          # this file — app, components, and server config
└── static/
    ├── Barclays.png
    ├── IBM.jpg
    ├── Oracle.jpg
    └── aws.jpg
```
Place your logo/icon assets in `static/` (the app auto-creates this folder if missing).

### Run the app
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```
Then open **http://localhost:8000**.

---

## Configuration notes

- **IDE launch paths** are currently hard-coded for common Windows install locations (`fast_paths` dict in `launch_ide`). Update these paths — or extend the `PATH`-based fallback — to match your environment (macOS/Linux users should rely on the `shutil.which` fallback or add platform-specific paths).
- **Cloud login links** (IBM, Oracle, AWS) open in a new tab and simply deep-link to each provider's login page — no credentials are handled by this app.
- **Telemetry values** are currently simulated with `random` for demo purposes. Swap the `update_metrics_loop` internals for real metric sources (Prometheus, a message bus, a DB query, etc.) to go from demo to production.

---

## Extending this dashboard

- Replace the simulated metrics in `MainDashboard.update_metrics_loop` with real observability data.
- Add more entries to `fast_paths` / `fallback_names` in `launch_ide()` to support additional editors.
- Add new data sources to the `data_sources` list in `RightSidebar` to surface more backend systems.
- Wrap `DeveloperDashboard` with auth/session middleware before exposing outside a trusted network — this app currently has no authentication layer.

---

## License

Internal tooling template — adapt licensing as appropriate for your organization.
