"""Resource Management Agent for handling system resources and performance."""

from typing import Dict, Any, Optional, List
import asyncio
import psutil
from datetime import datetime, timedelta

from core.interfaces import Agent
from core.monitoring import MetricsCollector, MetricType, Timer
from core.error_handling import ErrorHandler, ErrorCategory, RecoveryStrategy
from core.logging_config import get_logger

logger = get_logger(__name__)

class ResourceThresholds:
    """Resource usage thresholds."""
    CPU_HIGH = 80.0
    CPU_CRITICAL = 90.0
    MEMORY_HIGH = 80.0
    MEMORY_CRITICAL = 90.0
    DISK_HIGH = 80.0
    DISK_CRITICAL = 90.0

class ResourceAgent(Agent):
    """Agent responsible for monitoring and managing system resources."""
    
    def __init__(
        self,
        metrics_collector: MetricsCollector,
        error_handler: ErrorHandler,
        check_interval: float = 5.0
    ):
        self.metrics = metrics_collector
        self.error_handler = error_handler
        self.check_interval = check_interval
        self._monitoring_task: Optional[asyncio.Task] = None
        self._running = False
        
        # Configure error handling
        self.error_handler.set_recovery_strategy(
            ErrorCategory.RESOURCE,
            RecoveryStrategy.CIRCUIT_BREAK
        )
        
        self.logger = get_logger(self.__class__.__name__)
    
    async def start(self) -> None:
        """Start resource monitoring."""
        if self._running:
            return
        
        self._running = True
        self._monitoring_task = asyncio.create_task(self._monitor_resources())
        self.logger.info("Resource monitoring started")
    
    async def stop(self) -> None:
        """Stop resource monitoring."""
        self._running = False
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass
        self.logger.info("Resource monitoring stopped")
    
    async def _monitor_resources(self) -> None:
        """Monitor system resources periodically."""
        while self._running:
            try:
                async with Timer(
                    "resource_check",
                    "resource_agent",
                    self.metrics
                ):
                    await self._check_resources()
                    await self._handle_resource_issues()
                
                await asyncio.sleep(self.check_interval)
                
            except Exception as e:
                await self.error_handler.handle_error(
                    e,
                    {
                        "component": "resource_agent",
                        "operation": "monitor"
                    }
                )
                await asyncio.sleep(1)  # Brief pause before retry
    
    async def _check_resources(self) -> None:
        """Check current resource usage."""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            self.metrics.record(
                name="system_cpu_percent",
                value=cpu_percent,
                metric_type=MetricType.GAUGE,
                component="resource_agent"
            )
            
            # Memory usage
            memory = psutil.virtual_memory()
            self.metrics.record(
                name="system_memory_percent",
                value=memory.percent,
                metric_type=MetricType.GAUGE,
                component="resource_agent"
            )
            
            # Disk usage
            disk = psutil.disk_usage('/')
            self.metrics.record(
                name="system_disk_percent",
                value=disk.percent,
                metric_type=MetricType.GAUGE,
                component="resource_agent"
            )
            
            # Process information
            process = psutil.Process()
            self.metrics.record(
                name="system_open_files",
                value=len(process.open_files()),
                metric_type=MetricType.GAUGE,
                component="resource_agent"
            )
            self.metrics.record(
                name="system_threads",
                value=process.num_threads(),
                metric_type=MetricType.GAUGE,
                component="resource_agent"
            )
            
        except Exception as e:
            await self.error_handler.handle_error(
                e,
                {
                    "component": "resource_agent",
                    "operation": "check_resources"
                }
            )
    
    async def _handle_resource_issues(self) -> None:
        """Handle resource usage issues."""
        try:
            cpu_percent = psutil.cpu_percent()
            memory_percent = psutil.virtual_memory().percent
            disk_percent = psutil.disk_usage('/').percent
            
            # Check CPU usage
            if cpu_percent >= ResourceThresholds.CPU_CRITICAL:
                await self._handle_critical_cpu()
            elif cpu_percent >= ResourceThresholds.CPU_HIGH:
                await self._handle_high_cpu()
            
            # Check memory usage
            if memory_percent >= ResourceThresholds.MEMORY_CRITICAL:
                await self._handle_critical_memory()
            elif memory_percent >= ResourceThresholds.MEMORY_HIGH:
                await self._handle_high_memory()
            
            # Check disk usage
            if disk_percent >= ResourceThresholds.DISK_CRITICAL:
                await self._handle_critical_disk()
            elif disk_percent >= ResourceThresholds.DISK_HIGH:
                await self._handle_high_disk()
            
        except Exception as e:
            await self.error_handler.handle_error(
                e,
                {
                    "component": "resource_agent",
                    "operation": "handle_issues"
                }
            )
    
    async def _handle_critical_cpu(self) -> None:
        """Handle critical CPU usage."""
        self.logger.critical("Critical CPU usage detected")
        self.metrics.record(
            name="resource_critical_events",
            value=1,
            metric_type=MetricType.COUNTER,
            component="resource_agent",
            labels={"type": "cpu"}
        )
        # Implement CPU throttling or task suspension logic here
    
    async def _handle_high_cpu(self) -> None:
        """Handle high CPU usage."""
        self.logger.warning("High CPU usage detected")
        self.metrics.record(
            name="resource_warning_events",
            value=1,
            metric_type=MetricType.COUNTER,
            component="resource_agent",
            labels={"type": "cpu"}
        )
        # Implement CPU optimization logic here
    
    async def _handle_critical_memory(self) -> None:
        """Handle critical memory usage."""
        self.logger.critical("Critical memory usage detected")
        self.metrics.record(
            name="resource_critical_events",
            value=1,
            metric_type=MetricType.COUNTER,
            component="resource_agent",
            labels={"type": "memory"}
        )
        # Implement emergency memory cleanup logic here
    
    async def _handle_high_memory(self) -> None:
        """Handle high memory usage."""
        self.logger.warning("High memory usage detected")
        self.metrics.record(
            name="resource_warning_events",
            value=1,
            metric_type=MetricType.COUNTER,
            component="resource_agent",
            labels={"type": "memory"}
        )
        # Implement memory optimization logic here
    
    async def _handle_critical_disk(self) -> None:
        """Handle critical disk usage."""
        self.logger.critical("Critical disk usage detected")
        self.metrics.record(
            name="resource_critical_events",
            value=1,
            metric_type=MetricType.COUNTER,
            component="resource_agent",
            labels={"type": "disk"}
        )
        # Implement emergency disk cleanup logic here
    
    async def _handle_high_disk(self) -> None:
        """Handle high disk usage."""
        self.logger.warning("High disk usage detected")
        self.metrics.record(
            name="resource_warning_events",
            value=1,
            metric_type=MetricType.COUNTER,
            component="resource_agent",
            labels={"type": "disk"}
        )
        # Implement disk optimization logic here
    
    async def get_resource_report(self) -> Dict[str, Any]:
        """Get a comprehensive resource usage report."""
        try:
            cpu_percent = psutil.cpu_percent()
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            process = psutil.Process()
            
            report = {
                "timestamp": datetime.now().isoformat(),
                "cpu": {
                    "percent": cpu_percent,
                    "count": psutil.cpu_count(),
                    "status": self._get_resource_status(cpu_percent)
                },
                "memory": {
                    "percent": memory.percent,
                    "available": memory.available,
                    "total": memory.total,
                    "status": self._get_resource_status(memory.percent)
                },
                "disk": {
                    "percent": disk.percent,
                    "free": disk.free,
                    "total": disk.total,
                    "status": self._get_resource_status(disk.percent)
                },
                "process": {
                    "open_files": len(process.open_files()),
                    "threads": process.num_threads(),
                    "memory_percent": process.memory_percent()
                }
            }
            
            return report
            
        except Exception as e:
            await self.error_handler.handle_error(
                e,
                {
                    "component": "resource_agent",
                    "operation": "get_report"
                }
            )
            return {}
    
    def _get_resource_status(self, percent: float) -> str:
        """Get resource status based on usage percentage."""
        if percent >= 90:
            return "CRITICAL"
        elif percent >= 80:
            return "WARNING"
        elif percent >= 70:
            return "ELEVATED"
        else:
            return "NORMAL"
