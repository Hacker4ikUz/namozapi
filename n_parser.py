import redis.asyncio as redis
import aiohttp
import asyncio
import json
import random
from bs4 import BeautifulSoup
from regions import regions
from datetime import datetime
import logging


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

HEADERS_LIST = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/109.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/109.0",
]

user = 'lsykfknw'
password = 'ft7fdlodh1u3'

PROXY_LIST = [ 
    f"http://{user}:{password}@23.95.150.145:6114",
    f"http://{user}:{password}@198.23.239.134:6540",
    f"http://{user}:{password}@45.38.107.97:6014",
    f"http://{user}:{password}@107.172.163.27:6543",
    f"http://{user}:{password}@64.137.96.74:6641",
    f"http://{user}:{password}@45.43.186.39:6257",
    f"http://{user}:{password}@154.203.43.247:5536",
    f"http://{user}:{password}@216.10.27.159:6837",
    f"http://{user}:{password}@136.0.207.84:6661",
    f"http://{user}:{password}@142.147.128.93:6593",
]

REGION_IDS = [1, 4, 5, 9, 14, 15, 16, 18, 21, 25, 27, 37, 74]
CACHE_TTL = 86400  # 24 soat
MAX_RETRIES = 4
MIN_DELAY = 45
MAX_DELAY = 75


class NamozParser:
    def __init__(self, redis_url="redis://localhost"):
        self.session = None
        self.redis = None
        self.redis_url = redis_url
        self.proxy_index = 0

    async def init_services(self):
        if not self.session:
            connector = aiohttp.TCPConnector(
                limit=1,
                limit_per_host=1,
                enable_cleanup_closed=True,
                ttl_dns_cache=300,
                use_dns_cache=True,
            )
            timeout = aiohttp.ClientTimeout(total=45, connect=15)
            self.session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout,
            )
        if not self.redis:
            self.redis = await redis.from_url(self.redis_url, decode_responses=True)
            await self.redis.ping()  # Проверяем соединение

    async def close_services(self):
        if self.session:
            await self.session.close()
            self.session = None
        if self.redis:
            await self.redis.close()
            self.redis = None

    def get_next_proxy(self):
        proxy = PROXY_LIST[self.proxy_index]
        self.proxy_index = (self.proxy_index + 1) % len(PROXY_LIST)
        return proxy

    async def all_regions(self):
        return json.dumps(regions, ensure_ascii=False, indent=4)

    async def fetch_namoz_data(self, region_id: int):
        await self.init_services()
        cache_key = f"namoz:region:{region_id}"
        today = datetime.now().strftime("%d-%m-%Y")

        # Проверяем кэш
        cached_data = await self.redis.get(cache_key)
        if cached_data:
            data = json.loads(cached_data)
            if data.get("date") == today:
                logger.info(f"Region {region_id}: данные уже есть в кэше")
                return data

        base_urls = ["https://islom.uz", "https://islam.uz"]
        
        for attempt in range(MAX_RETRIES):
            proxy = self.get_next_proxy()
            headers = {
                "User-Agent": random.choice(HEADERS_LIST),
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
                "Accept-Encoding": "gzip, deflate, br",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
                "Cache-Control": "no-cache",
                "Pragma": "no-cache",
            }
            
            for base_url in base_urls:
                url = f"{base_url}/region/{region_id}"
                
                try:
                    logger.info(f"Region {region_id}: попытка {attempt + 1}/{MAX_RETRIES}")
                    
                    async with self.session.get(
                        url, 
                        headers=headers, 
                        proxy=proxy,
                        allow_redirects=True
                    ) as resp:
                        
                        if resp.status == 429:
                            delay = random.uniform(120, 180)
                            logger.warning(f"Region {region_id}: Rate limit, ждем {delay:.1f} сек")
                            await asyncio.sleep(delay)
                            continue
                            
                        if resp.status == 403:  # Forbidden
                            delay = random.uniform(90, 120)
                            logger.warning(f"Region {region_id}: Forbidden, ждем {delay:.1f} сек")
                            await asyncio.sleep(delay)
                            continue
                            
                        if resp.status != 200:
                            logger.warning(f"Region {region_id}: HTTP {resp.status}")
                            await asyncio.sleep(random.uniform(15, 30))
                            continue

                        html = await resp.text(encoding="utf-8")
                        
                        if len(html) < 1000:
                            logger.warning(f"Region {region_id}: подозрительно короткий ответ")
                            await asyncio.sleep(random.uniform(10, 20))
                            continue
                            
                        soup = BeautifulSoup(html, "lxml")

                        def safe_find(element_id):
                            tag = soup.find("div", id=element_id)
                            if tag:
                                text = tag.text.strip()
                                if text and len(text) >= 4 and ":" in text:
                                    return text
                            return "N/A"

                        region_name = "Unknown"
                        for region in regions.values():
                            if region["region_id"] == region_id:
                                region_name = region["region_name"]
                                break

                        data = {
                            "region": region_name,
                            "region_id": region_id,
                            "date": today,
                            "bomdod": safe_find("tc1"),
                            "quyosh": safe_find("tc2"),
                            "peshin": safe_find("tc3"),
                            "asr": safe_find("tc4"),
                            "shom": safe_find("tc5"),
                            "xufton": safe_find("tc6"),
                            "updated_at": datetime.now().isoformat(),
                            "developer": "@Haker4ik",
                        }

                        prayer_times = [data["bomdod"], data["quyosh"], data["peshin"], 
                                      data["asr"], data["shom"], data["xufton"]]
                        valid_times = [t for t in prayer_times if t != "N/A" and ":" in t]
                        
                        if len(valid_times) < 4:
                            logger.warning(f"Region {region_id}: недостаточно данных ({len(valid_times)}/6)")
                            await asyncio.sleep(random.uniform(10, 20))
                            continue

                        await self.redis.setex(cache_key, CACHE_TTL, json.dumps(data, ensure_ascii=False))
                        logger.info(f"Region {region_id}: успешно обновлен! ({len(valid_times)}/6 времен)")
                        return data

                except asyncio.TimeoutError:
                    logger.warning(f"Region {region_id}: timeout на попытке {attempt + 1}")
                    await asyncio.sleep(random.uniform(10, 20))
                except aiohttp.ClientError as e:
                    logger.warning(f"Region {region_id}: ошибка клиента - {str(e)[:100]}")
                    await asyncio.sleep(random.uniform(10, 20))
                except Exception as e:
                    logger.error(f"Region {region_id}: неожиданная ошибка - {str(e)[:100]}")
                    await asyncio.sleep(random.uniform(15, 30))

            if attempt < MAX_RETRIES - 1:
                delay = random.uniform(30, 60) * (attempt + 1)
                logger.info(f"Region {region_id}: ждем {delay:.1f} сек до следующей попытки")
                await asyncio.sleep(delay)

        logger.error(f"Region {region_id}: не удалось получить данные после {MAX_RETRIES} попыток")
        return None

    async def process_all_regions(self):
        """Улучшенная версия для обновления всех регионов"""
        await self.init_services()
        
        today = datetime.now().strftime("%d-%m-%Y")
        
        logger.info(f"Начинаем обновление всех {len(REGION_IDS)} регионов...")
        
        successful_regions = []
        failed_regions = []
        
        regions_to_update = []
        for region_id in REGION_IDS:
            cache_key = f"namoz:region:{region_id}"
            cached_data = await self.redis.get(cache_key)
            
            if cached_data:
                data = json.loads(cached_data)
                if data.get("date") == today:
                    logger.info(f"Region {region_id}: уже актуален")
                    successful_regions.append(region_id)
                    continue
            
            regions_to_update.append(region_id)

        if not regions_to_update:
            logger.info("Все регионы уже обновлены!")
            return {
                "status": "all_cached",
                "total": len(REGION_IDS),
                "updated": 0,
                "failed": 0,
                "message": "Все данные уже актуальны"
            }

        logger.info(f"Нужно обновить {len(regions_to_update)} регионов")
        
        for i, region_id in enumerate(regions_to_update):
            logger.info(f"Обрабатываем регион {region_id} ({i + 1}/{len(regions_to_update)})")
            
            result = await self.fetch_namoz_data(region_id)
            
            if result:
                successful_regions.append(region_id)
                logger.info(f"✓ Регион {region_id}: успешно")
            else:
                failed_regions.append(region_id)
                logger.error(f"✗ Регион {region_id}: ошибка")
            
            if i < len(regions_to_update) - 1:
                delay = random.uniform(MIN_DELAY, MAX_DELAY)
                logger.info(f"Ждем {delay:.1f} секунд...")
                await asyncio.sleep(delay)

        if failed_regions and len(failed_regions) <= 3:
            logger.info(f"Повторная попытка для {len(failed_regions)} регионов...")
            await asyncio.sleep(180)
            
            for region_id in failed_regions[:]:
                logger.info(f"Повторная попытка: регион {region_id}")
                result = await self.fetch_namoz_data(region_id)
                
                if result:
                    successful_regions.append(region_id)
                    failed_regions.remove(region_id)
                    logger.info(f"✓ Регион {region_id}: успешно при повторной попытке")
                
                await asyncio.sleep(random.uniform(60, 90))

        success_rate = len(successful_regions) / len(REGION_IDS) * 100
        
        result = {
            "status": "completed",
            "total_regions": len(REGION_IDS),
            "successful": len(successful_regions),
            "failed": len(failed_regions),
            "success_rate": f"{success_rate:.1f}%",
            "date": today,
            "successful_regions": successful_regions,
            "failed_regions": failed_regions if failed_regions else None
        }
        
        if success_rate >= 80:
            logger.info(f"✅ Обновление завершено успешно! {success_rate:.1f}% регионов обновлено")
        else:
            logger.warning(f"⚠️ Частичное обновление: {success_rate:.1f}% регионов")
        
        return result


namoz_parser = NamozParser()
