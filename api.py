from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, RedirectResponse
from n_parser import *
import uvicorn



app = FastAPI(
    title="NamozAPI.uz - Namoz vaqtlari - Prayer times",
    description="""API для получения времени намаза  
API for getting prayer times""",
    version="1.0.0",
    contact={
        "name": "Developer",
        "url": "https://t.me/Haker4ik"
    }
)


@app.get("/", include_in_schema=False)
async def redirect_to_docs():
    return RedirectResponse(url="/docs")


@app.get("/namoz/{region_id}")
async def get_namoz_times(region_id: int):
    res = await namoz_vaqti(region_id)
    times = json.loads(res)
    return times


@app.get("/regions")
async def get_all_regions():
    res = await all_regions()
    regions = json.loads(res)
    return regions


@app.exception_handler(404)
async def not_found(request: Request, exc: Exception):
    return JSONResponse(status_code=404, content={"detail": "Not Found", "support": "@Haker4ik"})


if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=80)