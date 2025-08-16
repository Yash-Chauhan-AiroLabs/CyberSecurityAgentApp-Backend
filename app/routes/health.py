from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from starlette.status import HTTP_503_SERVICE_UNAVAILABLE
from datetime import datetime, timezone
from app.config.database import get_db
from app.config.settings import settings
import time

router = APIRouter()

@router.get("/check")
def basic_health_check():
    """
    Basic health check - just confirms the API is running
    """
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "service": settings.APP_NAME,
        "version": settings.VERSION
    }

@router.get("/detailed")
def detailed_health_check(db: Session = Depends(get_db)):
    """
    Detailed health check - includes database connectivity
    """
    start_time = time.time()
    
    # Check database connectivity
    try:
        # Simple query to test database connection
        db.execute(text("SELECT 1"))
        db_status = "healthy"
        db_response_time = round((time.time() - start_time) * 1000, 2)  # ms
    except Exception as e:
        db_status = "unhealthy"
        db_response_time = None
        # In production, you might want to log this error
        print(f"Database health check failed: {e}")
    
    total_response_time = round((time.time() - start_time) * 1000, 2)
    
    health_data = {
        "status": "healthy" if db_status == "healthy" else "unhealthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "service": settings.APP_NAME,
        "version": settings.VERSION,
        "checks": {
            "database": {
                "status": db_status,
                "response_time_ms": db_response_time
            }
        },
        "response_time_ms": total_response_time
    }
    
    # Return 503 if any service is unhealthy
    if health_data["status"] == "unhealthy":
        raise HTTPException(
            status_code=HTTP_503_SERVICE_UNAVAILABLE, 
            detail=health_data
            )
    
    return health_data

@router.get("/ready")
def readiness_check(db: Session = Depends(get_db)):
    """
    Readiness probe - checks if service is ready to handle requests
    Used by Kubernetes/Docker orchestration
    """
    try:
        # Test database connection
        db.execute(text("SELECT 1"))
        
        # Add other readiness checks here:
        # - Check external API connectivity
        # - Verify required environment variables
        # - Test cache connectivity (Redis, etc.)
        
        return {
            "status": "ready",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        raise HTTPException(
            status_code=HTTP_503_SERVICE_UNAVAILABLE, 
            detail={
                "status": "not ready",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "error": str(e)
            }
        )
