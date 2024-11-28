"""System Monitoring and Optimization Service using specialized agents."""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List

from core.monitoring import MetricsCollector
from core.error_handling import ErrorHandler
from agents.memory_agent import MemoryAgent
from agents.resource_agent import ResourceAgent
from agents.coordinator_agent import CoordinatorAgent
from core.logging_config import get_logger

logger = get_logger(__name__)

class SystemMonitorService:
    """Service that monitors system health and optimizes performance."""
    
    def __init__(self):
        # Core components
        self.metrics = MetricsCollector()
        self.error_handler = ErrorHandler()
        
        # Specialized agents
        self.memory_agent = MemoryAgent(
            self.metrics,
            self.error_handler,
            working_memory_size=1000,
            long_term_memory_size=10000
        )
        
        self.resource_agent = ResourceAgent(
            self.metrics,
            self.error_handler,
            check_interval=5.0
        )
        
        self.coordinator = CoordinatorAgent(
            self.metrics,
            self.error_handler,
            max_concurrent_tasks=5
        )
        
        self._running = False
        self._monitoring_task: Any = None
    
    async def start(self) -> None:
        """Start the monitoring service."""
        logger.info("Starting System Monitor Service")
        
        # Start core components
        await self.metrics.start()
        await self.error_handler.start()
        
        # Start agents
        await self.memory_agent.start()
        await self.resource_agent.start()
        await self.coordinator.start()
        
        self._running = True
        self._monitoring_task = asyncio.create_task(self._monitoring_loop())
        
        logger.info("System Monitor Service started successfully")
    
    async def stop(self) -> None:
        """Stop the monitoring service."""
        logger.info("Stopping System Monitor Service")
        
        self._running = False
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass
        
        # Stop agents
        await self.coordinator.stop()
        await self.resource_agent.stop()
        await self.memory_agent.stop()
        
        # Stop core components
        await self.error_handler.stop()
        await self.metrics.stop()
        
        logger.info("System Monitor Service stopped successfully")
    
    async def _monitoring_loop(self) -> None:
        """Main monitoring loop that coordinates various tasks."""
        while self._running:
            try:
                # Schedule resource monitoring task
                await self.coordinator.submit_task(
                    name="monitor_resources",
                    coroutine=self._monitor_resources(),
                    priority=2
                )
                
                # Schedule memory consolidation task
                await self.coordinator.submit_task(
                    name="consolidate_memories",
                    coroutine=self._consolidate_memories(),
                    priority=1
                )
                
                # Schedule system optimization task
                await self.coordinator.submit_task(
                    name="optimize_system",
                    coroutine=self._optimize_system(),
                    priority=3
                )
                
                # Wait before next iteration
                await asyncio.sleep(60)  # Run main loop every minute
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(5)  # Brief pause before retry
    
    async def _monitor_resources(self) -> None:
        """Monitor system resources and store reports."""
        # Get resource report
        report = await self.resource_agent.get_resource_report()
        
        # Store in working memory
        timestamp = datetime.now().isoformat()
        await self.memory_agent.store_memory(
            f"resource_report_{timestamp}",
            report
        )
        
        # Check for critical conditions
        if self._is_critical_condition(report):
            # Store critical reports in long-term memory
            await self.memory_agent.store_memory(
                f"critical_report_{timestamp}",
                report,
                long_term=True
            )
            
            # Schedule immediate optimization
            await self.coordinator.submit_task(
                name="emergency_optimization",
                coroutine=self._emergency_optimize(),
                priority=4  # Highest priority
            )
    
    def _is_critical_condition(self, report: Dict[str, Any]) -> bool:
        """Check if system is in a critical condition."""
        return (
            report["cpu"]["status"] == "CRITICAL" or
            report["memory"]["status"] == "CRITICAL" or
            report["disk"]["status"] == "CRITICAL"
        )
    
    async def _consolidate_memories(self) -> None:
        """Consolidate important system metrics into long-term memory."""
        await self.memory_agent.consolidate_memories()
        
        # Clean up old working memory
        await self.memory_agent.cleanup_memories()
    
    async def _optimize_system(self) -> None:
        """Perform system optimization based on historical data."""
        # Get recent resource reports
        reports = await self.memory_agent.search_memories("resource_report")
        if not reports:
            return
        
        # Analyze trends and optimize
        await self._analyze_and_optimize(reports)
    
    async def _emergency_optimize(self) -> None:
        """Perform emergency optimization for critical conditions."""
        logger.warning("Performing emergency system optimization")
        
        # Get latest resource report
        report = await self.resource_agent.get_resource_report()
        
        # Perform specific optimizations based on the critical condition
        if report["cpu"]["status"] == "CRITICAL":
            await self._optimize_cpu_usage()
        
        if report["memory"]["status"] == "CRITICAL":
            await self._optimize_memory_usage()
        
        if report["disk"]["status"] == "CRITICAL":
            await self._optimize_disk_usage()
    
    async def _analyze_and_optimize(self, reports: List[Dict[str, Any]]) -> None:
        """Analyze resource trends and perform optimizations."""
        # Calculate average resource usage
        cpu_usage = sum(r["cpu"]["percent"] for r in reports) / len(reports)
        memory_usage = sum(r["memory"]["percent"] for r in reports) / len(reports)
        disk_usage = sum(r["disk"]["percent"] for r in reports) / len(reports)
        
        # Perform optimizations based on trends
        if cpu_usage > 70:
            await self._optimize_cpu_usage()
        
        if memory_usage > 70:
            await self._optimize_memory_usage()
        
        if disk_usage > 70:
            await self._optimize_disk_usage()
    
    async def _optimize_cpu_usage(self) -> None:
        """Optimize CPU usage."""
        logger.info("Optimizing CPU usage")
        # Implement CPU optimization logic here
        pass
    
    async def _optimize_memory_usage(self) -> None:
        """Optimize memory usage."""
        logger.info("Optimizing memory usage")
        # Implement memory optimization logic here
        pass
    
    async def _optimize_disk_usage(self) -> None:
        """Optimize disk usage."""
        logger.info("Optimizing disk usage")
        # Implement disk optimization logic here
        pass
    
    async def get_system_health(self) -> Dict[str, Any]:
        """Get overall system health report."""
        try:
            # Get latest resource metrics
            resource_report = await self.resource_agent.get_resource_report()
            
            # Get task metrics
            task_metrics = await self.coordinator.get_task_metrics()
            
            # Get memory stats
            memory_stats = await self.memory_agent.get_memory_stats()
            
            return {
                "timestamp": datetime.now().isoformat(),
                "resources": resource_report,
                "tasks": task_metrics,
                "memory": memory_stats,
                "overall_status": self._calculate_overall_status(
                    resource_report,
                    task_metrics,
                    memory_stats
                )
            }
            
        except Exception as e:
            logger.error(f"Error getting system health: {e}")
            return {}
    
    def _calculate_overall_status(
        self,
        resource_report: Dict[str, Any],
        task_metrics: Dict[str, Any],
        memory_stats: Dict[str, Any]
    ) -> str:
        """Calculate overall system status."""
        # Check for any critical conditions
        if (resource_report["cpu"]["status"] == "CRITICAL" or
            resource_report["memory"]["status"] == "CRITICAL" or
            resource_report["disk"]["status"] == "CRITICAL"):
            return "CRITICAL"
        
        # Check for warning conditions
        if (resource_report["cpu"]["status"] == "WARNING" or
            resource_report["memory"]["status"] == "WARNING" or
            resource_report["disk"]["status"] == "WARNING" or
            task_metrics["pending_tasks"] > 10):
            return "WARNING"
        
        # Check for elevated conditions
        if (resource_report["cpu"]["status"] == "ELEVATED" or
            resource_report["memory"]["status"] == "ELEVATED" or
            resource_report["disk"]["status"] == "ELEVATED" or
            task_metrics["pending_tasks"] > 5):
            return "ELEVATED"
        
        return "NORMAL"

async def main():
    """Run the system monitor service."""
    service = SystemMonitorService()
    
    try:
        await service.start()
        
        # Run for a while
        await asyncio.sleep(3600)  # Run for 1 hour
        
    except KeyboardInterrupt:
        logger.info("Received shutdown signal")
    finally:
        await service.stop()

if __name__ == "__main__":
    asyncio.run(main())
