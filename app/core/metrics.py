from prometheus_client import Counter, Histogram, Gauge

REQUEST_COUNT = Counter(
    "sentry_requests_total", "Total requests", ["status"]
)
REQUEST_LATENCY = Histogram(
    "sentry_request_latency_seconds", "Request latency"
)
RATE_LIMIT_REJECTIONS = Counter(
    "sentry_rate_limit_rejections_total", "Requests rejected by rate limiter"
)
CACHE_HITS = Counter("sentry_cache_hits_total", "Singleflight/idempotency cache hits")
CACHE_MISSES = Counter("sentry_cache_misses_total", "Cache misses (actual provider calls)")
BREAKER_STATE = Gauge(
    "sentry_breaker_state", "0=closed, 1=half_open, 2=open", ["provider"]
)