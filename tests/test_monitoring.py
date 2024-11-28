"""Tests for monitoring system."""

import pytest
import asyncio
from datetime import datetime, timedelta
import json

from core.monitoring import (
    MetricsCollector,
    MetricType,
    Metric,
    SystemMetrics,
    MetricsAggregator,
    MetricsExporter,
    Timer
)

@pytest.fixture
async def metrics_collector():
    """Create metrics collector fixture."""
    collector = MetricsCollector(
        aggregation_window=timedelta(minutes=1),
        system_metrics_interval=0.1
    )
    await collector.start()
    yield collector
    await collector.stop()

@pytest.fixture
def metrics_aggregator():
    """Create metrics aggregator fixture."""
    return MetricsAggregator(window_size=timedelta(minutes=1))

@pytest.fixture
def metrics_exporter(metrics_collector):
    """Create metrics exporter fixture."""
    return MetricsExporter(metrics_collector)

async def test_record_counter(metrics_collector):
    """Test recording counter metrics."""
    metrics_collector.record(
        name="test_counter",
        value=1,
        metric_type=MetricType.COUNTER,
        component="test",
        labels={"type": "test"}
    )
    
    stats = metrics_collector.aggregator.get_statistics("test_counter")
    assert stats["count"] == 1
    assert stats["sum"] == 1

async def test_record_gauge(metrics_collector):
    """Test recording gauge metrics."""
    metrics_collector.record(
        name="test_gauge",
        value=42.0,
        metric_type=MetricType.GAUGE,
        component="test"
    )
    
    stats = metrics_collector.aggregator.get_statistics("test_gauge")
    assert stats["min"] == 42.0
    assert stats["max"] == 42.0

async def test_record_histogram(metrics_collector):
    """Test recording histogram metrics."""
    values = [1.0, 2.0, 3.0, 4.0, 5.0]
    
    for value in values:
        metrics_collector.record(
            name="test_histogram",
            value=value,
            metric_type=MetricType.HISTOGRAM,
            component="test"
        )
    
    stats = metrics_collector.aggregator.get_statistics("test_histogram")
    assert stats["count"] == 5
    assert stats["min"] == 1.0
    assert stats["max"] == 5.0
    assert stats["mean"] == 3.0

async def test_system_metrics_collection(metrics_collector):
    """Test system metrics collection."""
    # Wait for system metrics collection
    await asyncio.sleep(0.2)
    
    # Check system metrics
    cpu_stats = metrics_collector.aggregator.get_statistics("system_cpu_percent")
    assert cpu_stats["count"] >= 1
    
    memory_stats = metrics_collector.aggregator.get_statistics("system_memory_percent")
    assert memory_stats["count"] >= 1

async def test_metrics_aggregation(metrics_aggregator):
    """Test metrics aggregation."""
    # Add test metrics
    for i in range(5):
        metric = Metric(
            name="test_metric",
            type=MetricType.COUNTER,
            value=float(i),
            timestamp=datetime.now(),
            labels={},
            component="test"
        )
        metrics_aggregator.add_metric(metric)
    
    # Check statistics
    stats = metrics_aggregator.get_statistics("test_metric")
    assert stats["count"] == 5
    assert stats["min"] == 0.0
    assert stats["max"] == 4.0
    assert stats["mean"] == 2.0

async def test_metrics_window(metrics_aggregator):
    """Test metrics window behavior."""
    # Add old metric
    old_metric = Metric(
        name="test_metric",
        type=MetricType.COUNTER,
        value=1.0,
        timestamp=datetime.now() - timedelta(minutes=2),
        labels={},
        component="test"
    )
    metrics_aggregator.add_metric(old_metric)
    
    # Add new metric
    new_metric = Metric(
        name="test_metric",
        type=MetricType.COUNTER,
        value=2.0,
        timestamp=datetime.now(),
        labels={},
        component="test"
    )
    metrics_aggregator.add_metric(new_metric)
    
    # Only new metric should be in window
    stats = metrics_aggregator.get_statistics("test_metric")
    assert stats["count"] == 1
    assert stats["min"] == 2.0
    assert stats["max"] == 2.0

async def test_json_export(metrics_collector, metrics_exporter):
    """Test JSON metrics export."""
    metrics_collector.record(
        name="test_metric",
        value=42.0,
        metric_type=MetricType.GAUGE,
        component="test"
    )
    
    json_output = metrics_exporter.export_json()
    data = json.loads(json_output)
    
    assert "test_metric" in data
    assert data["test_metric"]["count"] == 1
    assert data["test_metric"]["min"] == 42.0
    assert data["test_metric"]["max"] == 42.0

async def test_prometheus_export(metrics_collector, metrics_exporter):
    """Test Prometheus format metrics export."""
    metrics_collector.record(
        name="test_counter",
        value=1,
        metric_type=MetricType.COUNTER,
        component="test",
        labels={"type": "test"}
    )
    
    prometheus_output = metrics_exporter.export_prometheus()
    
    assert "# HELP test_counter" in prometheus_output
    assert "# TYPE test_counter counter" in prometheus_output
    assert 'test_counter{type="test"}' in prometheus_output

async def test_timer_context_manager(metrics_collector):
    """Test timer context manager."""
    async with Timer(
        name="test_operation",
        component="test",
        collector=metrics_collector
    ):
        await asyncio.sleep(0.1)
    
    stats = metrics_collector.aggregator.get_statistics("test_operation_duration_seconds")
    assert stats["count"] == 1
    assert 0.1 <= stats["min"] <= 0.2

async def test_timer_with_error(metrics_collector):
    """Test timer with error."""
    with pytest.raises(ValueError):
        async with Timer(
            name="test_operation",
            component="test",
            collector=metrics_collector
        ):
            raise ValueError("test error")
    
    error_stats = metrics_collector.aggregator.get_statistics("test_operation_errors_total")
    assert error_stats["count"] == 1
    assert error_stats["sum"] == 1
