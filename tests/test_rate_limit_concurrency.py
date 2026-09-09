import asyncio
import httpx

URL = "http://127.0.0.1:8001/v1/chat/completions"
PAYLOAD = {"messages": [{"role": "user", "content": "hello"}]}
CONCURRENT_REQUESTS = 50

async def fire_one(client: httpx.AsyncClient):
    resp = await client.post(URL, json=PAYLOAD)
    return resp.status_code

async def main():
    async with httpx.AsyncClient() as client:
        results = await asyncio.gather(*[fire_one(client) for _ in range(CONCURRENT_REQUESTS)])

    allowed = sum(1 for code in results if code == 200)
    blocked = sum(1 for code in results if code == 429)
    print(f"Allowed: {allowed}, Blocked: {blocked}, Total: {len(results)}")
    assert allowed <= 10, f"Rate limiter leaked! {allowed} requests got through, expected <= 10"
    print("PASSED: rate limiter held under concurrent load")

if __name__ == "__main__":
    asyncio.run(main())