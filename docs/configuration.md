# Configuration Guide

## Environment Setup

### Required Environment Variables
Create a `.env` file in your project root with these configurations:

```bash
# API Configuration
CLAUDE_API_KEY=your_api_key_here

# Browser Configuration
BROWSER_TYPE=playwright  # or selenium
HEADLESS=true           # true for background execution
USER_AGENT=Mozilla/5.0...

# Execution Configuration
MAX_RETRIES=3
TIMEOUT_SECONDS=30
DEBUG_LEVEL=INFO

# Rate Limiting
REQUESTS_PER_MINUTE=60
COOL_DOWN_PERIOD=5
```

### Browser Configuration

#### Playwright Settings
```python
playwright_config = {
    "headless": True,
    "slow_mo": 50,
    "viewport": {
        "width": 1920,
        "height": 1080
    }
}
```

#### Selenium Settings
```python
selenium_config = {
    "implicit_wait": 10,
    "page_load_timeout": 30,
    "window_size": (1920, 1080)
}
```

## Strategy Configuration

### Default Strategies
```python
strategy_config = {
    "form_filling": {
        "priority": ["visual", "dom", "api"],
        "timeout": 30,
        "retries": 3
    },
    "data_extraction": {
        "priority": ["api", "dom", "visual"],
        "timeout": 60,
        "retries": 5
    }
}
```

## Error Handling

### Retry Configuration
```python
retry_config = {
    "max_attempts": 3,
    "backoff_factor": 2,
    "errors": [
        "TimeoutError",
        "ElementNotFoundError",
        "NetworkError"
    ]
}
```

## Logging Configuration

### Default Logging Setup
```python
logging_config = {
    "version": 1,
    "formatters": {
        "detailed": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "detailed",
            "level": "INFO"
        },
        "file": {
            "class": "logging.FileHandler",
            "filename": "arcana.log",
            "formatter": "detailed",
            "level": "DEBUG"
        }
    },
    "root": {
        "level": "INFO",
        "handlers": ["console", "file"]
    }
}
```
