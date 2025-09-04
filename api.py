from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, RedirectResponse
from contextlib import asynccontextmanager
from datetime import datetime
from n_parser import *
import uvicorn
import json
import asyncio



@asynccontextmanager
async def lifespan(app: FastAPI):
    await namoz_parser.init_services()
    yield
    await namoz_parser.close_services()


app = FastAPI(
    lifespan=lifespan,
    title="NamozAPI.uz - Namoz vaqtlari - Prayer times",
    description="""API для получения времени намаза  
API for getting prayer times

👨‍💻 [Developer](https://t.me/Haker4ik)""",
    version="1.0.0",
)


@app.get("/", include_in_schema=False)
async def redirect_to_docs():
    return RedirectResponse(url="/docs")


@app.get("/namoz/all", include_in_schema=False)
async def get_all_namoz_times():
    cache_key = "namoz:last_update"
    last_update = await namoz_parser.redis.get(cache_key)
    today_date = datetime.now().strftime("%Y-%m-%d")

    if last_update and last_update == today_date:
        return {"status": "already_updated", "message": "Данные уже обновлены сегодня"}

    res = await namoz_parser.process_all_regions()
    
    await namoz_parser.redis.set(cache_key, today_date)

    return {"status": "updated", "details": res}


@app.get("/namoz/{region_id}")
async def get_namoz_times(region_id: int):
    res = await namoz_parser.fetch_namoz_data(region_id)
    return res if res else {"error": "Region not found"}


@app.get("/regions")
async def get_all_regions():
    res = await namoz_parser.all_regions()
    return json.loads(res)


@app.exception_handler(404)
async def not_found(request: Request, exc: Exception):
    """ Обработчик ошибки 404 """
    return JSONResponse(status_code=404, content={"detail": "Not Found", "support": "@Haker4ik"})


if __name__ == '__main__':
	uvicorn.run(app, host='0.0.0.0', port=80)
