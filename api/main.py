from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from .routes.generate_form import router as generate_form_router

app = FastAPI(
    title="Resume PDF API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS setup to allow all origins during development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Custom exception handler for validation errors.

    Args:
        request (Request): The incoming request object.
        exc (RequestValidationError): The validation error raised.

    Returns:
        JSONResponse: A structured JSON response with error details.
    """
    print("[Error] 422 details:", exc.errors())
    return JSONResponse(status_code=422, content={"detail": exc.errors()})

# Register the generate form router
app.include_router(generate_form_router)

@app.get("/healthz")
def healthz():
    """
    Basic health check endpoint.

    Returns:
        dict: A simple dictionary indicating the service is healthy.
    """
    return {"ok": True}