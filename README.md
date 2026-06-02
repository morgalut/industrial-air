Create:

````md
# README.md

# Industrial Air — Data Ingestion Library & Metrics API

This project solves **Challenge 1 — Data Ingestion Library & Metrics Service**.

The system is split into two clean parts:

1. **`air_ingestion/`** — reusable Python library  
2. **`metrics_api/`** — FastAPI service that uses the library

The important design rule is:

> The library does the heavy lifting.  
> The API is only a thin HTTP wrapper.

---

## Project Structure

```text
industrial-air/
├── requirements.txt
├── README.md
├── pyproject.toml
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
````

---

## What This Project Does

The project processes industrial compressor sensor data.

The raw data comes from SQLite:

```text
data/sensor_data.db
```

The expected schema comes from:

```text
data/sensor_schema.json
```

The data may contain:

* missing values
* malformed values
* sensor gaps
* flatline readings
* out-of-range values
* noisy time-series readings

The ingestion library cleans this data and returns:

* cleaned sensor data
* missing-value percentages
* out-of-range counts
* flatline detection results
* row counts before and after processing

The API then computes operational metrics.

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
   ├── missing value handling
   ├── flatline detection
   ├── out-of-range detection
   └── resampling
   │
   ▼
Clean DataFrame
   │
   ▼
Metrics Calculator
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

---

## Why This Structure Is Good

The project uses the **Repository Pattern**.

The ingestion engine does not know whether data comes from:

* SQLite
* PostgreSQL
* BigQuery
* CSV
* API
* data warehouse

It only depends on this interface:

```python
class AbstractSensorRepository:
    def fetch_station_data(self, station_id: str) -> pd.DataFrame:
        ...
```

So later, a production repository can be added without changing the processing engine.

Example:

```text
SQLiteSensorRepository today
BigQuerySensorRepository later
```

The API code does not need to change.

---

## Install

Create virtual environment:

```bash
python -m venv .venv
```

Activate it:

```bash
source .venv/bin/activate
```

Install dependencies:

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

---

## Required Files

Make sure these files exist:

```text
data/sensor_data.db
data/sensor_schema.json
```

Check:

```bash
ls -la data
```

Expected:

```text
sensor_data.db
sensor_schema.json
```

---

## Run Syntax Check

```bash
python -m py_compile air_ingestion/models.py
python -m py_compile air_ingestion/repository.py
python -m py_compile air_ingestion/schema.py
python -m py_compile air_ingestion/quality.py
python -m py_compile air_ingestion/engine.py

python -m py_compile metrics_api/calculator.py
python -m py_compile metrics_api/storage.py
python -m py_compile metrics_api/deps.py
python -m py_compile metrics_api/schemas.py
python -m py_compile metrics_api/main.py
```

Or all together:

```bash
python -m compileall air_ingestion metrics_api
```

---

## Run the API

Start FastAPI:

```bash
uvicorn metrics_api.main:app --reload
```

Open docs:

```text
http://127.0.0.1:8000/docs
```

Health check:

```bash
curl http://127.0.0.1:8000/health
```

Expected:

```json
{"status":"healthy"}
```

---

## Process a Station

Example:

```bash
curl -X POST "http://127.0.0.1:8000/api/v1/stations/STATION_001/process" \
  -H "Content-Type: application/json" \
  -d '{
    "frequency": "5min",
    "missing_strategy": "interpolate",
    "fill_value": 0,
    "flatline_window": 5
  }'
```

This endpoint:

1. reads raw station data
2. validates columns
3. detects missing values
4. detects out-of-range values
5. detects flatlines
6. cleans malformed values
7. resamples the time series
8. computes metrics
9. stores the result in memory
10. returns metrics and quality report

---

## Get Stored Metrics

```bash
curl "http://127.0.0.1:8000/api/v1/stations/STATION_001/metrics"
```

---

## Metric Definitions

### 1. Uptime Percent

A device is active when:

```text
rpm > 100 and power_kw > 0
```

Formula:

```text
active rows / total rows * 100
```

---

### 2. Average Pressure

Average compressor pressure:

```text
mean(pressure_bar)
```

---

### 3. Peak Pressure

Maximum pressure in the selected time period:

```text
max(pressure_bar)
```

---

### 4. Specific Power

Energy efficiency metric:

```text
sum(power_kw) / sum(flow_m3h)
```

Only active rows are used.

This shows how much power is required per unit of air flow.

---

### 5. Cycle Count

Counts how many times a device transitions from off to on.

The active state is:

```text
rpm > 100 and power_kw > 0
```

Transition counted when:

```text
inactive → active
```

---

### 6. Total Flow Volume

Flow rate is stored as:

```text
m3/h
```

To calculate volume:

```text
flow_m3h * time_delta_hours
```

Then sum all intervals.

---

## Run Tests

After tests are created:

```bash
pytest
```

Verbose mode:

```bash
pytest -v
```

Run one test file:

```bash
pytest tests/test_metrics_calculator.py -v
```

Run with print output:

```bash
pytest -s
```

---

## Run Lint

```bash
ruff check .
```

Auto-fix simple lint issues:

```bash
ruff check . --fix
```

Format code:

```bash
ruff format .
```

---

## Run Type Check

```bash
mypy air_ingestion metrics_api
```

---

## Full Local Validation Command

```bash
python -m compileall air_ingestion metrics_api && \
ruff check . && \
mypy air_ingestion metrics_api && \
pytest -v
```

---

## Example Development Flow

```bash
source .venv/bin/activate

python -m compileall air_ingestion metrics_api

uvicorn metrics_api.main:app --reload
```

Then in another terminal:

```bash
curl http://127.0.0.1:8000/health
```

Then process station:

```bash
curl -X POST "http://127.0.0.1:8000/api/v1/stations/STATION_001/process" \
  -H "Content-Type: application/json" \
  -d '{"frequency":"5min","missing_strategy":"interpolate","fill_value":0,"flatline_window":5}'
```

Then read metrics:

```bash
curl "http://127.0.0.1:8000/api/v1/stations/STATION_001/metrics"
```

---

## Testing Strategy

The test suite should be split into three levels.

### Unit Tests

These test pure logic without external files.

Examples:

* missing percentage calculation
* flatline detection
* metric formulas
* cycle count logic
* total flow volume calculation

### Integration Tests

These test interaction with SQLite or schema files.

Examples:

* repository reads expected columns
* ingestion engine loads schema
* engine processes a real station from SQLite

### API Tests

These test HTTP behavior.

Examples:

* health endpoint returns healthy
* process endpoint returns metrics
* metrics endpoint returns stored result
* unknown station returns useful error

---

## Design Document Summary

### 1. Versioning the Library Across 25+ Services

In a monorepo, the shared ingestion library should be versioned as an internal package.

Services should depend on it directly from the repository.

A future production structure may use:

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

A CI pipeline should test every service affected by a library change.

---

### 2. Schema Evolution

Schema changes should be handled by the library, not by every service.

Examples:

```text
pressure_bar renamed to discharge_pressure_bar
flow_m3h changed to flow_lpm
new sensor column added
old sensor column deprecated
```

Recommended strategy:

* keep schema versions
* support aliases
* support unit conversion
* never remove fields immediately
* emit warnings for deprecated fields
* add compatibility tests

---

### 3. CI/CD Pipeline

Recommended pipeline:

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
Run container smoke test
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

That is fine for the first challenge stage.

For production, replace it with:

* SQLite
* PostgreSQL
* TimescaleDB
* BigQuery
* Redis cache
* object storage

The important point is that storage is isolated in:

```text
metrics_api/storage.py
```

So replacing storage does not affect the API route logic.

---

## Current Status

Implemented:

* reusable ingestion library
* repository abstraction
* SQLite repository
* JSON schema loading
* missing data report
* out-of-range detection
* flatline detection
* configurable missing value strategy
* resampling
* FastAPI service
* metrics calculator
* in-memory metrics storage
* health endpoint
* process endpoint
* metrics retrieval endpoint

