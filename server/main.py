from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from api.routers.workflows import router as workflows_router
from api.routers.executions import router as executions_router
from infra.db.database import create_tables
from config.logging import setup_logging, get_logger

# Setup logging as early as possible
setup_logging()
logger = get_logger("main")

app = FastAPI(
    title="LayerX Workflow Engine",
    description="A workflow execution engine with node-based processing",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Custom exception handler for validation errors
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors without trying to decode binary data"""
    errors = []
    for error in exc.errors():
        # Clean up error dict to avoid binary data issues
        clean_error = {
            "type": error.get("type"),
            "loc": error.get("loc"),
            "msg": error.get("msg"),
        }
        # Only include input if it's not binary data
        if "input" in error and isinstance(error["input"], (str, int, float, bool, list, dict, type(None))):
            clean_error["input"] = error["input"]
        errors.append(clean_error)

    return JSONResponse(
        status_code=422,
        content={"detail": errors}
    )

# Include routers
app.include_router(workflows_router, prefix="/api")
app.include_router(executions_router, prefix="/api")

@app.on_event("startup")
async def startup_event():
    """Initialize database tables on startup"""
    logger.info("Starting LayerX Workflow Engine...")
    await create_tables()
    logger.info("Database tables initialized successfully")

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "LayerX Workflow Engine is running",
        "version": "1.0.0",
        "status": "healthy"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring"""
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)