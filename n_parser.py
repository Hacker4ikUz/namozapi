import aiohttp
from bs4 import BeautifulSoup
import json
import asyncio


async def all_regions():
    url = "https://islom.uz/region/1"
    headers = {"User-Agent": "Mozilla/5.0"}

    for _ in range(3):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, timeout=10) as resp:
                    if resp.status != 200:
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

        except aiohttp.ClientError:
            await asyncio.sleep(2)

    return json.dumps({"error": "Failed to fetch regions"}, ensure_ascii=False, indent=4)


async def namoz_vaqti(region_id: int):
    url = f"https://islom.uz/region/{region_id}"
    headers = {"User-Agent": "Mozilla/5.0"}
    
    for _ in range(3):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, timeout=10) as resp:
                    if resp.status != 200:
                        continue

                    html = await resp.text()
                    soup = BeautifulSoup(html, "lxml")

                    def safe_find(id):
                        tag = soup.find('div', id=id)
                        return tag.text.strip() if tag else "N/A"

                    times = {
                        "date": safe_find("date_time"),
                        "bomdod": safe_find("tc1"),
                        "quyosh": safe_find("tc2"),
                        "peshin": safe_find("tc3"),
                        "asr": safe_find("tc4"),
                        "shom": safe_find("tc5"),
                        "xufton": safe_find("tc6"),
                        "developer": "@Haker4ik"
                    }
                    return json.dumps(times, ensure_ascii=False, indent=4)
        except aiohttp.ClientError:
            await asyncio.sleep(2)

    return json.dumps({"error": "Failed to fetch prayer times"}, ensure_ascii=False, indent=4)



# import asyncio
# asyncio.run(all_regions())
# asyncio.run(namoz_vaqti(18))
        


