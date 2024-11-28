"""Monitoring and metrics collection system for Arcana Agent Framework."""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import asyncio
import json
import statistics
from dataclasses import dataclass, asdict
from enum import Enum
import psutil
import time

from .logging_config import get_logger

logger = get_logger(__name__)

class MetricType(Enum):
    """Types of metrics that can be collected."""
    COUNTER = "counter"      # Monotonically increasing value
    GAUGE = "gauge"          # Value that can go up or down
    HISTOGRAM = "histogram"  # Distribution of values
    TIMER = "timer"         # Duration measurements

@dataclass
class Metric:
    """Represents a single metric measurement."""
    name: str
    type: MetricType
    value: float
    timestamp: datetime
    labels: Dict[str, str]
    component: str

@dataclass
class SystemMetrics:
    """System-level metrics."""
    cpu_percent: float
    memory_percent: float
    disk_usage_percent: float
    open_files: int
    thread_count: int
    timestamp: datetime

class MetricsAggregator:
    """Aggregates metrics over time windows."""
    
    def __init__(self, window_size: timedelta = timedelta(minutes=1)):
        self.window_size = window_size
        self.metrics: Dict[str, List[Metric]] = {}
        self.logger = get_logger(self.__class__.__name__)
    
    def add_metric(self, metric: Metric) -> None:
        """Add a metric to the aggregator."""
        if metric.name not in self.metrics:
            self.metrics[metric.name] = []
        
        # Add new metric
        self.metrics[metric.name].append(metric)
        
        # Remove old metrics
        cutoff = datetime.now() - self.window_size
        self.metrics[metric.name] = [
            m for m in self.metrics[metric.name]
            if m.timestamp > cutoff
        ]
    
    def get_statistics(self, metric_name: str) -> Dict[str, float]:
        """Get statistical summary of a metric."""
        if metric_name not in self.metrics:
            return {}
        
        values = [m.value for m in self.metrics[metric_name]]
        if not values:
            return {}
        
        stats = {
            "count": len(values),
            "min": min(values),
            "max": max(values),
            "mean": statistics.mean(values),
            "median": statistics.median(values),
            "sum": sum(values)
        }
        
        try:
            stats["stddev"] = statistics.stdev(values)
        except statistics.StatisticsError:
            stats["stddev"] = 0.0
        
        return stats

class MetricsCollector:
    """Collects and manages metrics."""
    
    def __init__(
        self,
        aggregation_window: timedelta = timedelta(minutes=1),
        system_metrics_interval: float = 60.0
    ):
        self.aggregator = MetricsAggregator(aggregation_window)
        self.system_metrics_interval = system_metrics_interval
        self._running = False
        self._system_metrics_task: Optional[asyncio.Task] = None
        self.logger = get_logger(self.__class__.__name__)
    
    async def start(self) -> None:
        """Start metrics collection."""
        if self._running:
            return
        
        self._running = True
        self._system_metrics_task = asyncio.create_task(
            self._collect_system_metrics()
        )
        self.logger.info("Metrics collector started")
    
    async def stop(self) -> None:
        """Stop metrics collection."""
        self._running = False
        if self._system_metrics_task:
            self._system_metrics_task.cancel()
            try:
                await self._system_metrics_task
            except asyncio.CancelledError:
                pass
        self.logger.info("Metrics collector stopped")
    
    def record(
        self,
        name: str,
        value: float,
        metric_type: MetricType,
        component: str,
        labels: Optional[Dict[str, str]] = None
    ) -> None:
        """Record a metric."""
        metric = Metric(
            name=name,
            type=metric_type,
            value=value,
            timestamp=datetime.now(),
            labels=labels or {},
            component=component
        )
        self.aggregator.add_metric(metric)
    
    async def _collect_system_metrics(self) -> None:
        """Collect system metrics periodically."""
        while self._running:
            try:
                metrics = self._get_system_metrics()
                self._record_system_metrics(metrics)
                self.logger.debug(f"Collected system metrics: {metrics}")
                await asyncio.sleep(self.system_metrics_interval)
            except Exception as e:
                self.logger.error(f"Error collecting system metrics: {str(e)}")
                await asyncio.sleep(1)  # Brief pause before retry
    
    def _get_system_metrics(self) -> SystemMetrics:
        """Get current system metrics."""
        return SystemMetrics(
            cpu_percent=psutil.cpu_percent(),
            memory_percent=psutil.virtual_memory().percent,
            disk_usage_percent=psutil.disk_usage('/').percent,
            open_files=len(psutil.Process().open_files()),
            thread_count=psutil.Process().num_threads(),
            timestamp=datetime.now()
        )
    
    def _record_system_metrics(self, metrics: SystemMetrics) -> None:
        """Record system metrics."""
        system_metrics = asdict(metrics)
        del system_metrics['timestamp']  # Remove timestamp from labels
        
        for name, value in system_metrics.items():
            self.record(
                name=f"system_{name}",
                value=float(value),
                metric_type=MetricType.GAUGE,
                component="system",
                labels={"host": "localhost"}
            )

class MetricsExporter:
    """Exports metrics in various formats."""
    
    def __init__(self, collector: MetricsCollector):
        self.collector = collector
        self.logger = get_logger(self.__class__.__name__)
    
    def export_json(self) -> str:
        """Export metrics as JSON."""
        metrics_dict = {
            name: self.collector.aggregator.get_statistics(name)
            for name in self.collector.aggregator.metrics.keys()
        }
        return json.dumps(metrics_dict, indent=2)
    
    def export_prometheus(self) -> str:
        """Export metrics in Prometheus format."""
        lines = []
        for name, metrics in self.collector.aggregator.metrics.items():
            if not metrics:
                continue
            
            # Add metric help and type
            lines.append(f"# HELP {name} {name}")
            lines.append(f"# TYPE {name} {metrics[0].type.value}")
            
            # Add metric values
            for metric in metrics:
                labels = ",".join(
                    f'{k}="{v}"'
                    for k, v in metric.labels.items()
                )
                if labels:
                    lines.append(f'{name}{{{labels}}} {metric.value}')
                else:
                    lines.append(f'{name} {metric.value}')
        
        return "\n".join(lines)

class Timer:
    """Context manager for timing operations."""
    
    def __init__(
        self,
        name: str,
        component: str,
        collector: MetricsCollector,
        labels: Optional[Dict[str, str]] = None
    ):
        self.name = name
        self.component = component
        self.collector = collector
        self.labels = labels or {}
        self.start_time: Optional[float] = None
        self.logger = get_logger(self.__class__.__name__)
    
    async def __aenter__(self) -> 'Timer':
        """Enter async context manager."""
        self.start_time = time.time()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit async context manager."""
        if self.start_time is None:
            return
        
        duration = time.time() - self.start_time
        self.collector.record(
            name=f"{self.name}_duration_seconds",
            value=duration,
            metric_type=MetricType.TIMER,
            component=self.component,
            labels=self.labels
        )
        
        if exc_type is not None:
            self.collector.record(
                name=f"{self.name}_errors_total",
                value=1,
                metric_type=MetricType.COUNTER,
                component=self.component,
                labels=self.labels
            )
