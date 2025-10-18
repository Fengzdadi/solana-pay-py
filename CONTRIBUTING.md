# Contributing to Solana Pay Python

Thank you for your interest in contributing to Solana Pay Python! This document provides guidelines for contributing to the project.

## About This Project

This project was developed with the assistance of [Kiro](https://kiro.ai), an AI-powered development environment.

## Development Setup

### Prerequisites
- Python 3.11 or higher
- [uv](https://docs.astral.sh/uv/) package manager

### Setup Instructions

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/solana-pay-py.git
   cd solana-pay-py
   ```

2. **Install dependencies**
   ```bash
   uv sync --dev
   ```

3. **Install pre-commit hooks**
   ```bash
   uv run pre-commit install
   ```

4. **Verify setup**
   ```bash
   uv run pytest
   uv run ruff check
   uv run mypy solanapay
   ```

## Development Workflow

### Code Style
- We use [Ruff](https://docs.astral.sh/ruff/) for linting and formatting
- Code is automatically formatted on commit via pre-commit hooks
- Line length limit: 100 characters
- Follow PEP 8 conventions

### Type Checking
- All code must include type hints
- We use [mypy](https://mypy.readthedocs.io/) for static type checking
- Strict mode is enabled for the main codebase

### Testing
- Write tests for all new functionality
- Maintain high test coverage (>90%)
- Use pytest for testing framework
- Mark integration tests with `@pytest.mark.integration`
- Mark slow tests with `@pytest.mark.slow`

### Running Tests
```bash
# All tests
uv run pytest

# Unit tests only
uv run pytest -m "not integration"

# With coverage
uv run pytest --cov=solanapay --cov-report=html

# Specific test file
uv run pytest tests/test_urls.py -v
```

## Contribution Guidelines

### Pull Request Process

1. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**
   - Write code following our style guidelines
   - Add tests for new functionality
   - Update documentation as needed

3. **Run quality checks**
   ```bash
   uv run ruff check
   uv run ruff format
   uv run mypy solanapay
   uv run pytest
   ```

4. **Commit your changes**
   - Use clear, descriptive commit messages
   - Reference issue numbers when applicable

5. **Push and create PR**
   ```bash
   git push origin feature/your-feature-name
   ```

### Code Review Process
- All changes require review from maintainers
- Address feedback promptly and professionally
- Ensure CI passes before requesting review
- Squash commits before merging when appropriate

## Specification Compliance

### SPEC Adherence
- All changes must maintain compatibility with the [Solana Pay specification](https://github.com/solana-foundation/solana-pay/blob/master/SPEC.md)
- Test against official test vectors when available
- Ensure interoperability with JavaScript implementation

### Breaking Changes
- Breaking changes require major version bump
- Document migration path in CHANGELOG.md
- Provide deprecation warnings when possible

## Issue Reporting

### Bug Reports
Include the following information:
- Python version and operating system
- Library version
- Minimal code example reproducing the issue
- Expected vs actual behavior
- Full error traceback

### Feature Requests
- Describe the use case and motivation
- Provide examples of desired API
- Consider backward compatibility implications

## Documentation

### Code Documentation
- All public APIs must have docstrings
- Use Google-style docstrings
- Include examples in docstrings when helpful

### User Documentation
- Update README.md for user-facing changes
- Add examples to `examples/` directory
- Update API documentation as needed

## Release Process

### Version Numbering
We follow [Semantic Versioning](https://semver.org/):
- MAJOR: Breaking changes
- MINOR: New features (backward compatible)
- PATCH: Bug fixes (backward compatible)

### Release Checklist
- [ ] Update version in `pyproject.toml`
- [ ] Update CHANGELOG.md
- [ ] Run full test suite
- [ ] Test against live devnet
- [ ] Create release notes
- [ ] Tag release in git

## Community

### Code of Conduct
- Be respectful and inclusive
- Focus on constructive feedback
- Help newcomers get started
- Follow the [Python Community Code of Conduct](https://www.python.org/psf/conduct/)

### Getting Help
- Check existing issues and documentation first
- Ask questions in GitHub Discussions
- Join the Solana developer community

Thank you for contributing to Solana Pay Python!