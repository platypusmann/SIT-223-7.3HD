"""
Monitoring and metrics module for the FastAPI application
Provides Prometheus metrics and health monitoring endpoints
"""

import time
from typing import Dict, Any
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from fastapi import Request, Response
import psutil
import logging

logger = logging.getLogger(__name__)

# Prometheus metrics
REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

REQUEST_LATENCY = Histogram(
    'http_request_duration_seconds',
    'HTTP request latency in seconds',
    ['method', 'endpoint']
)

ACTIVE_CONNECTIONS = Gauge(
    'active_connections',
    'Number of active connections'
)

SYSTEM_CPU_USAGE = Gauge(
    'system_cpu_usage_percent',
    'System CPU usage percentage'
)

SYSTEM_MEMORY_USAGE = Gauge(
    'system_memory_usage_percent', 
    'System memory usage percentage'
)

APPLICATION_INFO = Gauge(
    'application_info',
    'Application information',
    ['version', 'environment']
)

class MetricsMiddleware:
    """Middleware to collect HTTP request metrics"""
    
    def __init__(self, app_version: str = "unknown", environment: str = "development"):
        self.app_version = app_version
        self.environment = environment
        # Set application info metric
        APPLICATION_INFO.labels(version=app_version, environment=environment).set(1)
    
    async def __call__(self, request: Request, call_next):
        """Process request and collect metrics"""
        start_time = time.time()
        
        # Get endpoint path (remove query parameters)
        endpoint = request.url.path
        method = request.method
        
        # Increment active connections
        ACTIVE_CONNECTIONS.inc()
        
        try:
            # Process request
            response = await call_next(request)
            
            # Record metrics
            duration = time.time() - start_time
            status_code = str(response.status_code)
            
            REQUEST_COUNT.labels(method=method, endpoint=endpoint, status=status_code).inc()
            REQUEST_LATENCY.labels(method=method, endpoint=endpoint).observe(duration)
            
            return response
            
        except Exception as e:
            # Record error metrics
            duration = time.time() - start_time
            REQUEST_COUNT.labels(method=method, endpoint=endpoint, status="500").inc()
            REQUEST_LATENCY.labels(method=method, endpoint=endpoint).observe(duration)
            raise e
            
        finally:
            # Decrement active connections
            ACTIVE_CONNECTIONS.dec()

def update_system_metrics():
    """Update system-level metrics"""
    try:
        # CPU usage
        cpu_percent = psutil.cpu_percent(interval=1)
        SYSTEM_CPU_USAGE.set(cpu_percent)
        
        # Memory usage
        memory = psutil.virtual_memory()
        SYSTEM_MEMORY_USAGE.set(memory.percent)
        
        logger.debug(f"System metrics updated: CPU {cpu_percent}%, Memory {memory.percent}%")
        
    except Exception as e:
        logger.warning(f"Failed to update system metrics: {e}")

def get_metrics() -> str:
    """Get Prometheus metrics in text format"""
    # Update system metrics before returning
    update_system_metrics()
    return generate_latest()

def get_health_status() -> Dict[str, Any]:
    """Get comprehensive health status"""
    try:
        # Basic health checks
        health_status = {
            "status": "healthy",
            "timestamp": time.time(),
            "version": getattr(get_health_status, 'app_version', 'unknown'),
            "environment": getattr(get_health_status, 'environment', 'development'),
            "checks": {
                "api": "healthy",
                "database": "not_configured",  # Would check actual DB connection
                "file_system": "healthy",
                "memory": "healthy"
            }
        }
        
        # System resource checks
        try:
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Memory check (warn if > 90%)
            if memory.percent > 90:
                health_status["checks"]["memory"] = "warning"
                health_status["status"] = "degraded"
            
            # Disk check (warn if > 85%)
            if disk.percent > 85:
                health_status["checks"]["file_system"] = "warning"
                health_status["status"] = "degraded"
                
            health_status["system"] = {
                "cpu_percent": psutil.cpu_percent(),
                "memory_percent": memory.percent,
                "disk_percent": disk.percent
            }
            
        except Exception as e:
            logger.warning(f"System check failed: {e}")
            health_status["checks"]["system"] = "warning"
        
        return health_status
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "timestamp": time.time(),
            "error": str(e)
        }

# Initialize metrics middleware
def create_metrics_middleware(app_version: str = "1.0.0", environment: str = "development"):
    """Create and configure metrics middleware"""
    middleware = MetricsMiddleware(app_version, environment)
    
    # Store version info for health checks
    get_health_status.app_version = app_version
    get_health_status.environment = environment
    
    return middleware