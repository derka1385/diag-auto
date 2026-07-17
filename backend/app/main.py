from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.api import router
from app.modules.vehicle_resolution.routes import router as vehicle_resolution_router
from app.modules.vehicle_data.routes import router as vehicle_data_router
from app.modules.diagnostic_ai.routes import router as diagnostic_ai_router
from app.core.config import settings
from app.core.logging import configure_logging, logger

configure_logging()
app=FastAPI(title="DiagPilot API",version="0.1.0",description="MVP fictif d’assistance au diagnostic automobile. Lecture seule.")
app.add_middleware(CORSMiddleware,allow_origins=[x.strip() for x in settings.cors_origins.split(",")],allow_credentials=False,allow_methods=["GET","POST","PUT","PATCH","DELETE"],allow_headers=["Content-Type","X-Garage-ID"])
app.include_router(router)
app.include_router(vehicle_resolution_router)
app.include_router(vehicle_data_router)
app.include_router(diagnostic_ai_router)
@app.middleware("http")
async def limit_request_size(request:Request,call_next):
    length=request.headers.get("content-length")
    request_limit=max(settings.max_upload_bytes,settings.max_image_total_bytes+1_000_000)
    if length and length.isdigit() and int(length)>request_limit:
        return JSONResponse(status_code=413,content={"detail":"Requête trop volumineuse"})
    return await call_next(request)
@app.exception_handler(Exception)
async def unexpected(request:Request,exc:Exception):
    logger.exception("unhandled_error",path=request.url.path,error_type=type(exc).__name__)
    return JSONResponse(status_code=500,content={"detail":"Erreur interne. Consultez les journaux avec l’identifiant de requête."})
