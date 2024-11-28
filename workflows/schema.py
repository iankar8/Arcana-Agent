"""Schema definitions for workflow YAML files."""

from typing import Dict, Any, List
from dataclasses import dataclass
from datetime import datetime
import yaml
from pathlib import Path

@dataclass
class WorkflowStep:
    """Single step in a workflow."""
    agent: str
    intent: str
    payload: Dict[str, Any]
    requires: List[str] = None
    timeout: int = None
    retry: Dict[str, Any] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WorkflowStep':
        """Create step from dictionary."""
        return cls(
            agent=data['agent'],
            intent=data['intent'],
            payload=data.get('payload', {}),
            requires=data.get('requires', []),
            timeout=data.get('timeout'),
            retry=data.get('retry')
        )

@dataclass
class Workflow:
    """Complete workflow definition."""
    name: str
    description: str
    version: str
    steps: List[WorkflowStep]
    metadata: Dict[str, Any]
    created_at: datetime

    @classmethod
    def from_yaml(cls, filepath: str) -> 'Workflow':
        """Load workflow from YAML file."""
        with open(filepath, 'r') as f:
            data = yaml.safe_load(f)

        return cls(
            name=data['name'],
            description=data['description'],
            version=data['version'],
            steps=[WorkflowStep.from_dict(s) for s in data['steps']],
            metadata=data.get('metadata', {}),
            created_at=datetime.now()
        )

    def validate(self) -> List[str]:
        """Validate workflow definition."""
        errors = []
        
        # Check required fields
        if not self.name:
            errors.append("Workflow name is required")
        if not self.version:
            errors.append("Workflow version is required")
        if not self.steps:
            errors.append("Workflow must have at least one step")

        # Validate step dependencies
        step_ids = {step.agent for step in self.steps}
        for step in self.steps:
            if step.requires:
                for req in step.requires:
                    if req not in step_ids:
                        errors.append(
                            f"Step '{step.agent}' requires unknown step '{req}'"
                        )

        return errors

    def to_dict(self) -> Dict[str, Any]:
        """Convert workflow to dictionary."""
        return {
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "steps": [
                {
                    "agent": step.agent,
                    "intent": step.intent,
                    "payload": step.payload,
                    "requires": step.requires,
                    "timeout": step.timeout,
                    "retry": step.retry
                }
                for step in self.steps
            ],
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat()
        }
