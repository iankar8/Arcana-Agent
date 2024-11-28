# Contributing to Arcana Agent Framework

We love your input! We want to make contributing to Arcana Agent Framework as easy and transparent as possible, whether it's:

- Reporting a bug
- Discussing the current state of the code
- Submitting a fix
- Proposing new features
- Becoming a maintainer

## Development Process

1. **Fork and Clone**
```bash
git clone https://github.com/YOUR_USERNAME/Arcana-Agent.git
cd Arcana-Agent
```

2. **Set Up Development Environment**
```bash
# Create virtual environment
python -m venv env
source env/bin/activate  # On Windows: env\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Set up pre-commit hooks
pre-commit install
```

3. **Create a Branch**
```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/your-bug-fix
```

4. **Make Your Changes**
- Write your code following our style guidelines
- Add tests for new functionality
- Update documentation as needed

5. **Test Your Changes**
```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_your_feature.py

# Run with coverage
pytest --cov=./ --cov-report=term-missing

# Run linting
flake8
black .
mypy .
```

6. **Commit Your Changes**
```bash
git add .
git commit -m "feat: add new feature"  # or "fix: resolve bug"
```

Follow our commit message conventions:
- `feat:` for new features
- `fix:` for bug fixes
- `docs:` for documentation changes
- `test:` for test-related changes
- `refactor:` for code refactoring
- `style:` for formatting changes
- `chore:` for maintenance tasks

7. **Push and Create Pull Request**
```bash
git push origin feature/your-feature-name
```

## Code Style Guidelines

### Python Style
We follow PEP 8 with some modifications:
- Line length: 100 characters
- Use type hints for function arguments and return values
- Use docstrings for classes and functions

Example:
```python
from typing import List, Dict

def process_data(input_data: List[Dict]) -> Dict:
    """
    Process the input data and return summarized results.
    
    Args:
        input_data: List of dictionaries containing raw data
        
    Returns:
        Dictionary containing processed results
        
    Raises:
        ValueError: If input_data is empty
    """
    if not input_data:
        raise ValueError("Input data cannot be empty")
    
    # Process data here
    return {"result": "processed"}
```

### Testing Guidelines
- Write tests for all new features
- Maintain test coverage above 80%
- Use meaningful test names and descriptions
- Include both positive and negative test cases

Example:
```python
import pytest
from your_module import YourClass

class TestYourClass:
    @pytest.fixture
    def instance(self):
        return YourClass()
    
    def test_successful_operation(self, instance):
        """Test that operation succeeds with valid input."""
        result = instance.operation(valid_input)
        assert result.status == "success"
    
    def test_handles_invalid_input(self, instance):
        """Test that operation fails gracefully with invalid input."""
        with pytest.raises(ValueError):
            instance.operation(invalid_input)
```

## Documentation Guidelines

### Docstrings
Use Google-style docstrings:
```python
def complex_function(param1: str, param2: int) -> Dict[str, Any]:
    """
    Brief description of function.

    Longer description if needed.

    Args:
        param1: Description of param1
        param2: Description of param2

    Returns:
        Description of return value

    Raises:
        ValueError: Description of when this error occurs
        RuntimeError: Description of when this error occurs
    """
```

### README Updates
- Keep code examples up to date
- Ensure installation steps work
- Document new features
- Update API reference when needed

## Issue Guidelines

### Bug Reports
When reporting bugs, include:
```markdown
### Description
Brief description of the bug

### Steps to Reproduce
1. Step 1
2. Step 2
3. Step 3

### Expected Behavior
What should happen

### Actual Behavior
What actually happens

### Environment
- OS: [e.g., Ubuntu 20.04]
- Python Version: [e.g., 3.8.5]
- Framework Version: [e.g., 1.0.0]

### Additional Context
Any other relevant information
```

### Feature Requests
When requesting features:
```markdown
### Problem
Describe the problem this feature would solve

### Proposed Solution
Describe your proposed solution

### Alternatives Considered
Other solutions you've considered

### Additional Context
Any other relevant information
```

## Getting Help

- Join our [Discussions](https://github.com/iankar8/Arcana-Agent/discussions)
- Check existing issues and pull requests
- Reach out to maintainers

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
