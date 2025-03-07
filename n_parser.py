import aiohttp
import asyncio
import json
import random
from bs4 import BeautifulSoup
from datetime import datetime, timedelta


HEADERS = {"User-Agent": "Mozilla/5.0"}


class NamozParser:
    def __init__(self):
        self.session = None
        self.last_updated_times = None
        self.cached_times = {}
        self.last_updated_regions = None
        self.cached_regions = {}

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
        today = datetime.now().date()
        
        if self.last_updated_times == today and region_id in self.cached_times:
            return self.cached_times[region_id]

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

                    data = json.dumps({
                        "date": get_date("date_time"),
                        "bomdod": safe_find("tc1"),
                        "quyosh": safe_find("tc2"),
                        "peshin": safe_find("tc3"),
                        "asr": safe_find("tc4"),
                        "shom": safe_find("tc5"),
                        "xufton": safe_find("tc6"),
                        "developer": "@Haker4ik"
                    }, ensure_ascii=False, indent=4)

                    self.cached_times[region_id] = data
                    self.last_updated_times = today
                    return data

            except (aiohttp.ClientError, asyncio.TimeoutError):
                await asyncio.sleep(random.uniform(2, 5))

        return json.dumps({"error": "Failed to fetch prayer times"}, ensure_ascii=False, indent=4)

    async def all_regions(self):
        today = datetime.now().date()

        if self.last_updated_regions == today and self.cached_regions:
            return self.cached_regions

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

                    self.cached_regions = json.dumps(region_data, ensure_ascii=False, indent=4)
                    self.last_updated_regions = today
                    return self.cached_regions

            except (aiohttp.ClientError, asyncio.TimeoutError):
                await asyncio.sleep(random.uniform(2, 5))

        return json.dumps({"error": "Failed to fetch regions"}, ensure_ascii=False, indent=4)


namoz_parser = NamozParser()
