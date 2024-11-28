"""Tests for caching system."""

import pytest
import asyncio
from datetime import datetime, timedelta

from core.caching import (
    Cache,
    CacheEntry,
    CacheStrategy,
    cached
)

@pytest.fixture
async def cache():
    """Create cache fixture."""
    cache = Cache[str](
        max_size=5,
        strategy=CacheStrategy.LRU,
        default_ttl=timedelta(seconds=1)
    )
    await cache.start()
    yield cache
    await cache.stop()

async def test_cache_set_get(cache):
    """Test basic cache set and get operations."""
    await cache.set("test_key", "test_value")
    value = await cache.get("test_key")
    assert value == "test_value"

async def test_cache_expiration(cache):
    """Test cache entry expiration."""
    await cache.set("test_key", "test_value", ttl=timedelta(milliseconds=100))
    
    # Value should exist initially
    value = await cache.get("test_key")
    assert value == "test_value"
    
    # Wait for expiration
    await asyncio.sleep(0.2)
    
    # Value should be None after expiration
    value = await cache.get("test_key")
    assert value is None

async def test_cache_max_size_lru(cache):
    """Test LRU eviction when cache is full."""
    # Fill cache
    for i in range(5):
        await cache.set(f"key_{i}", f"value_{i}")
    
    # Access key_0 to make it most recently used
    await cache.get("key_0")
    
    # Add new entry, should evict least recently used
    await cache.set("new_key", "new_value")
    
    # key_1 should be evicted (least recently used)
    assert await cache.get("key_1") is None
    assert await cache.get("key_0") == "value_0"
    assert await cache.get("new_key") == "new_value"

async def test_cache_invalidate(cache):
    """Test cache invalidation."""
    await cache.set("test_key", "test_value")
    await cache.invalidate("test_key")
    value = await cache.get("test_key")
    assert value is None

async def test_cache_clear(cache):
    """Test clearing all cache entries."""
    await cache.set("key1", "value1")
    await cache.set("key2", "value2")
    await cache.clear()
    
    assert await cache.get("key1") is None
    assert await cache.get("key2") is None

async def test_cache_decorator():
    """Test cache decorator."""
    call_count = 0
    
    @cached(ttl=timedelta(seconds=1))
    async def test_function(arg):
        nonlocal call_count
        call_count += 1
        return f"result_{arg}"
    
    # First call should execute function
    result1 = await test_function("test")
    assert result1 == "result_test"
    assert call_count == 1
    
    # Second call should use cached value
    result2 = await test_function("test")
    assert result2 == "result_test"
    assert call_count == 1
    
    # Different argument should execute function
    result3 = await test_function("other")
    assert result3 == "result_other"
    assert call_count == 2

async def test_cache_hit_tracking(cache):
    """Test cache hit counting."""
    await cache.set("test_key", "test_value")
    
    # Get value multiple times
    for _ in range(3):
        value = await cache.get("test_key")
        assert value == "test_value"
    
    # Check hit count
    entry = cache._cache["test_key"]
    assert entry.hits == 3

async def test_cache_size_estimation(cache):
    """Test cache size estimation."""
    # String value
    await cache.set("string_key", "test")
    assert cache._cache["string_key"].size_bytes == 4
    
    # Dictionary value
    await cache.set("dict_key", {"key": "value"})
    assert cache._cache["dict_key"].size_bytes > 0

async def test_different_cache_strategies():
    """Test different cache eviction strategies."""
    async def fill_and_check_eviction(strategy: CacheStrategy):
        cache = Cache[str](max_size=3, strategy=strategy)
        await cache.start()
        
        # Fill cache
        for i in range(3):
            await cache.set(f"key_{i}", f"value_{i}")
        
        if strategy == CacheStrategy.LRU:
            # Access first key to make it most recently used
            await cache.get("key_0")
            # Add new entry
            await cache.set("new_key", "new_value")
            # key_1 should be evicted (least recently used)
            assert await cache.get("key_1") is None
            assert await cache.get("key_0") == "value_0"
        
        elif strategy == CacheStrategy.FIFO:
            # Add new entry
            await cache.set("new_key", "new_value")
            # First key should be evicted
            assert await cache.get("key_0") is None
            assert await cache.get("key_1") == "value_1"
        
        await cache.stop()
    
    # Test LRU strategy
    await fill_and_check_eviction(CacheStrategy.LRU)
    
    # Test FIFO strategy
    await fill_and_check_eviction(CacheStrategy.FIFO)

async def test_cache_cleanup(cache):
    """Test automatic cleanup of expired entries."""
    # Add entries with short TTL
    await cache.set("key1", "value1", ttl=timedelta(milliseconds=100))
    await cache.set("key2", "value2", ttl=timedelta(seconds=10))
    
    # Wait for first entry to expire
    await asyncio.sleep(0.2)
    
    # Trigger cleanup
    await cache._cleanup_expired()
    
    # Check results
    assert await cache.get("key1") is None  # Should be cleaned up
    assert await cache.get("key2") == "value2"  # Should still exist
