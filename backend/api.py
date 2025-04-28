from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from collections import OrderedDict
from datetime import datetime, timezone
import asyncio
import uuid
import time
from dotenv import load_dotenv

from utils.config import config, EnvMode
from utils.logger import logger
from agentpress.thread_manager import ThreadManager
from services.supabase import DBConnection
from services import billing as billing_api
from services import redis
from agent import api as agent_api
from sandbox import api as sandbox_api
# Load environment variables
load_dotenv()

# Initialize managers
db = DBConnection()
thread_manager = None
instance_id = str(uuid.uuid4())[:8]  # Generate instance ID at module load time

# Rate limiter
ip_tracker = OrderedDict()
MAX_CONCURRENT_IPS = 25

@asynccontextmanager
async def lifespan(app: FastAPI):
    global thread_manager
    logger.info(f"Starting up FastAPI application with instance ID: {instance_id} in {config.ENV_MODE.value} mode")
    try:
        await db.initialize()
        thread_manager = ThreadManager()
        agent_api.initialize(thread_manager, db, instance_id)
        sandbox_api.initialize(db)

        try:
            await redis.initialize_async()
            logger.info("Redis connection initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Redis connection: {e}")

        asyncio.create_task(agent_api.restore_running_agent_runs())
        yield

        logger.info("Cleaning up agent resources")
        await agent_api.cleanup()

        try:
            logger.info("Closing Redis connection")
            await redis.close()
        except Exception as e:
            logger.error(f"Error closing Redis connection: {e}")

        logger.info("Disconnecting from database")
        await db.disconnect()

    except Exception as e:
        logger.error(f"Error during application startup: {e}")
        raise

# Create the FastAPI app with metadata
app = FastAPI(
    title="AgentPress API",
    description="Backend API for the AgentPress project",
    version="0.1.0",
    lifespan=lifespan
)

# Middleware to log every request
@app.middleware("http")
async def log_requests_middleware(request: Request, call_next):
    start_time = time.time()
    client_ip = request.client.host
    method = request.method
    path = request.url.path
    query_params = str(request.query_params)

    logger.info(f"Request started: {method} {path} from {client_ip} | Query: {query_params}")

    try:
        response = await call_next(request)
        process_time = time.time() - start_time
        logger.debug(f"Request completed: {method} {path} | Status: {response.status_code} | Time: {process_time:.2f}s")
        return response
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(f"Request failed: {method} {path} | Error: {str(e)} | Time: {process_time:.2f}s")
        raise

# CORS Setup
allowed_origins = [
    "https://www.suna.so",
    "https://suna.so",
    "https://staging.suna.so",
    "http://localhost:3000",
    "http://192.168.1.161:3000",  # ADD ALWAYS
    "http://192.168.1.160:8000",  # optional
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,  # Using our defined list of allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(agent_api.router, prefix="/api")
app.include_router(sandbox_api.router, prefix="/api")
app.include_router(billing_api.router, prefix="/api")
app.include_router(sandbox_api.router, prefix="/api")


# ——— Health check
@app.get("/api/health")
async def health():
    return {"status": "ok", "instance": instance_id}

# ——— Billing: the two endpoints your UI calls
@app.get("/api/billing/check-status")
async def billing_check():
    logger.info("Billing check-status called")
    return {"billing_required": False}

@app.get("/api/billing/subscription")
async def billing_subscription():
    logger.info("Billing subscription called")
    # return whatever your front-end expects here
    # for now stub it out so your UI stops  refusing connection
    return {"subscription_active": False}

# Dev mode run
if __name__ == "__main__":
    import uvicorn

    workers = 2

    logger.info(f"Starting server on 0.0.0.0:8000 with {workers} workers")
    uvicorn.run(
        "api:app",
        host="0.0.0.0",
        port=8000,
        workers=workers,
        reload=True
    )
