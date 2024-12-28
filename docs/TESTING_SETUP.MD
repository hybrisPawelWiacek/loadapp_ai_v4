# Testing Setup Documentation

## Overview
This document describes the testing setup for the LoadApp.AI project, including test organization, configuration, and execution procedures.

## Test Structure
```
tests/
├── backend/           # Backend-specific tests
├── frontend/         # Frontend-specific tests
└── conftest.py      # Shared test configuration and fixtures
```

## Test Configuration
- **pytest.ini**: Global pytest configuration
- **conftest.py**: Shared fixtures and test utilities
- **Environment Variables**: Test-specific configurations in `.env`

## Running Tests

### Using the Test Runner Script
The project includes a convenient test runner script (`scripts/run_tests.sh`) with various options:

```bash
# Run all tests
./scripts/run_tests.sh -a

# Run backend tests only
./scripts/run_tests.sh -b

# Run frontend tests only
./scripts/run_tests.sh -f

# Run tests matching a pattern
./scripts/run_tests.sh -p "hello"

# Run tests with verbose output
./scripts/run_tests.sh -a -v
```

### Manual Test Execution
You can also run tests directly using pytest:

```bash
# Activate virtual environment
source venv/bin/activate

# Run specific test files
pytest tests/backend/test_app.py -v
pytest tests/frontend/test_streamlit_app.py -v

# Run all tests
pytest tests/ -v
```

## Test Environment

### Virtual Environment
Tests should be run within the project's virtual environment:
```bash
# Create virtual environment (if not exists)
python3.12 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install requirements
pip install -r requirements.txt
```

### Environment Variables
Tests use environment variables defined in `.env` file. A template is provided in `template.env`.

Key test-related environment variables:
- `ENV=development`
- `BACKEND_PORT=5001`
- `FRONTEND_PORT=8501`
- `DEBUG_MODE=true`
- `LOG_LEVEL=DEBUG`

## Test Categories

### Backend Tests
- API endpoint tests
- Configuration tests
- Database integration tests
- Service layer tests

### Frontend Tests
- Component tests
- Integration tests with backend
- UI functionality tests

## Writing Tests

### Test File Naming
- Test files should be named `test_*.py`
- Test functions should be named `test_*`
- Test classes should be named `Test*`

### Test Organization
- Group related tests in classes
- Use descriptive test names
- Include docstrings for complex tests

### Fixtures
Common fixtures are available in `conftest.py`:
- `test_dir`: Test directory path
- `project_root`: Project root directory
- `mock_env_vars`: Environment variables for testing

## Continuous Integration
- Tests are automatically run on each commit
- All tests must pass before merging
- Test coverage reports are generated

## Best Practices
1. Write independent tests
2. Use appropriate fixtures
3. Mock external dependencies
4. Follow AAA pattern (Arrange, Act, Assert)
5. Keep tests focused and concise
6. Include both positive and negative test cases
7. Maintain test documentation

## Troubleshooting
Common issues and solutions:
1. Port conflicts: Ensure no other services are using test ports
2. Environment issues: Verify virtual environment is activated
3. Import errors: Check PYTHONPATH includes project root
4. Database errors: Ensure test database is properly configured 