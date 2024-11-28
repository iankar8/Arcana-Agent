# Arcana Agent Framework

![Build Status](https://github.com/iankar8/Arcana-Agent/actions/workflows/ci.yml/badge.svg)
![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)
![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)
![Code Coverage](https://img.shields.io/codecov/c/github/iankar8/Arcana-Agent)

Arcana is an intelligent web automation framework that combines the power of AI with robust browser automation to create resilient, adaptive web interactions. It's designed to handle complex workflows that traditional automation tools struggle with, using AI to understand and adapt to changing web interfaces.

## 🌟 Key Features

- **AI-Powered Navigation**: Leverages Claude AI to understand and interact with web elements intelligently
- **Adaptive Strategies**: Automatically selects the best approach for each task based on context
- **Self-Healing Scripts**: Recovers from errors and adapts to website changes automatically
- **Parallel Execution**: Efficiently handles multiple tasks concurrently
- **Browser Support**: Works with both Playwright and Selenium for maximum flexibility
- **Extensible Architecture**: Easy to add custom tools and strategies

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/iankar8/Arcana-Agent.git
cd Arcana-Agent

# Create and activate virtual environment
python -m venv env
source env/bin/activate  # On Windows: env\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your API keys
```

### Basic Usage

```python
from arcana_agent import LastMileAgent

# Initialize the agent
agent = LastMileAgent()

# Example: Restaurant Booking
result = await agent.execute_task({
    "type": "restaurant_booking",
    "restaurant": "Le Bernardin",
    "date": "2024-03-20",
    "time": "19:00",
    "guests": 2
})

# Example: Form Filling
result = await agent.execute_task({
    "type": "form_filling",
    "url": "https://example.com/form",
    "data": {
        "name": "John Doe",
        "email": "john@example.com"
    }
})
```

## 📋 Prerequisites

- Python 3.8 or higher
- Chrome/Firefox browser installed
- Claude API key for AI features
- Operating System: Windows, macOS, or Linux

## 🛠️ Development Setup

For development, install additional dependencies:

```bash
pip install -r requirements-dev.txt

# Run tests
pytest

# Run linting
flake8
```

## 📚 Documentation

- [Architecture Overview](docs/architecture.md)
- [API Reference](docs/api_reference.md)
- [Configuration Guide](docs/configuration.md)
- [Contributing Guide](CONTRIBUTING.md)

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details on:
- Setting up your development environment
- Code style guidelines
- Submitting pull requests
- Running tests

## 🔍 Examples

Check out our [examples directory](examples/) for complete usage examples:
- Restaurant booking automation
- Form filling and data extraction
- Multi-page workflows
- Error handling patterns

## Core Systems

### Error Handling & Recovery System
The framework includes a robust error handling system with:
- Multiple severity levels and error categories
- Configurable recovery strategies
- Circuit breaker pattern for fault tolerance
- Comprehensive error context tracking

Usage:
```python
from core.error_handling import ErrorHandler, ErrorCategory, RecoveryStrategy

# Initialize error handler
error_handler = ErrorHandler()

# Set recovery strategy
error_handler.set_recovery_strategy(
    ErrorCategory.TIMEOUT,
    RecoveryStrategy.BACKOFF
)

# Handle errors
try:
    result = await some_operation()
except Exception as e:
    await error_handler.handle_error(e, {"component": "task_executor"})
```

### Monitoring & Metrics System
Comprehensive monitoring with:
- Multiple metric types (Counter, Gauge, Histogram, Timer)
- System metrics collection (CPU, Memory, Disk)
- Metric aggregation and statistics
- Prometheus-compatible export format

Usage:
```python
from core.monitoring import MetricsCollector, MetricType, Timer

# Initialize collector
collector = MetricsCollector()
await collector.start()

# Record metrics
collector.record(
    name="task_count",
    value=1,
    metric_type=MetricType.COUNTER,
    component="task_executor"
)

# Use timer context manager
async with Timer("task_execution", "task_executor", collector):
    await execute_task()
```

### Caching System
Flexible caching system with:
- Multiple cache strategies (LRU, LFU, FIFO, TTL)
- Automatic cache maintenance
- Size-based eviction
- Decorator support

Usage:
```python
from core.caching import Cache, cached
from datetime import timedelta

# Initialize cache
cache = Cache[str](max_size=1000)
await cache.start()

# Use cache directly
await cache.set("key", "value", ttl=timedelta(hours=1))
value = await cache.get("key")

# Use decorator
@cached(ttl=timedelta(minutes=30))
async def expensive_operation():
    return await compute_result()
```

## Testing

To run the tests:

```bash
# Run all tests
pytest

# Run tests with coverage report
pytest --cov=core --cov=agents

# Run tests in parallel
pytest -n auto

# Run specific test file
pytest tests/test_core_components.py
```

### Test Structure

The test suite includes:
- Unit tests for core components (NLU, TaskPlanner, ResponseBuilder)
- Integration tests for the orchestrator
- Mock tests for external API calls

### Logging

The framework uses a comprehensive logging system:
- Console logging for development
- File logging for production (logs stored in `logs/` directory)
- Rotating file handler to manage log size
- Different log levels (DEBUG, INFO, WARNING, ERROR)

To configure logging:

```python
from core.logging_config import setup_logging

# Basic setup with console logging
setup_logging()

# Setup with file logging
setup_logging(
    log_file="logs/arcana.log",
    log_level=logging.INFO
)
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Playwright](https://playwright.dev/) for modern browser automation
- [Anthropic](https://www.anthropic.com/) for Claude AI integration
- All our [contributors](https://github.com/iankar8/Arcana-Agent/graphs/contributors)

## 📬 Contact & Support

- Create an issue for bug reports or feature requests
- Join our [Discussions](https://github.com/iankar8/Arcana-Agent/discussions) for questions
- Follow [@iankar8](https://twitter.com/iankar8) for updates

---
Built with ❤️ by the Arcana Agent community
