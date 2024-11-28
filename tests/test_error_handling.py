"""Tests for error handling system."""

import pytest
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any

from core.error_handling import (
    ErrorHandler,
    ErrorSeverity,
    ErrorCategory,
    ErrorContext,
    RecoveryStrategy,
    CircuitBreaker
)

@pytest.fixture
async def error_handler():
    """Create error handler fixture."""
    handler = ErrorHandler()
    yield handler

@pytest.fixture
async def circuit_breaker():
    """Create circuit breaker fixture."""
    breaker = CircuitBreaker(
        failure_threshold=2,
        reset_timeout=0.1,
        half_open_timeout=0.05
    )
    yield breaker

async def test_error_handler_initialization(error_handler):
    """Test error handler initialization."""
    assert error_handler.error_handlers == {}
    assert len(error_handler.recovery_strategies) == len(ErrorCategory)

async def test_register_handler(error_handler):
    """Test handler registration."""
    async def test_handler(context: ErrorContext):
        pass
    
    error_handler.register_handler(ValueError, test_handler)
    assert ValueError in error_handler.error_handlers
    assert len(error_handler.error_handlers[ValueError]) == 1

async def test_set_recovery_strategy(error_handler):
    """Test setting recovery strategy."""
    error_handler.set_recovery_strategy(
        ErrorCategory.TIMEOUT,
        RecoveryStrategy.BACKOFF
    )
    assert error_handler.recovery_strategies[ErrorCategory.TIMEOUT] == RecoveryStrategy.BACKOFF

async def test_handle_error(error_handler):
    """Test error handling."""
    handled = False
    
    async def test_handler(context: ErrorContext):
        nonlocal handled
        handled = True
        assert context.error_type == "ValueError"
        assert context.severity == ErrorSeverity.LOW
        assert context.category == ErrorCategory.VALIDATION
    
    error_handler.register_handler(ValueError, test_handler)
    
    try:
        raise ValueError("test error")
    except Exception as e:
        await error_handler.handle_error(e, {"component": "test"})
    
    assert handled

async def test_circuit_breaker_normal_operation(circuit_breaker):
    """Test circuit breaker under normal operation."""
    async def success_operation():
        return "success"
    
    result = await circuit_breaker.execute(success_operation)
    assert result == "success"
    assert not circuit_breaker.is_open

async def test_circuit_breaker_failure(circuit_breaker):
    """Test circuit breaker under failure conditions."""
    async def failing_operation():
        raise ValueError("test error")
    
    # First failure
    with pytest.raises(ValueError):
        await circuit_breaker.execute(failing_operation)
    assert not circuit_breaker.is_open
    
    # Second failure should open circuit
    with pytest.raises(ValueError):
        await circuit_breaker.execute(failing_operation)
    assert circuit_breaker.is_open
    
    # Further calls should fail immediately
    with pytest.raises(Exception) as exc_info:
        await circuit_breaker.execute(failing_operation)
    assert str(exc_info.value) == "Circuit breaker is open"

async def test_circuit_breaker_reset(circuit_breaker):
    """Test circuit breaker reset after timeout."""
    async def failing_operation():
        raise ValueError("test error")
    
    async def success_operation():
        return "success"
    
    # Trigger circuit breaker
    for _ in range(2):
        with pytest.raises(ValueError):
            await circuit_breaker.execute(failing_operation)
    
    assert circuit_breaker.is_open
    
    # Wait for reset timeout
    await asyncio.sleep(0.2)
    
    # Should work again
    result = await circuit_breaker.execute(success_operation)
    assert result == "success"
    assert not circuit_breaker.is_open

async def test_error_severity_detection(error_handler):
    """Test error severity detection."""
    async def test_handler(context: ErrorContext):
        if isinstance(context.error_type, KeyboardInterrupt):
            assert context.severity == ErrorSeverity.FATAL
        elif isinstance(context.error_type, MemoryError):
            assert context.severity == ErrorSeverity.HIGH
        elif isinstance(context.error_type, TimeoutError):
            assert context.severity == ErrorSeverity.MEDIUM
        else:
            assert context.severity == ErrorSeverity.LOW
    
    error_handler.register_handler(Exception, test_handler)
    
    # Test different error types
    for error in [ValueError(), MemoryError(), TimeoutError()]:
        try:
            raise error
        except Exception as e:
            await error_handler.handle_error(e, {"component": "test"})

async def test_error_category_detection(error_handler):
    """Test error category detection."""
    async def test_handler(context: ErrorContext):
        if isinstance(context.error_type, ValueError):
            assert context.category == ErrorCategory.VALIDATION
        elif isinstance(context.error_type, TimeoutError):
            assert context.category == ErrorCategory.TIMEOUT
        elif isinstance(context.error_type, ConnectionError):
            assert context.category == ErrorCategory.EXTERNAL
    
    error_handler.register_handler(Exception, test_handler)
    
    # Test different error types
    for error in [ValueError(), TimeoutError(), ConnectionError()]:
        try:
            raise error
        except Exception as e:
            await error_handler.handle_error(e, {"component": "test"})
