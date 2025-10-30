from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from contextlib import asynccontextmanager
import os

from app.database import init_db
from app.api import tasks


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize on startup"""
    # Create data directory
    os.makedirs("./data", exist_ok=True)

    # Initialize database
    await init_db()
    print("Database initialized")

    yield


app = FastAPI(
    title="JamUpTaskMaster",
    description="Task management for neurodivergent workflows",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS for dashboard
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API routes
app.include_router(tasks.router, prefix="/api", tags=["tasks"])


# Dashboard route
@app.get("/", response_class=HTMLResponse)
async def dashboard():
    """Serve the dashboard HTML"""
    html_path = os.path.join(os.path.dirname(__file__), "static", "dashboard.html")

    if os.path.exists(html_path):
        with open(html_path, "r") as f:
            return HTMLResponse(content=f.read())
    else:
        return HTMLResponse(
            content="""
            <html>
            <body>
                <h1>JamUpTaskMaster</h1>
                <p>Dashboard coming soon...</p>
                <p>API is running at <a href="/docs">/docs</a></p>
            </body>
            </html>
            """
        )


@app.get("/health")
async def health():
    """Health check"""
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port)
