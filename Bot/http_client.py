import json

import aiohttp

from fastapi import HTTPException


from sqlalchemy.exc import IntegrityError
from starlette import status







async def check_imei(imei: str, service_id: int, api_key: str):
    headers = {'Authorization': f'Bearer {api_key}',
               'Content-Type': 'application/json'
               }
    async with aiohttp.ClientSession() as session:
        async with session.post("https://api.imeicheck.net/v1/checks", headers=headers, data=json.dumps({
            "deviceId": imei,
            "serviceId": service_id
        })) as response:
            result = await response.json()
            if response.status == 201:
                return result
            elif response.status == 422:
                print(f"Status: {response.status}, details: {result}")
                return str(result["errors"]["deviceId"])[2:-2] #возращаем пояснение об ошибке юзеру обрезая [" и "] по бокам
            else:
                print(f"Status: {response.status}, details: {result}")
                return result["message"]



async def get_services(api_key: str):
    headers = {'Authorization': f'Bearer {api_key}',
               'Content-Type': 'application/json'
               }
    async with aiohttp.ClientSession() as session:
        async with session.get(f"https://api.imeicheck.net/v1/services", headers=headers,
                               ) as response:
            result = await response.json()
            if response.status == 200:
                return result
            else:
                return f"Status: {response.status}, details: {result}"


async def get_info(api_key: str, service_id: int):
    headers = {'Authorization': f'Bearer {api_key}',
               'Content-Type': 'application/json'
               }
    async with aiohttp.ClientSession() as session:
        async with session.get(f"https://api.imeicheck.net/v1/services/{service_id}",
                               headers=headers) as response:
            result = await response.json()
            if response.status == 200:
                return result
            else:
                print(f"Status: {response.status}, details: {result}")
                raise ValueError("Such service doesn't exist")


