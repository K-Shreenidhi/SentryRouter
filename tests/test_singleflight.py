import asyncio
import httpx

URL = "http://127.0.0.1:8001/v1/chat/completions"
PAYLOAD = {"messages": [{"role": "user", "content": "identical prompt"}], "temperature": 0.0}
HEADERS = {"x-api-key": "singleflight-test"}
CONCURRENT = 20

async def fire(client):
    r = await client.post(URL, json=PAYLOAD, headers=HEADERS)
    print("STATUS:", r.status_code)
    print("BODY:", repr(r.text))
    return r.json()

async def main():
    async with httpx.AsyncClient(timeout=10.0) as client:
        results = await asyncio.gather(*[fire(client) for _ in range(CONCURRENT)])
        call_counts = {r.get("call_count") for r in results if "call_count" in r}
        print(f"Distinct call_count values seen: {call_counts}")
        assert len(call_counts) == 1, f"Provider was called more than once: {call_counts}"
        print("PASSED: singleflight collapsed 20 concurrent identical requests into 1 provider call")

if __name__ == "__main__":
    asyncio.run(main())