"""Retry logic and error handling utilities."""
import asyncio
import logging
from typing import Callable, TypeVar, Any
from functools import wraps
import httpx

logger = logging.getLogger(__name__)

T = TypeVar('T')


async def retry_with_backoff(
    func: Callable[..., T],
    max_retries: int = 3,
    initial_delay: float = 1.0,
    backoff_factor: float = 2.0,
    exceptions: tuple = (httpx.TimeoutException, httpx.NetworkError)
) -> T:
    """
    Retry a function with exponential backoff.
    
    Args:
        func: Async function to retry
        max_retries: Maximum number of retry attempts
        initial_delay: Initial delay in seconds
        backoff_factor: Multiplier for delay after each retry
        exceptions: Tuple of exceptions to catch
        
    Returns:
        Result of the function call
        
    Raises:
        The last exception if all retries fail
    """
    delay = initial_delay
    last_exception = None
    
    for attempt in range(max_retries + 1):
        try:
            return await func()
        except exceptions as e:
            last_exception = e
            if attempt == max_retries:
                logger.error(f"All {max_retries} retries failed: {e}")
                raise
            
            logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {delay}s...")
            await asyncio.sleep(delay)
            delay *= backoff_factor
    
    raise last_exception


def handle_api_errors(service_name: str):
    """
    Decorator to handle common API errors.
    
    Args:
        service_name: Name of the external service (e.g., 'GitHub', 'solved.ac')
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            from app.exceptions import (
                ExternalAPIError,
                RateLimitError,
                AuthenticationError,
                NetworkError
            )
            
            try:
                return await func(*args, **kwargs)
            except httpx.HTTPStatusError as e:
                status_code = e.response.status_code
                
                if status_code == 401:
                    raise AuthenticationError(f"{service_name} 인증에 실패했습니다")
                elif status_code == 403:
                    raise RateLimitError(f"{service_name} API 호출 한도를 초과했습니다")
                elif status_code == 404:
                    raise ExternalAPIError(service_name, "요청한 리소스를 찾을 수 없습니다")
                elif status_code >= 500:
                    raise ExternalAPIError(service_name, f"{service_name} 서버 오류")
                else:
                    raise ExternalAPIError(service_name, f"알 수 없는 오류 (HTTP {status_code})")
                    
            except httpx.TimeoutException:
                raise NetworkError(f"{service_name} API 응답 시간 초과")
                
            except httpx.NetworkError as e:
                raise NetworkError(f"{service_name} 네트워크 오류: {str(e)}")
                
            except Exception as e:
                logger.exception(f"Unexpected error in {service_name} API call")
                raise ExternalAPIError(service_name, f"예상치 못한 오류: {str(e)}")
        
        return wrapper
    return decorator


class RateLimiter:
    """Simple rate limiter for API calls."""
    
    def __init__(self, max_calls: int, time_window: float):
        """
        Args:
            max_calls: Maximum number of calls allowed
            time_window: Time window in seconds
        """
        self.max_calls = max_calls
        self.time_window = time_window
        self.calls = []
    
    async def acquire(self):
        """Wait if rate limit would be exceeded."""
        import time
        
        now = time.time()
        
        # Remove old calls outside the time window
        self.calls = [call_time for call_time in self.calls if now - call_time < self.time_window]
        
        if len(self.calls) >= self.max_calls:
            # Calculate how long to wait
            oldest_call = self.calls[0]
            wait_time = self.time_window - (now - oldest_call)
            
            if wait_time > 0:
                logger.info(f"Rate limit reached. Waiting {wait_time:.2f}s...")
                await asyncio.sleep(wait_time)
                # Recursive call to check again
                return await self.acquire()
        
        self.calls.append(now)


# Global rate limiters for different services
github_rate_limiter = RateLimiter(max_calls=60, time_window=60.0)  # 60 calls per minute
solvedac_rate_limiter = RateLimiter(max_calls=100, time_window=60.0)  # 100 calls per minute
