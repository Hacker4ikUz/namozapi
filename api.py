from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, RedirectResponse
from xz import *
import uvicorn


app = FastAPI()
BASE_URL = "https://islom.uz/region/"


@app.get("/", include_in_schema=False)
async def redirect_to_docs():
    return RedirectResponse(url="/docs")


@app.get("/namoz/{region_id}")
async def get_namoz_times(region_id: int):
    res = await namoz_vaqti(region_id)
    times = json.loads(res)
    return times


@app.get("/namoz/regions")
async def get_all_regions():
        res = await all_regions()
        regions = json.loads(res)
        return regions


@app.exception_handler(404)
async def not_found(request: Request, exc: Exception):
    return JSONResponse(status_code=404, content={"detail": "Not Found", "support": "@Haker4ik"})


if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=80)