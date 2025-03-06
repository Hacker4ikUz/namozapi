import aiohttp
from bs4 import BeautifulSoup
import json



async def all_regions():
    async with aiohttp.ClientSession() as session:
        async with session.get("https://islom.uz/region/1") as resp:
            if resp.status != 200:
                err = json.dumps({"error": "Failed to fetch regions"}, ensure_ascii=False, indent=4)
                return err
            
            html = await resp.text()
            soup = BeautifulSoup(html, features="lxml")
            regions = soup.find('div', class_="custom-select")
            region = {}
            b = 0
            for i in regions.find('select').find_all('option'):
                b += 1
                region[b] = {'region_name': i.text.strip(), 'region_id': int(i['value'])}

            regions = json.dumps(region, ensure_ascii=False, indent=4)
            return regions


async def namoz_vaqti(region_id: int):
    async with aiohttp.ClientSession() as session:
        async with session.get(f"https://islom.uz/region/{region_id}") as resp:
            if resp.status != 200:
                err = json.dumps({"error": "Failed to fetch prayer times"}, ensure_ascii=False, indent=4)
                return err
            
            html = await resp.text()
            soup = BeautifulSoup(html, features="lxml")
            bomdod = soup.find('div', id="tc1").text
            quyosh = soup.find('div', id="tc2").text
            peshin = soup.find('div', id="tc3").text
            asr = soup.find('div', id="tc4").text
            shom = soup.find('div', id="tc5").text
            xufton = soup.find('div', id="tc6").text
            date_time = soup.find('div', class_="date_time").text.strip()
            times = {
                "date": date_time,
                "bomdod": bomdod,
                "quyosh": quyosh,
                "peshin": peshin,
                "asr": asr,
                "shom": shom,
                "xufton": xufton,
                "developer": "@Haker4ik"
            }
            n_times = json.dumps(times, ensure_ascii=False, indent=4)
            return n_times



# import asyncio
# asyncio.run(all_regions())
# asyncio.run(namoz_vaqti(18))
        


