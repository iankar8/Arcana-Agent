"""Memory Management Agent for handling long-term and working memory."""

from typing import Dict, Any, Optional, List
from datetime import timedelta
import asyncio
import json

from core.interfaces import Agent
from core.caching import Cache, CacheStrategy
from core.monitoring import MetricsCollector, MetricType, Timer
from core.error_handling import ErrorHandler, ErrorCategory, RecoveryStrategy
from core.logging_config import get_logger

logger = get_logger(__name__)

class MemoryAgent(Agent):
    """Agent responsible for managing system memory and knowledge persistence."""
    
    def __init__(
        self,
        metrics_collector: MetricsCollector,
        error_handler: ErrorHandler,
        working_memory_size: int = 1000,
        long_term_memory_size: int = 10000
    ):
        self.metrics = metrics_collector
        self.error_handler = error_handler
        
        # Configure memory caches
        self.working_memory = Cache[Dict[str, Any]](
            max_size=working_memory_size,
            strategy=CacheStrategy.LRU,
            default_ttl=timedelta(hours=1)
        )
        
        self.long_term_memory = Cache[Dict[str, Any]](
            max_size=long_term_memory_size,
            strategy=CacheStrategy.LFU,
            default_ttl=timedelta(days=30)
        )
        
        # Set up error handling
        self.error_handler.set_recovery_strategy(
            ErrorCategory.RESOURCE,
            RecoveryStrategy.CIRCUIT_BREAK
        )
        
        self.logger = get_logger(self.__class__.__name__)
    
    async def start(self) -> None:
        """Start memory management systems."""
        await self.working_memory.start()
        await self.long_term_memory.start()
        self.logger.info("Memory management systems started")
    
    async def stop(self) -> None:
        """Stop memory management systems."""
        await self.working_memory.stop()
        await self.long_term_memory.stop()
        self.logger.info("Memory management systems stopped")
    
    async def store_memory(
        self,
        key: str,
        data: Dict[str, Any],
        long_term: bool = False,
        ttl: Optional[timedelta] = None
    ) -> None:
        """Store data in memory."""
        try:
            async with Timer(
                "memory_store",
                "memory_agent",
                self.metrics,
                {"type": "long_term" if long_term else "working"}
            ):
                cache = self.long_term_memory if long_term else self.working_memory
                await cache.set(key, data, ttl)
                
                self.metrics.record(
                    name="memory_store_size_bytes",
                    value=len(json.dumps(data)),
                    metric_type=MetricType.HISTOGRAM,
                    component="memory_agent",
                    labels={"memory_type": "long_term" if long_term else "working"}
                )
                
        except Exception as e:
            await self.error_handler.handle_error(
                e,
                {
                    "component": "memory_agent",
                    "operation": "store",
                    "key": key,
                    "memory_type": "long_term" if long_term else "working"
                }
            )
    
    async def retrieve_memory(
        self,
        key: str,
        long_term: bool = False
    ) -> Optional[Dict[str, Any]]:
        """Retrieve data from memory."""
        try:
            async with Timer(
                "memory_retrieve",
                "memory_agent",
                self.metrics,
                {"type": "long_term" if long_term else "working"}
            ):
                cache = self.long_term_memory if long_term else self.working_memory
                data = await cache.get(key)
                
                if data is not None:
                    self.metrics.record(
                        name="memory_hits",
                        value=1,
                        metric_type=MetricType.COUNTER,
                        component="memory_agent",
                        labels={"memory_type": "long_term" if long_term else "working"}
                    )
                else:
                    self.metrics.record(
                        name="memory_misses",
                        value=1,
                        metric_type=MetricType.COUNTER,
                        component="memory_agent",
                        labels={"memory_type": "long_term" if long_term else "working"}
                    )
                
                return data
                
        except Exception as e:
            await self.error_handler.handle_error(
                e,
                {
                    "component": "memory_agent",
                    "operation": "retrieve",
                    "key": key,
                    "memory_type": "long_term" if long_term else "working"
                }
            )
            return None
    
    async def consolidate_memories(self) -> None:
        """Move important working memories to long-term storage."""
        try:
            async with Timer(
                "memory_consolidation",
                "memory_agent",
                self.metrics
            ):
                # Get frequently accessed working memories
                working_entries = self.working_memory._cache
                
                for key, entry in working_entries.items():
                    # If memory has been accessed frequently, store in long-term
                    if entry.hits >= 5:
                        await self.store_memory(
                            key,
                            entry.value,
                            long_term=True,
                            ttl=timedelta(days=30)
                        )
                        
                        self.metrics.record(
                            name="memory_consolidations",
                            value=1,
                            metric_type=MetricType.COUNTER,
                            component="memory_agent"
                        )
                
        except Exception as e:
            await self.error_handler.handle_error(
                e,
                {
                    "component": "memory_agent",
                    "operation": "consolidate"
                }
            )
    
    async def search_memories(
        self,
        pattern: str,
        long_term: bool = False
    ) -> List[Dict[str, Any]]:
        """Search memories using a pattern."""
        try:
            async with Timer(
                "memory_search",
                "memory_agent",
                self.metrics,
                {"type": "long_term" if long_term else "working"}
            ):
                cache = self.long_term_memory if long_term else self.working_memory
                results = []
                pattern = pattern.lower()
                
                for key, entry in cache._cache.items():
                    # Search in both key and value
                    if (pattern in key.lower() or 
                        pattern in json.dumps(entry.value).lower()):
                        results.append(entry.value)
                
                self.metrics.record(
                    name="memory_search_results",
                    value=len(results),
                    metric_type=MetricType.HISTOGRAM,
                    component="memory_agent",
                    labels={"memory_type": "long_term" if long_term else "working"}
                )
                
                return results
                
        except Exception as e:
            await self.error_handler.handle_error(
                e,
                {
                    "component": "memory_agent",
                    "operation": "search",
                    "pattern": pattern,
                    "memory_type": "long_term" if long_term else "working"
                }
            )
            return []
    
    async def cleanup_memories(self) -> None:
        """Clean up old or unused memories."""
        try:
            async with Timer(
                "memory_cleanup",
                "memory_agent",
                self.metrics
            ):
                # Clean working memory more aggressively
                await self.working_memory._cleanup_expired()
                await self.long_term_memory._cleanup_expired()
                
                self.metrics.record(
                    name="memory_cleanup",
                    value=1,
                    metric_type=MetricType.COUNTER,
                    component="memory_agent"
                )
                
        except Exception as e:
            await self.error_handler.handle_error(
                e,
                {
                    "component": "memory_agent",
                    "operation": "cleanup"
                }
            )
    
    async def get_memory_stats(self) -> Dict[str, Any]:
        """Get memory usage statistics."""
        try:
            working_size = len(self.working_memory._cache)
            long_term_size = len(self.long_term_memory._cache)
            
            stats = {
                "working_memory_size": working_size,
                "long_term_memory_size": long_term_size,
                "working_memory_utilization": working_size / self.working_memory.max_size,
                "long_term_memory_utilization": long_term_size / self.long_term_memory.max_size
            }
            
            # Record metrics
            for name, value in stats.items():
                self.metrics.record(
                    name=f"memory_{name}",
                    value=value,
                    metric_type=MetricType.GAUGE,
                    component="memory_agent"
                )
            
            return stats
            
        except Exception as e:
            await self.error_handler.handle_error(
                e,
                {
                    "component": "memory_agent",
                    "operation": "get_stats"
                }
            )
            return {}
