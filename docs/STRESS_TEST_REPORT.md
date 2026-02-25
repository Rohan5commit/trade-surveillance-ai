# Stress Test Report

Date: 2026-02-25
Run completed (UTC): 2026-02-25T04:18:49Z
Environment: local uvicorn (`DEMO_MODE=true`, `REQUIRE_API_KEY=false`)
Tool: Locust 2.32.2 (`scripts/load/locustfile.py`)

## Scenarios

1. `s1` burst: 50 users for 1 minute
2. `s2` burst: 150 users for 1 minute
3. `s3` burst: 300 users for 1 minute
4. `soak`: 150 users for 2 minutes

## Results

| Scenario | Requests | Failures | RPS | p50 (ms) | p95 (ms) | p99 (ms) | Avg (ms) | Max (ms) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| s1 | 21,218 | 0 | 359.44 | 99 | 210 | 250 | 103.78 | 394.98 |
| s2 | 13,280 | 0 | 224.49 | 450 | 1,100 | 1,300 | 596.21 | 1,670.76 |
| s3 | 10,348 | 0 | 171.82 | 1,100 | 3,100 | 3,300 | 1,550.73 | 3,494.82 |
| soak | 17,405 | 0 | 144.60 | 770 | 1,600 | 1,800 | 972.21 | 2,944.81 |

## Aggregate

- Total requests: 62,251
- Total failures: 0
- Error rate: 0.00%
- Note: load harness defaults to `SURVEILLANCE_BOOTSTRAP_AUTH=0` in demo mode to avoid auth bootstrap contention and measure event/alert throughput directly.

## Artifacts

- `artifacts/load/s1_stats.csv`
- `artifacts/load/s2_stats.csv`
- `artifacts/load/s3_stats.csv`
- `artifacts/load/soak_stats.csv`
- `artifacts/load/summary.json`
