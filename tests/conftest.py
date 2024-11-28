import pytest
import pytest_asyncio
import os
import json
from pathlib import Path

# Load test data fixtures
@pytest.fixture
def test_data_dir():
    return Path(__file__).parent / 'test_data'

@pytest.fixture
def html_fixtures(test_data_dir):
    def _load_html(name):
        with open(test_data_dir / 'html' / f'{name}.html', 'r', encoding='utf-8') as f:
            return f.read()
    return _load_html

@pytest.fixture
def json_fixtures(test_data_dir):
    def _load_json(name):
        with open(test_data_dir / 'json' / f'{name}.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    return _load_json

# Mock environment variables
@pytest.fixture
def mock_env(monkeypatch):
    env_vars = {
        'CLAUDE_API_KEY': 'test_api_key',
        'BROWSER_TYPE': 'playwright',
        'HEADLESS': 'true',
        'DEBUG_LEVEL': 'DEBUG'
    }
    for key, value in env_vars.items():
        monkeypatch.setenv(key, value)
    return env_vars

# Mock responses
@pytest.fixture
def mock_claude_responses():
    return {
        'analyze_page': {'analysis': 'Test analysis'},
        'generate_script': {'script': 'Test script'},
        'analyze_form': {'fields': [{'name': 'test', 'type': 'text'}]},
        'error': {'error': 'Test error', 'status': 'error'}
    }

@pytest.fixture
def mock_browser_responses():
    return {
        'navigate': {'status': 'success'},
        'click': {'status': 'success', 'element': 'button'},
        'form_fill': {'status': 'success', 'fields_filled': ['username', 'password']},
        'error': {'status': 'error', 'message': 'Element not found'}
    }

# Common test tasks
@pytest.fixture
def test_tasks():
    return {
        'restaurant_booking': {
            'type': 'restaurant_booking',
            'restaurant': 'Test Restaurant',
            'date': '2024-03-20',
            'time': '19:00',
            'guests': 2
        },
        'form_filling': {
            'type': 'form_filling',
            'url': 'https://example.com/form',
            'data': {
                'username': 'testuser',
                'password': 'testpass'
            }
        },
        'data_extraction': {
            'type': 'data_extraction',
            'url': 'https://example.com/data',
            'selectors': {
                'title': 'h1',
                'content': '.content'
            }
        }
    }

# Performance testing configurations
@pytest.fixture
def performance_config():
    return {
        'concurrent_tasks': 5,
        'iterations': 100,
        'timeout': 30,
        'max_retries': 3
    }
