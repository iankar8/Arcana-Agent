"""Error handling and recovery system for Arcana Agent Framework."""

from typing import Optional, Dict, Any, Type, Callable, List
import asyncio
import traceback
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

from .logging_config import get_logger
from core.interfaces import Agent
from core.monitoring import MetricsCollector

logger = get_logger(__name__)

class ErrorSeverity(Enum):
    """Severity levels for errors."""
    LOW = "low"           # Non-critical errors that don't affect core functionality
    MEDIUM = "medium"     # Errors that affect specific features but not the whole system
    HIGH = "high"         # Critical errors that require immediate attention
    FATAL = "fatal"       # System-breaking errors that require shutdown

class ErrorCategory(Enum):
    """Categories of errors for better handling."""
    VALIDATION = "validation"
    EXECUTION = "execution"
    TIMEOUT = "timeout"
    RESOURCE = "resource"
    EXTERNAL = "external"
    INTERNAL = "internal"
    TASK = "task"
    UNKNOWN = "unknown"

@dataclass
class ErrorContext:
    """Context information for errors."""
    timestamp: datetime
    error_type: str
    message: str
    stack_trace: str
    severity: ErrorSeverity
    category: ErrorCategory
    component: str
    additional_info: Dict[str, Any]

class RecoveryStrategy(Enum):
    """Available recovery strategies."""
    RETRY = "retry"               # Simple retry
    BACKOFF = "backoff"          # Exponential backoff retry
    FALLBACK = "fallback"        # Use fallback method
    CIRCUIT_BREAK = "break"      # Stop operations temporarily
    IGNORE = "ignore"            # Continue despite error
    SHUTDOWN = "shutdown"        # Graceful shutdown

class CircuitBreaker:
    """Circuit breaker pattern implementation."""
    
    def __init__(
        self,
        failure_threshold: int = 5,
        reset_timeout: float = 60.0,
        half_open_timeout: float = 5.0
    ):
        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout
        self.half_open_timeout = half_open_timeout
        self.failure_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.is_open = False
        self.logger = get_logger(self.__class__.__name__)
    
    async def execute(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker pattern."""
        if self.is_open:
            if self._should_reset():
                self.logger.info("Circuit half-open, attempting reset")
                try:
                    result = await asyncio.wait_for(
                        func(*args, **kwargs),
                        timeout=self.half_open_timeout
                    )
                    self._reset()
                    return result
                except Exception as e:
                    self._record_failure()
                    raise
            else:
                raise Exception("Circuit breaker is open")
        
        try:
            result = await func(*args, **kwargs)
            self._reset()
            return result
        except Exception as e:
            self._record_failure()
            raise
    
    def _record_failure(self) -> None:
        """Record a failure and potentially open the circuit."""
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        
        if self.failure_count >= self.failure_threshold:
            self.is_open = True
            self.logger.warning(f"Circuit breaker opened after {self.failure_count} failures")
    
    def _should_reset(self) -> bool:
        """Check if enough time has passed to try resetting the circuit."""
        if not self.last_failure_time:
            return True
        
        time_since_last_failure = (datetime.now() - self.last_failure_time).total_seconds()
        return time_since_last_failure >= self.reset_timeout
    
    def _reset(self) -> None:
        """Reset the circuit breaker state."""
        self.failure_count = 0
        self.last_failure_time = None
        self.is_open = False

class ErrorHandler(Agent):
    """Central error handling system."""
    
    def __init__(self, metrics_collector: MetricsCollector):
        self.metrics = metrics_collector
        self.error_handlers: Dict[Type[Exception], List[Callable]] = {}
        self.recovery_strategies: Dict[ErrorCategory, RecoveryStrategy] = {
            ErrorCategory.VALIDATION: RecoveryStrategy.IGNORE,
            ErrorCategory.EXECUTION: RecoveryStrategy.RETRY,
            ErrorCategory.TIMEOUT: RecoveryStrategy.BACKOFF,
            ErrorCategory.RESOURCE: RecoveryStrategy.CIRCUIT_BREAK,
            ErrorCategory.EXTERNAL: RecoveryStrategy.FALLBACK,
            ErrorCategory.INTERNAL: RecoveryStrategy.SHUTDOWN,
            ErrorCategory.UNKNOWN: RecoveryStrategy.SHUTDOWN,
            ErrorCategory.TASK: RecoveryStrategy.IGNORE
        }
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.logger = get_logger(self.__class__.__name__)
    
    async def start(self) -> None:
        """Start the error handler."""
        self.logger.info("Error handler started")
    
    async def stop(self) -> None:
        """Stop the error handler."""
        self.logger.info("Error handler stopped")
    
    def register_handler(
        self,
        exception_type: Type[Exception],
        handler: Callable
    ) -> None:
        """Register an error handler for a specific exception type."""
        if exception_type not in self.error_handlers:
            self.error_handlers[exception_type] = []
        self.error_handlers[exception_type].append(handler)
        self.logger.info(f"Registered handler for {exception_type.__name__}")
    
    def set_recovery_strategy(
        self,
        category: ErrorCategory,
        strategy: RecoveryStrategy
    ) -> None:
        """Set recovery strategy for an error category."""
        self.recovery_strategies[category] = strategy
        self.logger.info(f"Set {strategy.value} strategy for {category.value} errors")
    
    def get_circuit_breaker(self, name: str) -> CircuitBreaker:
        """Get or create a circuit breaker."""
        if name not in self.circuit_breakers:
            self.circuit_breakers[name] = CircuitBreaker()
        return self.circuit_breakers[name]
    
    async def handle_error(
        self,
        error: Exception,
        context: Dict[str, Any]
    ) -> Optional[Any]:
        """Handle an error with appropriate recovery strategy."""
        try:
            # Create error context
            error_context = ErrorContext(
                timestamp=datetime.now(),
                error_type=error.__class__.__name__,
                message=str(error),
                stack_trace=traceback.format_exc(),
                severity=self._get_severity(error),
                category=self._get_category(error),
                component=context.get("component", "unknown"),
                additional_info=context
            )
            
            self.logger.error(f"Handling error: {error_context}")
            
            # Execute registered handlers
            for handler in self.error_handlers.get(type(error), []):
                try:
                    await handler(error_context)
                except Exception as e:
                    self.logger.error(f"Error handler failed: {str(e)}")
            
            # Apply recovery strategy
            strategy = self.recovery_strategies[error_context.category]
            return await self._apply_strategy(strategy, error_context)
            
        except Exception as e:
            self.logger.error(f"Error handling failed: {str(e)}")
            raise
    
    def _get_severity(self, error: Exception) -> ErrorSeverity:
        """Determine error severity based on error type."""
        if isinstance(error, (KeyboardInterrupt, SystemExit)):
            return ErrorSeverity.FATAL
        if isinstance(error, (MemoryError, RuntimeError)):
            return ErrorSeverity.HIGH
        if isinstance(error, TimeoutError):
            return ErrorSeverity.MEDIUM
        return ErrorSeverity.LOW
    
    def _get_category(self, error: Exception) -> ErrorCategory:
        """Categorize error based on type."""
        if isinstance(error, ValueError):
            return ErrorCategory.VALIDATION
        if isinstance(error, TimeoutError):
            return ErrorCategory.TIMEOUT
        if isinstance(error, (MemoryError, OSError)):
            return ErrorCategory.RESOURCE
        if isinstance(error, ConnectionError):
            return ErrorCategory.EXTERNAL
        if isinstance(error, Exception):
            return ErrorCategory.INTERNAL
        return ErrorCategory.UNKNOWN
    
    async def _apply_strategy(
        self,
        strategy: RecoveryStrategy,
        context: ErrorContext
    ) -> Optional[Any]:
        """Apply the selected recovery strategy."""
        self.logger.info(f"Applying {strategy.value} strategy for {context.error_type}")
        
        if strategy == RecoveryStrategy.RETRY:
            return await self._handle_retry(context)
        elif strategy == RecoveryStrategy.BACKOFF:
            return await self._handle_backoff(context)
        elif strategy == RecoveryStrategy.FALLBACK:
            return await self._handle_fallback(context)
        elif strategy == RecoveryStrategy.CIRCUIT_BREAK:
            return await self._handle_circuit_break(context)
        elif strategy == RecoveryStrategy.IGNORE:
            return None
        elif strategy == RecoveryStrategy.SHUTDOWN:
            await self._handle_shutdown(context)
            return None
    
    async def _handle_retry(self, context: ErrorContext) -> Optional[Any]:
        """Handle retry strategy."""
        # Implementation depends on the task execution system
        self.logger.info(f"Retrying operation for {context.component}")
        return None
    
    async def _handle_backoff(self, context: ErrorContext) -> Optional[Any]:
        """Handle exponential backoff strategy."""
        # Implementation depends on the task execution system
        self.logger.info(f"Applying backoff for {context.component}")
        return None
    
    async def _handle_fallback(self, context: ErrorContext) -> Optional[Any]:
        """Handle fallback strategy."""
        # Implementation depends on available fallback methods
        self.logger.info(f"Using fallback for {context.component}")
        return None
    
    async def _handle_circuit_break(self, context: ErrorContext) -> Optional[Any]:
        """Handle circuit breaker strategy."""
        circuit_breaker = self.get_circuit_breaker(context.component)
        self.logger.info(f"Circuit breaker engaged for {context.component}")
        return None
    
    async def _handle_shutdown(self, context: ErrorContext) -> None:
        """Handle shutdown strategy."""
        self.logger.critical(f"Initiating shutdown due to: {context.error_type}")
        # Implement graceful shutdown logic here

class DefaultErrorHandler(ErrorHandler):
    """Default implementation of error handling."""

    def __init__(self, metrics_collector: MetricsCollector, max_history: int = 1000):
        super().__init__(metrics_collector)
        self.max_history = max_history
        self._error_history: list[tuple[Exception, ErrorContext]] = []
        self._logger = logging.getLogger(__name__)

    async def handle_error(
        self,
        error: Exception,
        context: Dict[str, Any],
        severity: ErrorSeverity = ErrorSeverity.MEDIUM
    ) -> None:
        """Handle an error with context."""
        error_context = ErrorContext(
            timestamp=datetime.now(),
            component=context.get("component", "unknown"),
            operation=context.get("operation", "unknown"),
            details=context,
            error_type=error.__class__.__name__,
            message=str(error),
            stack_trace=traceback.format_exc(),
            severity=severity,
            category=self._get_category(error),
            additional_info=context
        )
        
        self._error_history.append((error, error_context))
        
        # Log the error
        log_message = (
            f"Error in {error_context.component}.{error_context.operation}: "
            f"{str(error)}\nContext: {context}\n{traceback.format_exc()}"
        )
        
        if severity == ErrorSeverity.CRITICAL:
            self._logger.critical(log_message)
        elif severity == ErrorSeverity.HIGH:
            self._logger.error(log_message)
        elif severity == ErrorSeverity.MEDIUM:
            self._logger.warning(log_message)
        else:
            self._logger.info(log_message)
            
        # Update metrics
        self.metrics.increment_counter(
            "errors_total",
            {
                "component": error_context.component,
                "operation": error_context.operation,
                "severity": severity.value,
                "error_type": error.__class__.__name__
            }
        )

    async def get_error_history(
        self,
        component: Optional[str] = None,
        severity: Optional[ErrorSeverity] = None,
        limit: int = 100
    ) -> List[Tuple[Exception, ErrorContext]]:
        """Get error history with optional filters."""
        filtered_history = []
        
        for error, context in reversed(self._error_history):
            if component and context.component != component:
                continue
                
            # Note: We don't filter by severity here since it's not stored in context
            # This could be enhanced by storing severity in ErrorContext
            
            filtered_history.append((error, context))
            if len(filtered_history) >= limit:
                break
                
        return filtered_history
