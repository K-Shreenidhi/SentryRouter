# SentryRouter — /brag plan

**What it is:** A self-built gateway that sits in front of your LLM providers and keeps requests flowing when one fails, floods, or repeats.
**For:** Teams moving LLM calls from prototype to production traffic.
**Sets it apart:** Every primitive (rate limiter, circuit breaker, singleflight) is hand-built and proven by a concurrency test, not borrowed from a library.
**Most impressive claim:** Provider dies mid-traffic → breaker opens → every request still answered by provider-b.
**Visual hook:** A single provider box turning red and the request stream dying with 503s.
**Real material used:** provider names (`provider-a`, `provider-b`), breaker states (CLOSED/OPEN), the 10-token bucket, test PASS lines, and Locust CSV numbers in `loadtest_results/`.
**Tone:** `default` — punchy, clean, dark infra aesthetic (terminal green / signal amber / fault red).
**Share caption:** see `share-copy.txt`.

## Numbers (from `loadtest_results/*.csv`, not the README)
- Sustained: 3,694 requests, 0 failures, P50 3 ms, P99 14 ms (mock providers)
- Overload: 17,858 requests, 11,429 rate-limited (64%), P99 12 ms

## Storyboard — 23 s, 1920×1080, 30 fps, 120 BPM (bar = 2 s)
| # | Time | Scene | On screen |
|---|---|---|---|
| 1 | 0–3 | Hook | Requests stream into one provider; it flashes red, 503s pile up. "One LLM provider. One point of failure." |
| 2 | 3–6.5 | Reveal | Wordmark **SentryRouter** + "A multi-provider LLM gateway, built from scratch." Diagram: App → SentryRouter → provider-a / provider-b |
| 3 | 6.5–10.5 | Failover | provider-a fails, breaker CLOSED → OPEN, traffic swings to provider-b. Terminal: `PASSED: failover held` |
| 4 | 10.5–14.5 | Rate limit | 50 concurrent requests hit a 10-token bucket: 10 × 200, 40 × 429. "Atomic Redis Lua. No race." |
| 5 | 14.5–17 | Singleflight | 20 identical requests collapse into 1 provider call |
| 6 | 17–20.5 | Proof | 3,694 requests · 0 failures · P99 14 ms / Overload 17,858 req · P99 12 ms |
| 7 | 20.5–23 | Outro | Wordmark + github.com/K-Shreenidhi/SentryRouter |

## Sound
A-minor, 120 BPM, synthesized. Hook: low pad + muffled pulse (tension). Drop on the reveal at 3 s: kick, bass, pluck arpeggio. SFX in key: soft whoosh into each scene, fault thud on breaker OPEN, quiet pentatonic ticks for 200s, muted lower ticks for 429s. Fade out over the last bar.
