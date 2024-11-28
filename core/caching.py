"""Caching system for Arcana Agent Framework."""

from typing import Dict, Any, Optional, Callable, TypeVar, Generic
from datetime import datetime, timedelta
import asyncio
import json
import hashlib
from dataclasses import dataclass
from enum import Enum

from .logging_config import get_logger

logger = get_logger(__name__)

T = TypeVar('T')  # Type variable for cache values

class CachePolicy(Enum):
    """Cache policies for different types of data."""
    MEMORY = "memory"       # In-memory cache only
    PERSISTENT = "disk"     # Disk-based persistent cache
    DISTRIBUTED = "redis"   # Distributed cache (e.g., Redis)

@dataclass
class CacheEntry(Generic[T]):
    """Represents a cached item with metadata."""
    key: str
    value: T
    created_at: datetime
    expires_at: Optional[datetime]
    hits: int = 0
    last_accessed: Optional[datetime] = None
    size_bytes: int = 0

class CacheStrategy(Enum):
    """Cache eviction strategies."""
    LRU = "lru"    # Least Recently Used
    LFU = "lfu"    # Least Frequently Used
    FIFO = "fifo"  # First In First Out
    TTL = "ttl"    # Time To Live

class Cache(Generic[T]):
    """Generic cache implementation with multiple strategies."""
    
    def __init__(
        self,
        max_size: int = 1000,
        strategy: CacheStrategy = CacheStrategy.LRU,
        default_ttl: Optional[timedelta] = timedelta(hours=1)
    ):
        self.max_size = max_size
        self.strategy = strategy
        self.default_ttl = default_ttl
        self._cache: Dict[str, CacheEntry[T]] = {}
        self._cleanup_task: Optional[asyncio.Task] = None
        self.logger = get_logger(self.__class__.__name__)
    
    async def start(self) -> None:
        """Start cache maintenance tasks."""
        if not self._cleanup_task:
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())
            self.logger.info("Cache maintenance tasks started")
    
    async def stop(self) -> None:
        """Stop cache maintenance tasks."""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
            self._cleanup_task = None
            self.logger.info("Cache maintenance tasks stopped")
    
    def _generate_key(self, *args, **kwargs) -> str:
        """Generate a cache key from arguments."""
        key_parts = [str(arg) for arg in args]
        key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
        key_string = "|".join(key_parts)
        return hashlib.sha256(key_string.encode()).hexdigest()
    
    async def get(self, key: str) -> Optional[T]:
        """Get a value from the cache."""
        try:
            entry = self._cache.get(key)
            if not entry:
                return None
            
            # Check expiration
            if entry.expires_at and entry.expires_at <= datetime.now():
                del self._cache[key]
                return None
            
            # Update metadata
            entry.hits += 1
            entry.last_accessed = datetime.now()
            
            self.logger.debug(f"Cache hit for key: {key}")
            return entry.value
            
        except Exception as e:
            self.logger.error(f"Error retrieving from cache: {str(e)}")
            return None
    
    async def set(
        self,
        key: str,
        value: T,
        ttl: Optional[timedelta] = None
    ) -> None:
        """Set a value in the cache."""
        try:
            # Check cache size before adding
            if len(self._cache) >= self.max_size:
                await self._evict()
            
            # Calculate expiration time
            expires_at = None
            if ttl or self.default_ttl:
                expires_at = datetime.now() + (ttl or self.default_ttl)
            
            # Create cache entry
            entry = CacheEntry(
                key=key,
                value=value,
                created_at=datetime.now(),
                expires_at=expires_at,
                size_bytes=self._estimate_size(value)
            )
            
            self._cache[key] = entry
            self.logger.debug(f"Cached value for key: {key}")
            
        except Exception as e:
            self.logger.error(f"Error setting cache value: {str(e)}")
    
    async def invalidate(self, key: str) -> None:
        """Invalidate a cache entry."""
        try:
            if key in self._cache:
                del self._cache[key]
                self.logger.debug(f"Invalidated cache key: {key}")
        except Exception as e:
            self.logger.error(f"Error invalidating cache: {str(e)}")
    
    async def clear(self) -> None:
        """Clear all cache entries."""
        try:
            self._cache.clear()
            self.logger.info("Cache cleared")
        except Exception as e:
            self.logger.error(f"Error clearing cache: {str(e)}")
    
    def _estimate_size(self, value: T) -> int:
        """Estimate the size of a cached value in bytes."""
        try:
            if isinstance(value, (str, bytes)):
                return len(value)
            return len(json.dumps(value))
        except:
            return 0
    
    async def _cleanup_loop(self) -> None:
        """Periodic cleanup of expired entries."""
        while True:
            try:
                await self._cleanup_expired()
                await asyncio.sleep(60)  # Cleanup every minute
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in cache cleanup: {str(e)}")
                await asyncio.sleep(5)  # Brief pause before retry
    
    async def _cleanup_expired(self) -> None:
        """Remove expired cache entries."""
        now = datetime.now()
        expired_keys = [
            key
            for key, entry in self._cache.items()
            if entry.expires_at and entry.expires_at <= now
        ]
        
        for key in expired_keys:
            del self._cache[key]
        
        if expired_keys:
            self.logger.debug(f"Cleaned up {len(expired_keys)} expired cache entries")
    
    async def _evict(self) -> None:
        """Evict entries based on the chosen strategy."""
        if not self._cache:
            return
        
        if self.strategy == CacheStrategy.LRU:
            # Evict least recently accessed
            key_to_evict = min(
                self._cache.items(),
                key=lambda x: x[1].last_accessed or x[1].created_at
            )[0]
        
        elif self.strategy == CacheStrategy.LFU:
            # Evict least frequently used
            key_to_evict = min(
                self._cache.items(),
                key=lambda x: x[1].hits
            )[0]
        
        elif self.strategy == CacheStrategy.FIFO:
            # Evict oldest entry
            key_to_evict = min(
                self._cache.items(),
                key=lambda x: x[1].created_at
            )[0]
        
        else:  # TTL strategy
            # Evict nearest to expiration
            key_to_evict = min(
                self._cache.items(),
                key=lambda x: x[1].expires_at or datetime.max
            )[0]
        
        del self._cache[key_to_evict]
        self.logger.debug(f"Evicted cache key: {key_to_evict}")

def cached(
    ttl: Optional[timedelta] = None,
    key_generator: Optional[Callable[..., str]] = None
):
    """Decorator for caching function results."""
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        cache = Cache[T]()
        
        async def wrapper(*args, **kwargs) -> T:
            # Generate cache key
            if key_generator:
                key = key_generator(*args, **kwargs)
            else:
                key = cache._generate_key(*args, **kwargs)
            
            # Try to get from cache
            cached_value = await cache.get(key)
            if cached_value is not None:
                return cached_value
            
            # Calculate and cache result
            result = await func(*args, **kwargs)
            await cache.set(key, result, ttl)
            return result
        
        return wrapper
    return decorator
