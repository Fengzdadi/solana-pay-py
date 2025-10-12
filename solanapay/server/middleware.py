"""Middleware for Solana Pay transaction request server."""

from __future__ import annotations

import time
import logging
from typing import Dict, Any, Optional
from collections import defaultdict, deque

from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.responses import JSONResponse
from starlette.status import HTTP_429_TOO_MANY_REQUESTS, HTTP_500_INTERNAL_SERVER_ERROR

from .schemas import ErrorResponse
from ..utils.errors import SolanaPayError

logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware to prevent abuse.
    
    Implements a simple token bucket rate limiter per IP address.
    """
    
    def __init__(
        self,
        app,
        requests_per_minute: int = 60,
        burst_size: int = 10
    ):
        """Initialize rate limiter.
        
        Args:
            app: FastAPI application
            requests_per_minute: Maximum requests per minute per IP
            burst_size: Maximum burst requests allowed
        """
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.burst_size = burst_size
        self.buckets: Dict[str, deque] = defaultdict(deque)
        
    async def dispatch(self, request: Request, call_next):
        """Process request with rate limiting."""
        client_ip = self._get_client_ip(request)
        current_time = time.time()
        
        # Clean old requests (older than 1 minute)
        bucket = self.buckets[client_ip]
        while bucket and bucket[0] < current_time - 60:
            bucket.popleft()
        
        # Check rate limit
        if len(bucket) >= self.requests_per_minute:
            logger.warning(f"Rate limit exceeded for IP: {client_ip}")
            return JSONResponse(
                status_code=HTTP_429_TOO_MANY_REQUESTS,
                content=ErrorResponse(
                    error="Rate limit exceeded",
                    code="RATE_LIMIT_EXCEEDED",
                    details={
                        "requests_per_minute": self.requests_per_minute,
                        "retry_after": 60
                    }
                ).dict()
            )
        
        # Check burst limit
        recent_requests = sum(1 for t in bucket if t > current_time - 10)  # Last 10 seconds
        if recent_requests >= self.burst_size:
            logger.warning(f"Burst limit exceeded for IP: {client_ip}")
            return JSONResponse(
                status_code=HTTP_429_TOO_MANY_REQUESTS,
                content=ErrorResponse(
                    error="Too many requests in short time",
                    code="BURST_LIMIT_EXCEEDED",
                    details={
                        "burst_size": self.burst_size,
                        "retry_after": 10
                    }
                ).dict()
            )
        
        # Add current request to bucket
        bucket.append(current_time)
        
        # Process request
        response = await call_next(request)
        return response
    
    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address from request."""
        # Check for forwarded headers (when behind proxy)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # Fallback to direct client IP
        return request.client.host if request.client else "unknown"


class LoggingMiddleware(BaseHTTPMiddleware):
    """Logging middleware for request/response tracking."""
    
    def __init__(self, app, log_requests: bool = True, log_responses: bool = False):
        """Initialize logging middleware.
        
        Args:
            app: FastAPI application
            log_requests: Whether to log incoming requests
            log_responses: Whether to log outgoing responses
        """
        super().__init__(app)
        self.log_requests = log_requests
        self.log_responses = log_responses
    
    async def dispatch(self, request: Request, call_next):
        """Process request with logging."""
        start_time = time.time()
        
        # Log incoming request
        if self.log_requests:
            logger.info(
                f"Request: {request.method} {request.url.path} "
                f"from {self._get_client_ip(request)}"
            )
        
        # Process request
        try:
            response = await call_next(request)
            
            # Calculate processing time
            process_time = time.time() - start_time
            
            # Log response
            if self.log_responses:
                logger.info(
                    f"Response: {response.status_code} "
                    f"({process_time:.3f}s)"
                )
            
            # Add processing time header
            response.headers["X-Process-Time"] = str(process_time)
            
            return response
            
        except Exception as e:
            process_time = time.time() - start_time
            logger.error(
                f"Request failed: {request.method} {request.url.path} "
                f"({process_time:.3f}s) - {str(e)}"
            )
            raise
    
    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address from request."""
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        return request.client.host if request.client else "unknown"


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Global error handling middleware."""
    
    async def dispatch(self, request: Request, call_next):
        """Process request with error handling."""
        try:
            return await call_next(request)
            
        except HTTPException:
            # Let FastAPI handle HTTP exceptions
            raise
            
        except SolanaPayError as e:
            # Handle Solana Pay specific errors
            logger.error(f"Solana Pay error: {e}")
            
            return JSONResponse(
                status_code=400,
                content=ErrorResponse(
                    error=e.message,
                    code=e.error_code,
                    details=e.context
                ).dict()
            )
            
        except Exception as e:
            # Handle unexpected errors
            logger.exception(f"Unexpected error: {e}")
            
            return JSONResponse(
                status_code=HTTP_500_INTERNAL_SERVER_ERROR,
                content=ErrorResponse(
                    error="Internal server error",
                    code="INTERNAL_ERROR"
                ).dict()
            )


def setup_cors(
    app: FastAPI,
    allowed_origins: Optional[list] = None,
    allow_credentials: bool = True,
    allowed_methods: Optional[list] = None,
    allowed_headers: Optional[list] = None
):
    """Set up CORS middleware for the application.
    
    Args:
        app: FastAPI application
        allowed_origins: List of allowed origins (None for all)
        allow_credentials: Whether to allow credentials
        allowed_methods: List of allowed HTTP methods
        allowed_headers: List of allowed headers
    """
    if allowed_origins is None:
        allowed_origins = ["*"]
    
    if allowed_methods is None:
        allowed_methods = ["GET", "POST", "OPTIONS"]
    
    if allowed_headers is None:
        allowed_headers = [
            "Content-Type",
            "Authorization",
            "X-Requested-With",
            "Accept",
            "Origin"
        ]
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=allow_credentials,
        allow_methods=allowed_methods,
        allow_headers=allowed_headers,
        expose_headers=["X-Process-Time"]
    )


def setup_middleware(
    app: FastAPI,
    enable_rate_limiting: bool = True,
    enable_logging: bool = True,
    enable_error_handling: bool = True,
    enable_cors: bool = True,
    rate_limit_rpm: int = 60,
    rate_limit_burst: int = 10,
    cors_origins: Optional[list] = None
):
    """Set up all middleware for the application.
    
    Args:
        app: FastAPI application
        enable_rate_limiting: Whether to enable rate limiting
        enable_logging: Whether to enable request logging
        enable_error_handling: Whether to enable error handling
        enable_cors: Whether to enable CORS
        rate_limit_rpm: Rate limit requests per minute
        rate_limit_burst: Rate limit burst size
        cors_origins: CORS allowed origins
    """
    # Add middleware in reverse order (last added = first executed)
    
    if enable_error_handling:
        app.add_middleware(ErrorHandlingMiddleware)
    
    if enable_logging:
        app.add_middleware(LoggingMiddleware)
    
    if enable_rate_limiting:
        app.add_middleware(
            RateLimitMiddleware,
            requests_per_minute=rate_limit_rpm,
            burst_size=rate_limit_burst
        )
    
    if enable_cors:
        setup_cors(app, allowed_origins=cors_origins)


class SecurityHeaders:
    """Security headers for API responses."""
    
    @staticmethod
    def add_security_headers(response: Response):
        """Add security headers to response."""
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Content-Security-Policy"] = "default-src 'self'"


def create_health_check_endpoint(app: FastAPI):
    """Add a health check endpoint to the application.
    
    Args:
        app: FastAPI application
    """
    @app.get("/health", include_in_schema=False)
    async def health_check():
        """Health check endpoint."""
        return {
            "status": "healthy",
            "timestamp": time.time(),
            "service": "solana-pay-transaction-request"
        }