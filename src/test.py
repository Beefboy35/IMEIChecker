import asyncio

import aiohttp

from src.config import settings
async def my_func():
    url = "http://localhost:8000/imei/check_imei"
    headers = {"Authorization": f"Bearer {settings.LIVE_API_KEY}"}
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as resp:
            return await resp.json()

print(asyncio.run(my_func()))