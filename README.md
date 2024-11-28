# Arcana Agent Framework

A flexible, intelligent web automation framework for real-world tasks. Built with modern Python and powered by AI, Arcana helps developers create robust web automation solutions that can adapt to changing websites and handle complex workflows.

## Key Features

### 🤖 Intelligent Web Automation
- **Multi-Strategy Navigation**: Adapts to different website structures and layouts
- **AI-Powered Interaction**: Uses Claude API for intelligent decision making
- **Anti-Detection Mechanisms**: Built-in protections against bot detection
- **Parallel Task Processing**: Execute multiple tasks efficiently

### 🛠️ Flexible Architecture
- **Strategy Pattern**: Dynamically selects best approach for each task
- **Plugin System**: Easily extend with custom tools and strategies
- **Error Recovery**: Automatic retry and fallback mechanisms
- **State Management**: Persistent task state and progress tracking

### 🔌 Built-in Integrations
- **Browser Automation**: Selenium and Playwright support
- **AI Services**: Claude API integration
- **Authentication**: Multiple auth strategies (Form, OAuth, Cookie)
- **Data Extraction**: Multiple extraction methods (Direct, API, Visual)

## Installation

### Basic Installation
```bash
pip install arcana-agent
```

### Development Installation
```bash
git clone https://github.com/codeium/arcana-agent.git
cd arcana-agent
pip install -e ".[dev]"
```

## Quick Start

```python
from arcana_agent import LastMileAgent

# Initialize agent
agent = LastMileAgent()

# Example: Book a restaurant
result = await agent.execute_task({
    "type": "restaurant_booking",
    "restaurant": "Absinthe Brasserie",
    "date": "2024-03-20",
    "time": "19:00",
    "guests": 4
})

# Example: Fill a complex form
result = await agent.execute_task({
    "type": "form_filling",
    "url": "https://example.com/form",
    "form_data": {
        "name": "John Doe",
        "email": "john@example.com",
        "preferences": ["option1", "option2"]
    }
})
```

## Advanced Usage

### Custom Strategy Implementation
```python
from arcana_agent import Strategy, LastMileAgent

class CustomStrategy(Strategy):
    async def execute(self, task):
        # Custom implementation
        pass

agent = LastMileAgent()
agent.add_strategy("custom", CustomStrategy())
```

### Parallel Task Execution
```python
tasks = [
    {"type": "data_extraction", "url": "https://site1.com"},
    {"type": "data_extraction", "url": "https://site2.com"}
]

results = await agent.execute_parallel(tasks)
```

## Configuration

### Environment Variables
```bash
CLAUDE_API_KEY=your_api_key_here
BROWSER_TYPE=playwright  # or selenium
DEBUG_LEVEL=INFO
```

### Custom Configuration
```python
agent = LastMileAgent(
    config={
        "max_retries": 3,
        "timeout": 30,
        "browser": {
            "headless": True,
            "user_agent": "custom-user-agent"
        }
    }
)
```

## Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Setup
```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run linting
black .
isort .
mypy .
```

## Documentation

Full documentation is available at [https://arcana-agent.readthedocs.io/](https://arcana-agent.readthedocs.io/)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built with [Selenium](https://www.selenium.dev/) and [Playwright](https://playwright.dev/)
- Powered by [Anthropic's Claude API](https://www.anthropic.com/)
