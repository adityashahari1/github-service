# Rate limiter for GitHub API
# Author: Mohsen Minai

import asyncio
from fastapi import HTTPException


class RateLimiter:
    #rate limiter that waits when we hit limits
    
    def __init__(self):
        self.remaining = None
        self.wait_seconds = None
    
    def update_from_headers(self, headers):
        #get rate limit info from GitHub response
        if "x-ratelimit-remaining" in headers:
            self.remaining = int(headers["x-ratelimit-remaining"])
    
    async def wait_if_needed(self):
        #wait if we're low on API calls
        if self.remaining and self.remaining < 10:
            await asyncio.sleep(1)  # Simple 1 second wait
    
    def handle_rate_limit_error(self, status_code, headers):
        #throw error when rate limited
        if status_code == 429:
            retry_after = headers.get("retry-after", "60")
            raise HTTPException(
                status_code=429,
                detail=f"Rate limited. Wait {retry_after} seconds"
            )


# one global rate limiter
rate_limiter = RateLimiter()


