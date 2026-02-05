import asyncio
import aiohttp
import time

API_URL = "http://localhost:8000/details-final/company-details?name=삼성전자"
CONCURRENCY = 10  # 동시에 요청할 클라이언트 수

async def fetch(session, idx):
    start = time.monotonic()
    async with session.get(API_URL) as resp:
        await resp.text()  # 내용을 읽음으로써 응답 완료
        duration = time.monotonic() - start
        print(f"{idx}: {duration:.3f}s")
        return duration

async def run_test():
    async with aiohttp.ClientSession() as session:
        tasks = [fetch(session, i) for i in range(CONCURRENCY)]
        durations = await asyncio.gather(*tasks)
        print(f"AVG: {sum(durations) / len(durations):.3f}s")

if __name__ == "__main__":
    asyncio.run(run_test())
