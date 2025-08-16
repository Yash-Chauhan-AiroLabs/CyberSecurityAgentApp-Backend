# app/main.py - Updated with health routes
from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from app.config.database import engine, Base
from app.config.settings import settings
from app.routes.health import router as health_router

# Create database tables
Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    debug=settings.DEBUG,
)

# Include health check routes
app.include_router(health_router, tags=["Health"], prefix="/health")

# Example route using database
@app.get("/")
def root():
    return RedirectResponse(url="/docs")

# Run the application
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app", 
        host="0.0.0.0", 
        port=8000, 
        reload=settings.DEBUG
    )