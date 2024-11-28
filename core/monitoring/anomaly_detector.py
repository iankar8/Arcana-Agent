"""Anomaly detection for workflow execution in Arcana."""

from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timedelta
import statistics
from dataclasses import dataclass
import json
import numpy as np
from enum import Enum

from core.monitoring import MetricsCollector
from core.error_handling import ErrorHandler
from core.feedback_loop import FeedbackLoop, FeedbackLevel

class AnomalyType(Enum):
    """Types of anomalies that can be detected."""
    
    DURATION = "duration"
    PATTERN = "pattern"
    VALUE = "value"
    FREQUENCY = "frequency"
    RESOURCE = "resource"

@dataclass
class AnomalyConfig:
    """Configuration for anomaly detection."""
    
    # Duration thresholds
    duration_threshold_factor: float = 2.0  # Multiple of average duration
    min_duration_samples: int = 5
    
    # Value thresholds
    value_zscore_threshold: float = 3.0
    min_value_samples: int = 10
    
    # Pattern detection
    pattern_window_size: int = 5
    pattern_similarity_threshold: float = 0.8
    
    # Resource thresholds
    memory_threshold_mb: float = 1000.0
    cpu_threshold_percent: float = 80.0

@dataclass
class Anomaly:
    """Represents a detected anomaly."""
    
    type: AnomalyType
    workflow_id: str
    step_id: Optional[str]
    timestamp: datetime
    description: str
    severity: float  # 0.0 to 1.0
    data: Dict[str, Any]

class AnomalyDetector:
    """Detects anomalies in workflow execution."""
    
    def __init__(
        self,
        metrics_collector: MetricsCollector,
        error_handler: Optional[ErrorHandler] = None,
        feedback_loop: Optional[FeedbackLoop] = None,
        config: Optional[AnomalyConfig] = None
    ):
        self.metrics = metrics_collector
        self.error_handler = error_handler
        self.feedback_loop = feedback_loop
        self.config = config or AnomalyConfig()
        
        # Historical data for analysis
        self._duration_history: Dict[str, List[float]] = {}
        self._value_history: Dict[str, List[float]] = {}
        self._pattern_history: Dict[str, List[Dict[str, Any]]] = {}
        self._detected_anomalies: List[Anomaly] = []
        
    async def analyze_step(
        self,
        workflow_id: str,
        step_id: str,
        metrics: Dict[str, Any]
    ) -> List[Anomaly]:
        """Analyze a workflow step for anomalies."""
        anomalies = []
        
        try:
            # Check duration anomalies
            if "duration" in metrics:
                duration_anomaly = self._check_duration_anomaly(
                    workflow_id,
                    step_id,
                    metrics["duration"]
                )
                if duration_anomaly:
                    anomalies.append(duration_anomaly)
                    
            # Check value anomalies
            if "output_value" in metrics:
                value_anomaly = self._check_value_anomaly(
                    workflow_id,
                    step_id,
                    metrics["output_value"]
                )
                if value_anomaly:
                    anomalies.append(value_anomaly)
                    
            # Check pattern anomalies
            pattern_anomaly = self._check_pattern_anomaly(
                workflow_id,
                step_id,
                metrics
            )
            if pattern_anomaly:
                anomalies.append(pattern_anomaly)
                
            # Check resource usage
            if "memory_mb" in metrics or "cpu_percent" in metrics:
                resource_anomaly = self._check_resource_anomaly(
                    workflow_id,
                    step_id,
                    metrics
                )
                if resource_anomaly:
                    anomalies.append(resource_anomaly)
                    
            # Record anomalies
            self._detected_anomalies.extend(anomalies)
            
            # Notify via feedback loop
            if anomalies and self.feedback_loop:
                await self._notify_anomalies(workflow_id, anomalies)
                
        except Exception as e:
            if self.error_handler:
                await self.error_handler.handle_error(
                    e,
                    {
                        "component": "AnomalyDetector",
                        "operation": "analyze_step",
                        "workflow_id": workflow_id,
                        "step_id": step_id
                    }
                )
            raise
            
        return anomalies
    
    def _check_duration_anomaly(
        self,
        workflow_id: str,
        step_id: str,
        duration: float
    ) -> Optional[Anomaly]:
        """Check for duration-based anomalies."""
        key = f"{workflow_id}:{step_id}"
        
        if key not in self._duration_history:
            self._duration_history[key] = []
            
        history = self._duration_history[key]
        history.append(duration)
        
        if len(history) >= self.config.min_duration_samples:
            avg_duration = statistics.mean(history)
            if duration > avg_duration * self.config.duration_threshold_factor:
                return Anomaly(
                    type=AnomalyType.DURATION,
                    workflow_id=workflow_id,
                    step_id=step_id,
                    timestamp=datetime.now(),
                    description=f"Step duration {duration:.2f}s exceeds threshold "
                              f"(avg: {avg_duration:.2f}s)",
                    severity=min(duration / avg_duration - 1, 1.0),
                    data={
                        "duration": duration,
                        "average": avg_duration,
                        "threshold": self.config.duration_threshold_factor
                    }
                )
        return None
    
    def _check_value_anomaly(
        self,
        workflow_id: str,
        step_id: str,
        value: float
    ) -> Optional[Anomaly]:
        """Check for value-based anomalies using Z-score."""
        key = f"{workflow_id}:{step_id}"
        
        if key not in self._value_history:
            self._value_history[key] = []
            
        history = self._value_history[key]
        history.append(value)
        
        if len(history) >= self.config.min_value_samples:
            zscore = abs(
                (value - statistics.mean(history))
                / statistics.stdev(history)
            )
            if zscore > self.config.value_zscore_threshold:
                return Anomaly(
                    type=AnomalyType.VALUE,
                    workflow_id=workflow_id,
                    step_id=step_id,
                    timestamp=datetime.now(),
                    description=f"Value {value} is {zscore:.2f} standard deviations "
                              f"from mean",
                    severity=min(zscore / self.config.value_zscore_threshold, 1.0),
                    data={
                        "value": value,
                        "zscore": zscore,
                        "threshold": self.config.value_zscore_threshold
                    }
                )
        return None
    
    def _check_pattern_anomaly(
        self,
        workflow_id: str,
        step_id: str,
        metrics: Dict[str, Any]
    ) -> Optional[Anomaly]:
        """Check for pattern-based anomalies."""
        key = f"{workflow_id}:{step_id}"
        
        if key not in self._pattern_history:
            self._pattern_history[key] = []
            
        history = self._pattern_history[key]
        history.append(metrics)
        
        if len(history) >= self.config.pattern_window_size:
            # Simple pattern check: look for repeated failures
            recent = history[-self.config.pattern_window_size:]
            failure_count = sum(
                1 for m in recent
                if m.get("status") == "failed"
            )
            
            if failure_count >= self.config.pattern_window_size / 2:
                return Anomaly(
                    type=AnomalyType.PATTERN,
                    workflow_id=workflow_id,
                    step_id=step_id,
                    timestamp=datetime.now(),
                    description=f"Detected {failure_count} failures in last "
                              f"{self.config.pattern_window_size} executions",
                    severity=failure_count / self.config.pattern_window_size,
                    data={
                        "failure_count": failure_count,
                        "window_size": self.config.pattern_window_size,
                        "recent_metrics": recent
                    }
                )
        return None
    
    def _check_resource_anomaly(
        self,
        workflow_id: str,
        step_id: str,
        metrics: Dict[str, Any]
    ) -> Optional[Anomaly]:
        """Check for resource usage anomalies."""
        anomalies = []
        
        if (
            "memory_mb" in metrics
            and metrics["memory_mb"] > self.config.memory_threshold_mb
        ):
            anomalies.append(
                Anomaly(
                    type=AnomalyType.RESOURCE,
                    workflow_id=workflow_id,
                    step_id=step_id,
                    timestamp=datetime.now(),
                    description=f"Memory usage {metrics['memory_mb']:.1f}MB exceeds "
                              f"threshold {self.config.memory_threshold_mb}MB",
                    severity=min(
                        metrics["memory_mb"] / self.config.memory_threshold_mb,
                        1.0
                    ),
                    data={
                        "memory_mb": metrics["memory_mb"],
                        "threshold": self.config.memory_threshold_mb
                    }
                )
            )
            
        if (
            "cpu_percent" in metrics
            and metrics["cpu_percent"] > self.config.cpu_threshold_percent
        ):
            anomalies.append(
                Anomaly(
                    type=AnomalyType.RESOURCE,
                    workflow_id=workflow_id,
                    step_id=step_id,
                    timestamp=datetime.now(),
                    description=f"CPU usage {metrics['cpu_percent']:.1f}% exceeds "
                              f"threshold {self.config.cpu_threshold_percent}%",
                    severity=min(
                        metrics["cpu_percent"] / self.config.cpu_threshold_percent,
                        1.0
                    ),
                    data={
                        "cpu_percent": metrics["cpu_percent"],
                        "threshold": self.config.cpu_threshold_percent
                    }
                )
            )
            
        return anomalies[0] if anomalies else None
    
    async def _notify_anomalies(
        self,
        workflow_id: str,
        anomalies: List[Anomaly]
    ) -> None:
        """Notify about detected anomalies via feedback loop."""
        for anomaly in anomalies:
            await self.feedback_loop.emit(
                task_id=workflow_id,
                level=FeedbackLevel.WARNING,
                message=f"Anomaly detected: {anomaly.description}",
                details={
                    "anomaly_type": anomaly.type.value,
                    "step_id": anomaly.step_id,
                    "severity": anomaly.severity,
                    "data": anomaly.data
                }
            )
            
    def get_anomalies(
        self,
        workflow_id: Optional[str] = None,
        anomaly_type: Optional[AnomalyType] = None,
        min_severity: float = 0.0,
        since: Optional[datetime] = None
    ) -> List[Anomaly]:
        """Get detected anomalies with optional filtering."""
        filtered = self._detected_anomalies
        
        if workflow_id:
            filtered = [a for a in filtered if a.workflow_id == workflow_id]
            
        if anomaly_type:
            filtered = [a for a in filtered if a.type == anomaly_type]
            
        if min_severity > 0:
            filtered = [a for a in filtered if a.severity >= min_severity]
            
        if since:
            filtered = [a for a in filtered if a.timestamp >= since]
            
        return filtered
