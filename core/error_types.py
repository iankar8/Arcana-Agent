"""Error types and interfaces for the Arcana Agent Framework."""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from enum import Enum
from dataclasses import dataclass
from datetime import datetime

class ErrorSeverity(Enum):
    """Severity levels for errors."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class ErrorContext:
    """Context information for an error."""
    timestamp: datetime
    component: str
    operation: str
    details: Optional[Dict[str, Any]] = None

class ErrorHandler(ABC):
    """Interface for error handling components."""

    @abstractmethod
    async def handle_error(
        self,
        error: Exception,
        context: Dict[str, Any],
        severity: ErrorSeverity = ErrorSeverity.MEDIUM
    ) -> None:
        """Handle an error with context."""
        pass

    @abstractmethod
    async def get_error_history(
        self,
        component: Optional[str] = None,
        severity: Optional[ErrorSeverity] = None,
        limit: int = 100
    ) -> list[tuple[Exception, ErrorContext]]:
        """Get error history with optional filters."""
        pass
