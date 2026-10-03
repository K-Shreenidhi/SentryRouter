# Sentry Router

**A multi-provider LLM inference gateway, built from scratch to solve the reliability problems every team hits once LLM calls move from a prototype to production traffic.**

Not a wrapper around an existing library. The rate limiter, circuit breaker, and request deduplication logic are hand-built and load-tested - this repo exists to demonstrate that engineering, not to hide it behind a framework.

---

## The problem

Every team running LLMs in production eventually hits the same wall: a single provider becomes a single point of failure. Rate limits get hit under load, latency spikes during provider incidents, and a slow or down provider silently degrades the whole product if nothing in front of it is watching.

Sentry Router sits between your application and your LLM providers (OpenAI, Anthropic, self-hosted, etc.) and handles:

- **Per-client rate limiting** that holds exactly under concurrent load — not approximately
- **Automatic failover** when a provider errors out or hangs, with no client-facing disruption
- **Request deduplication** so concurrent identical calls don't multiply provider cost
- **Safe retries** via idempotency keys, so a dropped connection never double-charges a provider call

---

## Why this is worth looking at

Most "LLM gateway" portfolio projects call `LiteLLM` or a similar library and stop there. This one doesn't — every primitive below was implemented and proven under real concurrent load, not assumed to work because a library says so:

| Claim | Proof |
|---|---|
| Rate limiter has no race condition | Atomic Redis Lua script, verified with 50 truly concurrent requests against a 10-token bucket - exactly 10 pass, every run |
| Failover is transparent to the client | Automated chaos test trips a provider mid-request and asserts zero client-visible errors |
| Dedup actually collapses duplicate calls | 20 concurrent identical requests verified to hit the upstream provider exactly once |
| Gateway overhead is known, not guessed | Load-tested: **P50 3ms / P95 5ms / P99 13ms** gateway-added latency at ~67 req/s sustained, 0 failures across 3,703 requests |
| Rate limiter survives abuse, not just normal traffic | 17,904 requests fired at 2–10x per-client quota — 64% correctly rejected, P99 latency held at 12ms throughout |

Full numbers and methodology: [`loadtest_results/`](./loadtest_results).

---

## Architecture

```
Client
  │
  ▼
FastAPI Gateway  ── auth, idempotency-key check
  │
  ▼
Redis  ── token-bucket rate limiter (atomic Lua), singleflight cache
  │
  ▼
Circuit-Breaker Router  ── CLOSED → OPEN → HALF_OPEN per provider
  │
  ├──▶ Provider A (OpenAI)
  ├──▶ Provider B (Anthropic)
  └──▶ Provider C (self-hosted / local)
  │
  ▼
Postgres  ── async request log, cost & latency tracking
```

Every request is checked for rate limit and cache hit before a provider is ever called. If the selected provider's breaker is `OPEN`, it's skipped - no wasted call to something already known to be down.

---

## Key engineering decisions

Full writeup in [`DESIGN.md`](./DESIGN.md). Highlights:

- **Why a Lua script for rate limiting, not a Python check-then-decrement:** the naive approach has a race window — two concurrent requests can both read "1 token left" before either writes back. The Lua script makes the check-and-decrement atomic inside Redis.
- **Why timeouts count as circuit-breaker failures, not just explicit errors:** a provider that hangs is as harmful as one that returns a 500. `asyncio.wait_for` wraps every provider call so slow failures trip the breaker too.
- **Why singleflight and idempotency keys are separate mechanisms:** idempotency keys handle client-initiated safe retries; singleflight handles server-side collapsing of concurrently arriving, coincidentally identical requests from different callers. Conflating them was a deliberate decision to avoid, not an oversight.
- **Known limitation — streaming (SSE):** mid-stream failover is not supported. Once the first token reaches the client, there's no clean way to retract it and switch providers. Documented in full in `DESIGN.md`, including the tradeoff this implies.

---

## Tech stack

`FastAPI` · `Redis` (rate limiting, caching, locks) · `PostgreSQL` (async audit log) · `Docker Compose` · `Prometheus` + `Grafana` (observability) · `Locust` (load testing) · `GitHub Actions` (CI)

---

## Running it locally

```bash
git clone https://github.com/K-Shreenidhi/SentryRouter.git
cd SentryRouter-
docker compose up -d
pip install -r requirements.txt
uvicorn app.main:app --port 8001
```

Verify it's up:
```bash
curl http://127.0.0.1:8001/health
```

Metrics: `http://127.0.0.1:8001/metrics` · Grafana: `http://localhost:3000` (`admin`/`admin`)

---

## Testing

```bash
python tests/test_rate_limit_concurrency.py   # proves the rate limiter holds under concurrency
python tests/test_singleflight.py             # proves dedup collapses concurrent identical calls
python tests/test_failover_chaos.py           # proves failover is transparent under provider failure
```

All three run in CI on every push — see [`.github/workflows/test.yml`](./.github/workflows/test.yml).




## What this deliberately doesn't include

No auth system beyond a static API key check, no billing UI, no Kubernetes, no more than three providers. The scope is the reliability primitives - rate limiting, failover, dedup - proven under load, not a full commercial product surface.
