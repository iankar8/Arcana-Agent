# Contributing to Arcana Agent Framework

We love your input! We want to make contributing to Arcana Agent Framework as easy and transparent as possible, whether it's:

- Reporting a bug
- Discussing the current state of the code
- Submitting a fix
- Proposing new features
- Becoming a maintainer

## We Develop with Github
We use GitHub to host code, to track issues and feature requests, as well as accept pull requests.

## We Use [Github Flow](https://guides.github.com/introduction/flow/index.html)
Pull requests are the best way to propose changes to the codebase. We actively welcome your pull requests:

1. Fork the repo and create your branch from `main`.
2. If you've added code that should be tested, add tests.
3. If you've changed APIs, update the documentation.
4. Ensure the test suite passes.
5. Make sure your code lints.
6. Issue that pull request!

## Any contributions you make will be under the MIT Software License
In short, when you submit code changes, your submissions are understood to be under the same [MIT License](http://choosealicense.com/licenses/mit/) that covers the project. Feel free to contact the maintainers if that's a concern.

## Report bugs using Github's [issue tracker](https://github.com/codeium/arcana-agent/issues)
We use GitHub issues to track public bugs. Report a bug by [opening a new issue](https://github.com/codeium/arcana-agent/issues/new); it's that easy!

## Write bug reports with detail, background, and sample code

**Great Bug Reports** tend to have:

- A quick summary and/or background
- Steps to reproduce
  - Be specific!
  - Give sample code if you can.
- What you expected would happen
- What actually happens
- Notes (possibly including why you think this might be happening, or stuff you tried that didn't work)

## Development Process

1. Clone the repository
```bash
git clone https://github.com/codeium/arcana-agent.git
cd arcana-agent
```

2. Create a virtual environment and install dependencies
```bash
python -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`
pip install -e ".[dev]"
```

3. Create a branch
```bash
git checkout -b feature-name
```

4. Make your changes
- Write your code
- Add tests if applicable
- Update documentation if needed

5. Run tests and linting
```bash
# Run tests
pytest

# Run linting
black .
isort .
mypy .
```

6. Commit your changes
```bash
git add .
git commit -m "Description of changes"
```

7. Push to your fork and submit a pull request
```bash
git push origin feature-name
```

## Code Style

We use several tools to maintain code quality:

- [Black](https://black.readthedocs.io/) for code formatting
- [isort](https://pycqa.github.io/isort/) for import sorting
- [mypy](http://mypy-lang.org/) for static type checking
- [pylint](https://www.pylint.org/) for code analysis

Please ensure your code passes all style checks before submitting:

```bash
# Install dev dependencies if you haven't already
pip install -e ".[dev]"

# Run style checks
black --check .
isort --check-only .
mypy .
pylint arcana_agent
```

## License
By contributing, you agree that your contributions will be licensed under its MIT License.
