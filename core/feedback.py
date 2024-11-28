"""Feedback management system for agent learning and adaptation."""

from typing import Dict, Any, List, Optional
from datetime import datetime
import json
from dataclasses import dataclass, asdict
import uuid

from core.monitoring import MetricsCollector
from core.error_handling import ErrorHandler
from core.logging_config import get_logger

logger = get_logger(__name__)

@dataclass
class Feedback:
    """Represents a piece of feedback for an agent."""
    id: str
    agent_name: str
    feedback_type: str
    message: str
    timestamp: datetime
    metadata: Dict[str, Any]
    source: str
    severity: str

    @classmethod
    def create(
        cls,
        agent_name: str,
        feedback_type: str,
        message: str,
        metadata: Optional[Dict[str, Any]] = None,
        source: str = "user",
        severity: str = "info"
    ) -> 'Feedback':
        """Create a new feedback entry."""
        return cls(
            id=str(uuid.uuid4()),
            agent_name=agent_name,
            feedback_type=feedback_type,
            message=message,
            timestamp=datetime.now(),
            metadata=metadata or {},
            source=source,
            severity=severity
        )

class FeedbackManager:
    """Manages feedback collection and analysis for agents."""

    def __init__(
        self,
        metrics_collector: MetricsCollector,
        error_handler: ErrorHandler
    ):
        self.metrics = metrics_collector
        self.error_handler = error_handler
        self.feedback_log: List[Feedback] = []
        self._logger = get_logger(self.__class__.__name__)

    def add_feedback(self, feedback: Feedback) -> None:
        """Add a new feedback entry."""
        self.feedback_log.append(feedback)
        
        self.metrics.record(
            name="feedback_received",
            value=1,
            metric_type="counter",
            component="feedback_manager",
            labels={
                "agent": feedback.agent_name,
                "type": feedback.feedback_type,
                "severity": feedback.severity
            }
        )
        
        self._logger.info(
            f"Received feedback for agent {feedback.agent_name}: {feedback.message}"
        )

    def get_agent_feedback(
        self,
        agent_name: str,
        feedback_type: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[Feedback]:
        """Get feedback for a specific agent."""
        feedback = [
            f for f in self.feedback_log
            if f.agent_name == agent_name
            and (feedback_type is None or f.feedback_type == feedback_type)
        ]
        
        if limit:
            feedback = sorted(
                feedback,
                key=lambda x: x.timestamp,
                reverse=True
            )[:limit]
            
        return feedback

    def get_feedback_summary(self, agent_name: str) -> Dict[str, Any]:
        """Get a summary of feedback for an agent."""
        agent_feedback = self.get_agent_feedback(agent_name)
        
        if not agent_feedback:
            return {
                "agent_name": agent_name,
                "total_feedback": 0,
                "feedback_types": {},
                "severity_distribution": {}
            }

        feedback_types = {}
        severity_distribution = {}
        
        for feedback in agent_feedback:
            feedback_types[feedback.feedback_type] = feedback_types.get(
                feedback.feedback_type, 0
            ) + 1
            severity_distribution[feedback.severity] = severity_distribution.get(
                feedback.severity, 0
            ) + 1

        return {
            "agent_name": agent_name,
            "total_feedback": len(agent_feedback),
            "feedback_types": feedback_types,
            "severity_distribution": severity_distribution,
            "latest_feedback": asdict(agent_feedback[-1])
        }

    def export_feedback(self, filepath: str) -> None:
        """Export feedback log to a JSON file."""
        data = {
            "feedback_log": [
                {
                    **asdict(f),
                    "timestamp": f.timestamp.isoformat()
                }
                for f in self.feedback_log
            ]
        }
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)

    @classmethod
    def import_feedback(
        cls,
        filepath: str,
        metrics_collector: MetricsCollector,
        error_handler: ErrorHandler
    ) -> 'FeedbackManager':
        """Import feedback log from a JSON file."""
        manager = cls(metrics_collector, error_handler)
        
        with open(filepath, 'r') as f:
            data = json.load(f)
            
        manager.feedback_log = [
            Feedback(
                **{
                    **f,
                    "timestamp": datetime.fromisoformat(f["timestamp"])
                }
            )
            for f in data["feedback_log"]
        ]
        
        return manager
