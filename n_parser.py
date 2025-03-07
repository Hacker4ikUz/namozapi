import aiohttp
from bs4 import BeautifulSoup
import json
import asyncio
import random

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://islom.uz/"
}

class NamozParser:
    def __init__(self):
        self.session = None

    async def init_session(self):
        if not self.session:
            self.session = aiohttp.ClientSession(
                connector=aiohttp.TCPConnector(limit=5),
                timeout=aiohttp.ClientTimeout(total=30)
            )

    async def close_session(self):
        if self.session:
            await self.session.close()
            self.session = None

    async def namoz_vaqti(self, region_id: int):
        await self.init_session()
        url = f"https://islom.uz/region/{region_id}"

        for _ in range(3):
            try:
                async with self.session.get(url, headers=HEADERS) as resp:
                    if resp.status != 200:
                        await asyncio.sleep(random.uniform(1, 3))
                        continue

                    html = await resp.text()
                    soup = BeautifulSoup(html, "lxml")

                    def get_date(class_name):
                        tag = soup.find('div', class_=class_name)
                        return tag.text.strip() if tag else "N/A"

                    def safe_find(id):
                        tag = soup.find('div', id=id)
                        return tag.text.strip() if tag else "N/A"

                    return json.dumps({
                        "date": get_date("date_time"),
                        "bomdod": safe_find("tc1"),
                        "quyosh": safe_find("tc2"),
                        "peshin": safe_find("tc3"),
                        "asr": safe_find("tc4"),
                        "shom": safe_find("tc5"),
                        "xufton": safe_find("tc6"),
                        "developer": "@Haker4ik"
                    }, ensure_ascii=False, indent=4)

            except (aiohttp.ClientError, asyncio.TimeoutError):
                await asyncio.sleep(random.uniform(2, 5))

        return json.dumps({"error": "Failed to fetch prayer times"}, ensure_ascii=False, indent=4)
    

    async def all_regions(self):
        await self.init_session()
        url = "https://islom.uz/region/1"

        for _ in range(3):
            try:
                async with self.session.get(url, headers=HEADERS) as resp:
                    if resp.status != 200:
                        await asyncio.sleep(random.uniform(1, 3))
                        continue

                    html = await resp.text()
                    soup = BeautifulSoup(html, "lxml")

                    regions = soup.find('div', class_="custom-select")
                    if not regions:
                        return json.dumps({"error": "Failed to parse regions"}, ensure_ascii=False)

                    region_data = {}
                    for idx, option in enumerate(regions.find('select').find_all('option'), start=1):
                        region_data[idx] = {
                            "region_name": option.text.strip(),
                            "region_id": int(option['value'])
                        }

                    return json.dumps(region_data, ensure_ascii=False, indent=4)

            except (aiohttp.ClientError, asyncio.TimeoutError):
                await asyncio.sleep(random.uniform(2, 5))

        return json.dumps({"error": "Failed to fetch regions"}, ensure_ascii=False, indent=4)


namoz_parser = NamozParser()
