import asyncio
import httpx

BASE = "http://127.0.0.1:8001"
PAYLOAD = {"messages": [{"role": "user", "content": "hello"}]}
HEADERS = {"x-api-key": "chaos-test-client"}

async def main():
    async with httpx.AsyncClient(timeout=10.0) as client:
        await client.post(f"{BASE}/debug/provider-a/fail?fail=true")
        await client.post(f"{BASE}/debug/provider-b/fail?fail=false")

        results = []
        for _ in range(6):
            resp = await client.post(f"{BASE}/v1/chat/completions", json=PAYLOAD, headers=HEADERS)
            results.append(resp.json().get("provider"))

        assert all(p == "provider-b" for p in results[1:]), (
            f"Expected failover to provider-b after the first attempt, got {results}"
        )
        print(f"PASSED: failover held. Providers used: {results}")

        breaker_state = await client.get(f"{BASE}/debug/breaker-states")
        assert breaker_state.json()["provider-a"] == "open"
        print("PASSED: provider-a breaker correctly opened")

        # cleanup
        await client.post(f"{BASE}/debug/provider-a/fail?fail=false")

if __name__ == "__main__":
    asyncio.run(main())