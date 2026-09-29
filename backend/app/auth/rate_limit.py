"""
Lightweight In-Memory Sliding-Window Rate Limiter Middleware for BhuSetu APIs.
Protects sensitive land record and cadastral endpoints against scraping and DoS.
"""

import time
from collections import defaultdict
from typing import Dict, List
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

# Maximum requests per minute by default
DEFAULT_RATE_LIMIT = 180  # requests per 60 seconds
WINDOW_SECONDS = 60


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, requests_per_minute: int = DEFAULT_RATE_LIMIT):
        super().__init__(app)
        self.limit = requests_per_minute
        self.requests_log: Dict[str, List[float]] = defaultdict(list)

    async def dispatch(self, request: Request, call_next):
        # Exclude static assets and health check from rate limiting
        path = request.url.path
        if path.startswith("/storage") or path in ["/health", "/api/health", "/docs", "/openapi.json"]:
            return await call_next(request)

        # Identify client by API Key, Authorization, or Client IP
        client_key = request.headers.get("X-API-Key") or request.headers.get("Authorization") or (request.client.host if request.client else "unknown")

        now = time.time()
        window_start = now - WINDOW_SECONDS

        # Prune old timestamps
        timestamps = [t for t in self.requests_log[client_key] if t > window_start]
        self.requests_log[client_key] = timestamps

        if len(timestamps) >= self.limit:
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Too Many Requests",
                    "message": f"Rate limit exceeded ({self.limit} requests per minute). Please throttle your requests.",
                    "retry_after_seconds": int(WINDOW_SECONDS - (now - timestamps[0]))
                },
                headers={"Retry-After": str(int(WINDOW_SECONDS - (now - timestamps[0])))}
            )

        self.requests_log[client_key].append(now)
        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(self.limit)
        response.headers["X-RateLimit-Remaining"] = str(max(0, self.limit - len(self.requests_log[client_key])))
        return response
