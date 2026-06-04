# Industrial Air — Data Ingestion Library & Metrics API

A production-grade system for processing industrial compressor sensor data.

Split into two clean layers:

- **`air_ingestion/`** — reusable Python library for ingestion, validation, and quality analysis
- **`metrics_api/`** — FastAPI service that exposes the library over HTTP

> **Design rule:** The library does the heavy lifting. The API is only a thin HTTP wrapper.

---

## Table of Contents

1. [Project Structure](#project-structure)
2. [What This Project Does](#what-this-project-does)
3. [Main Architecture](#main-architecture)
4. [Challenge 2 — LLM Powered Features](#challenge-2--llm-powered-features)
5. [Assumptions](#assumptions)
6. [Tradeoffs & Design Decisions](#tradeoffs--design-decisions)
7. [Environment Variables](#environment-variables)
8. [Observability](#observability)
9. [Install](#install)
10. [Run the API](#run-the-api)
11. [Step-by-Step: Full Workflow with curl](#step-by-step-full-workflow-with-curl)
12. [Metric Definitions](#metric-definitions)
13. [Testing Strategy](#testing-strategy)
14. [Run Tests, Lint & Type Check](#run-tests-lint--type-check)
15. [Design Document Summary](#design-document-summary)
16. [Current Status](#current-status)
---
## Project Structure

```text
industrial-air/
├── requirements.txt
├── README.md
├── pyproject.toml
├── .env.example
├── data/
│   ├── sensor_data.db
│   └── sensor_schema.json
├── air_ingestion/
│   ├── engine.py
│   ├── models.py
│   ├── repository.py
│   ├── schema.py
│   └── quality.py
├── metrics_api/
│   ├── main.py
│   ├── deps.py
│   ├── calculator.py
│   ├── storage.py
│   └── schemas.py
├── tests/
└── docs/
    └── design.md
```

---

## What This Project Does

The project processes industrial compressor sensor data.

Raw data source:

```text
data/sensor_data.db       ← SQLite database with sensor readings
data/sensor_schema.json   ← expected column definitions and ranges
```

The raw data may contain:

- missing values
- malformed values
- sensor gaps
- flatline readings
- out-of-range values
- noisy time-series readings

The ingestion library cleans this data and returns:

- cleaned sensor DataFrame
- missing-value percentages per column
- out-of-range counts per column
- flatline detection results
- row counts before and after processing

The API then computes operational metrics and (optionally) generates LLM-powered summaries.

---

## Main Architecture

```text
SQLite DB
   │
   ▼
SQLiteSensorRepository
   │
   ▼
IngestionEngine
   │
   ├── schema validation
   ├── missing value handling  (interpolate / fill / drop)
   ├── flatline detection
   ├── out-of-range detection
   └── resampling
   │
   ▼
Clean DataFrame
   │
   ▼
MetricsCalculator
   │
   ├── uptime percent
   ├── average pressure
   ├── peak pressure
   ├── specific power
   ├── cycle count
   └── total flow volume
   │
   ▼
FastAPI Response
```

### Why Repository Pattern?

The ingestion engine does not know whether data comes from SQLite, PostgreSQL, BigQuery, CSV, or an API.

It depends only on this interface:

```python
class AbstractSensorRepository:
    def fetch_station_data(self, station_id: str) -> pd.DataFrame:
        ...
```

This means:

```text
SQLiteSensorRepository   ← used today
BigQuerySensorRepository ← can be added later
```

The API and engine code do not need to change.

---

## Challenge 2 — LLM Powered Features

The service includes optional LLM-powered endpoints for plain-English operational intelligence.

### Station Health Summary

```text
GET /api/v1/stations/{station_id}/summary
```

Produces a plain-English operational summary. Example output:

```text
Station uptime remained above 90% during the selected period.
Discharge pressure remained stable between 7.2 and 8.1 bar.
Specific power indicates efficient operation at 0.12 kW/(m³/h).
```

### Data Quality Summary

```text
GET /api/v1/stations/{station_id}/quality-summary
```

Produces a plain-English explanation of:

- missing values and affected columns
- out-of-range sensor readings
- flatline detection results
- overall data reliability assessment

### LLM Provider Abstraction

The API does not depend directly on OpenAI. Instead:

```text
AbstractLLMProvider
        │
        ▼
OpenAILLMProvider
```

This allows future support for:

- Anthropic Claude
- Google Gemini
- Ollama (local)
- Azure OpenAI

without changing business logic.

### Retry Strategy

LLM requests use exponential backoff with a configurable timeout.

If the provider fails:

```text
503 Service Unavailable
```

is returned to the caller.

### LLM Testing Strategy

The LLM is treated as a black box in tests.

Tests use:

```python
MockLLMProvider
```

instead of making real API calls. This keeps tests deterministic, fast, and inexpensive.

---

## Assumptions

The challenge description does not fully define several operational behaviors.
The following assumptions were made:

### Station Existence

A station is considered invalid if no sensor records exist for it.

```text
No sensor data found
        ↓
  404 Not Found
```

### Device Active State

A compressor is considered **active** when:

```text
rpm > 100
AND
power_kw > 0
```

This threshold is used for:

- uptime calculation
- cycle counting
- specific power calculation

### Missing Values

Default strategy: **interpolate**

Dropping rows would remove too much operational data. Filling with zeros may introduce artificial shutdown periods. Interpolation preserves continuity for time-series metrics.

### Flatline Detection

Repeated zero values are **not** considered flatlines.

```text
rpm = 0, flow = 0, power = 0
```

may indicate a legitimate device shutdown, not a sensor malfunction.

### Metrics Storage

Current implementation stores results in memory:

```python
_METRICS_STORE = {}
```

This was chosen to keep the implementation simple and focused on architecture correctness.
A production implementation would replace this with a persistent store.

---

## Tradeoffs & Design Decisions

### Why Pandas Instead of Polars?

Pandas was selected because:

- mature ecosystem with wide adoption
- strong time-series resampling support
- well understood by data engineers

Polars may provide better performance for very large datasets, but the trade-off in ecosystem maturity and team familiarity favored Pandas here.

### Why In-Memory Storage?

| Pros | Cons |
|---|---|
| Simple, no extra infrastructure | Data lost on restart |
| Easy to implement and test | Not horizontally scalable |
| Fast reads | Not suitable for production |

A production implementation would use **PostgreSQL** or **TimescaleDB** with the same `storage.py` interface — no API route changes needed.

### Why Repository Pattern?

| Pros | Cons |
|---|---|
| Storage backend can change freely | Slight additional abstraction |
| Ingestion engine stays unchanged | Extra interface layer to maintain |
| Easier to unit test with mocks | |

The flexibility outweighs the added complexity for a multi-service architecture.

### Why FastAPI?

| FastAPI | Flask |
|---|---|
| OpenAPI docs auto-generated | Manual documentation |
| Pydantic validation built-in | Manual validation |
| Async support | Limited async |
| Dependency injection | Manual wiring |

FastAPI was selected for stronger typing, validation, and developer experience.

---

## Environment Variables

Copy the example file:

```bash
cp .env.example .env
```

Then fill in your values:

```env
# Required for Challenge 1
# (no additional keys needed beyond what's in the repo)

# Required for Challenge 2 — LLM features
OPENAI_API_KEY=sk-...

# Optional — defaults to gpt-4o-mini
OPENAI_MODEL=gpt-4o-mini

# Required for LangSmith observability
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=ls-...
LANGSMITH_PROJECT=industrial-air-metrics
```

---

## Observability

### LangSmith Tracing

Challenge 2 integrates LangSmith tracing for all LLM interactions.

Traced components:

- LLM requests and responses
- Station health summary generation
- Data quality report generation

Benefits:

- Full prompt visibility
- Latency analysis per call
- Debugging failed or degraded summaries
- Prompt evaluation and regression testing

To enable, set in `.env`:

```env
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=ls-...
LANGSMITH_PROJECT=industrial-air-metrics
```

---

## Install

**Step 1 — Create virtual environment:**

```bash
python -m venv .venv
```

**Step 2 — Activate it:**

```bash
# macOS / Linux
source .venv/bin/activate

# Windows
.venv\Scripts\activate
```

**Step 3 — Install dependencies:**

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

**Step 4 — Verify data files exist:**

```bash
ls -la data/
```

Expected:

```text
sensor_data.db
sensor_schema.json
```

**Step 5 — Set up environment variables:**

```bash
cp .env.example .env
# Edit .env and fill in your API keys
```

---

## Run the API

Start the server:

```bash
uvicorn metrics_api.main:app --reload
```

Open interactive API docs:

```text
http://127.0.0.1:8000/docs
```

---

## Step-by-Step: Full Workflow with curl

This section walks through the complete lifecycle of processing a station and reading its results.

---

### Step 1 — Health Check

Verify the API is running before doing anything else.

```bash
curl http://127.0.0.1:8000/health
```

Expected response:

```json
{"status": "healthy"}
```

If this fails, check that `uvicorn` is running and the port is correct.

---

### Step 2 — Process a Station

This is the main operation. It reads raw sensor data, cleans it, computes metrics, and stores the result.

```bash
curl -X POST "http://127.0.0.1:8000/api/v1/stations/63e5b8d0-99c5-5791-bd7e-f6bcc0349683/process" \
  -H "Content-Type: application/json" \
  -d '{
    "frequency": "5min",
    "missing_strategy": "interpolate",
    "fill_value": 0,
    "flatline_window": 5
  }'
```

**What happens internally:**

```text
1. Read raw rows from SQLite for station_id
2. Validate columns against sensor_schema.json
3. Detect and report missing values per column
4. Detect out-of-range values per column
5. Detect flatlines (repeated non-zero values)
6. Apply missing value strategy (interpolate / fill / drop)
7. Resample time series to requested frequency (5min)
8. Compute all operational metrics
9. Store result in _METRICS_STORE[station_id]
10. Return metrics + quality report in response
```

**Request parameters:**

| Parameter | Type | Description |
|---|---|---|
| `frequency` | string | Resample interval. Examples: `"1min"`, `"5min"`, `"1h"` |
| `missing_strategy` | string | How to handle gaps: `"interpolate"`, `"fill"`, `"drop"` |
| `fill_value` | number | Used when `missing_strategy` is `"fill"` |
| `flatline_window` | integer | Number of consecutive identical readings to flag as flatline |

**Example response:**

```json
{
  "station_id": "63e5b8d0-99c5-5791-bd7e-f6bcc0349683",
  "metrics": {
    "uptime_percent": 91.4,
    "average_pressure_bar": 7.83,
    "peak_pressure_bar": 8.21,
    "specific_power_kw_per_m3h": 0.118,
    "cycle_count": 3,
    "total_flow_volume_m3": 1240.5
  },
  "quality_report": {
    "rows_before": 8640,
    "rows_after": 8640,
    "missing_percent": {
      "rpm": 0.2,
      "pressure_bar": 0.0,
      "power_kw": 0.1,
      "flow_m3h": 0.3
    },
    "out_of_range_counts": {
      "pressure_bar": 2,
      "rpm": 0
    },
    "flatline_flags": {
      "pressure_bar": false,
      "rpm": false
    }
  }
}
```

---

### Step 3 — Retrieve Stored Metrics

After processing, retrieve the stored metrics without re-running the full pipeline.

```bash
curl "http://127.0.0.1:8000/api/v1/stations/63e5b8d0-99c5-5791-bd7e-f6bcc0349683/metrics"
```

Returns the same metrics object as stored from the last `/process` call.

If the station has never been processed:

```json
{"detail": "No metrics found for station 63e5b8d0-99c5-5791-bd7e-f6bcc0349683"}
```

---

### Step 4 — Get LLM Health Summary (Challenge 2)

Requires `OPENAI_API_KEY` to be set in `.env`.

```bash
curl "http://127.0.0.1:8000/api/v1/stations/63e5b8d0-99c5-5791-bd7e-f6bcc0349683/summary"
```

Example response:

```json
{
  "station_id": "63e5b8d0-99c5-5791-bd7e-f6bcc0349683",
  "summary": "Station uptime remained above 90% during the selected period. Discharge pressure was stable between 7.2 and 8.2 bar with no anomalies detected. Specific power indicates efficient operation. Three compressor cycles were recorded."
}
```

---

### Step 5 — Get LLM Data Quality Summary (Challenge 2)

```bash
curl "http://127.0.0.1:8000/api/v1/stations/63e5b8d0-99c5-5791-bd7e-f6bcc0349683/quality-summary"
```

Example response:

```json
{
  "station_id": "63e5b8d0-99c5-5791-bd7e-f6bcc0349683",
  "quality_summary": "Data quality is generally good. Flow and RPM columns had minor gaps under 0.5% which were resolved by interpolation. Two out-of-range pressure readings were detected and flagged but did not affect overall metrics significantly. No flatlines were detected."
}
```

---

### Full Sequence (copy-paste ready)

```bash
# 1. Health check
curl http://127.0.0.1:8000/health

# 2. Process station
curl -X POST "http://127.0.0.1:8000/api/v1/stations/63e5b8d0-99c5-5791-bd7e-f6bcc0349683/process" \
  -H "Content-Type: application/json" \
  -d '{"frequency":"5min","missing_strategy":"interpolate","fill_value":0,"flatline_window":5}'

# 3. Get stored metrics
curl "http://127.0.0.1:8000/api/v1/stations/63e5b8d0-99c5-5791-bd7e-f6bcc0349683/metrics"

# 4. Get LLM health summary
curl "http://127.0.0.1:8000/api/v1/stations/63e5b8d0-99c5-5791-bd7e-f6bcc0349683/summary"

# 5. Get LLM quality summary
curl "http://127.0.0.1:8000/api/v1/stations/63e5b8d0-99c5-5791-bd7e-f6bcc0349683/quality-summary"
```

---

## Metric Definitions

### 1. Uptime Percent

Measures what percentage of time the compressor was actively running.

Active state definition:

```text
rpm > 100 AND power_kw > 0
```

Formula:

```text
uptime_percent = (active_rows / total_rows) * 100
```

---

### 2. Average Pressure

Mean compressor discharge pressure across the time window:

```text
average_pressure_bar = mean(pressure_bar)
```

---

### 3. Peak Pressure

Maximum pressure recorded in the selected time period:

```text
peak_pressure_bar = max(pressure_bar)
```

---

### 4. Specific Power

Energy efficiency metric — how much power is needed per unit of air delivered:

```text
specific_power = sum(power_kw) / sum(flow_m3h)
```

Only active rows (rpm > 100 and power_kw > 0) are included.

Lower values indicate more efficient operation.

---

### 5. Cycle Count

Counts how many times the compressor transitions from off to on.

```text
inactive (rpm ≤ 100 OR power_kw = 0)
           ↓
        active (rpm > 100 AND power_kw > 0)
           ↑
     counts as 1 cycle
```

---

### 6. Total Flow Volume

Flow rate is stored in m³/h. Volume is calculated by integrating over time:

```text
volume = flow_m3h × time_delta_hours
```

Then summed across all intervals:

```text
total_flow_volume_m3 = sum(flow_m3h[i] × Δt[i])
```

---

## Testing Strategy

Tests are split into three levels.

### Unit Tests

Pure logic, no external files or databases.

Examples:

- missing percentage calculation
- flatline detection logic
- metric formula correctness
- cycle count transitions
- total flow volume integration

### Integration Tests

Test interaction with SQLite and schema files.

Examples:

- repository reads expected columns
- ingestion engine loads schema from JSON
- engine processes a real station from SQLite
- out-of-range detection against schema bounds

### API Tests

Test HTTP behavior end-to-end.

Examples:

- health endpoint returns `{"status": "healthy"}`
- process endpoint returns metrics and quality report
- metrics endpoint returns stored result after processing
- unknown station returns 404
- invalid request body returns 422

---

## Run Tests, Lint & Type Check

**Syntax check only:**

```bash
python -m compileall air_ingestion metrics_api
```

**Run tests:**

```bash
pytest
pytest -v                                       # verbose
pytest tests/test_metrics_calculator.py -v     # single file
pytest -s                                       # show print output
```

**Lint:**

```bash
ruff check .
ruff check . --fix     # auto-fix simple issues
ruff format .          # format code
```

**Type check:**

```bash
mypy air_ingestion metrics_api
```

**Full local validation (run before every commit):**

```bash
python -m compileall air_ingestion metrics_api && \
ruff check . && \
mypy air_ingestion metrics_api && \
pytest -v
```

---

## Design Document Summary

### 1. Versioning the Library Across 25+ Services

In a monorepo, the shared ingestion library should be versioned as an internal package.

Recommended structure:

```text
libs/air_ingestion
services/metrics_api
services/service_a
services/service_b
```

Each service imports:

```python
from air_ingestion.engine import IngestionEngine
```

A CI pipeline should run tests for every service affected by a library change.

---

### 2. Schema Evolution

Schema changes should be handled in the library, not in every consuming service.

Recommended strategy:

- keep versioned schema definitions
- support column aliases (e.g. `pressure_bar` → `discharge_pressure_bar`)
- support unit conversion
- never remove fields immediately — deprecate with warnings first
- add backward-compatibility tests for each schema version

---

### 3. CI/CD Pipeline

```text
Install dependencies
      │
      ▼
Ruff lint
      │
      ▼
Ruff format check
      │
      ▼
Mypy type check
      │
      ▼
Pytest unit tests
      │
      ▼
Pytest integration tests
      │
      ▼
Build Docker image
      │
      ▼
Container smoke test
      │
      ▼
Deploy
```

---

## Important Notes

Current storage is in-memory:

```python
_METRICS_STORE = {}
```

This is acceptable for the challenge. For production, replace with:

- PostgreSQL
- TimescaleDB
- Redis cache
- BigQuery

Storage is isolated in `metrics_api/storage.py`, so replacing it does not affect route logic.

---

## Current Status

Implemented:

- reusable ingestion library (`air_ingestion/`)
- repository abstraction (`AbstractSensorRepository`)
- SQLite repository implementation
- JSON schema loading and validation
- missing data detection and reporting
- out-of-range detection
- flatline detection
- configurable missing value strategy (interpolate / fill / drop)
- configurable resampling
- FastAPI service (`metrics_api/`)
- metrics calculator (uptime, pressure, specific power, cycles, flow volume)
- in-memory metrics storage
- health endpoint
- process endpoint
- metrics retrieval endpoint
- LLM health summary endpoint (Challenge 2)
- LLM quality summary endpoint (Challenge 2)
- LLM provider abstraction
- LangSmith observability integration