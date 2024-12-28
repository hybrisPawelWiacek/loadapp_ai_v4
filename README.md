# LoadApp.AI Project

A modern application featuring Streamlit frontend, Flask-RESTful backend, and SQLite database, following clean architecture principles.

## Technology Stack

- **Frontend**: Streamlit
- **Backend**: Python with Flask-RESTful
- **Database**: SQLite with SQLAlchemy
- **Configuration**: Pydantic for settings management
- **External Services**:
  - OpenAI API Integration
- **Logging**: Structlog for JSON-formatted logs
- **Testing**: Pytest suite with frontend and backend tests

## Local Development Setup

### Prerequisites

- Python 3.12 (recommended) or higher
- pip (Python package installer)
- Git

### Installation Steps

1. Clone the repository:
```bash
git clone [your-repository-url]
cd loadapp4
```

2. Create and activate a virtual environment:
```bash
# Create virtual environment
python3.12 -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
# Create .env file from template
cp template.env .env

# Edit .env file with your configuration:
# OPENAI_API_KEY=your_api_key
# Other settings as needed
```

### Running the Application

The application comes with convenient scripts in the `scripts/` directory:

1. Start the backend server:
```bash
# In one terminal
./scripts/start_backend.sh
```

2. Start the Streamlit frontend:
```bash
# In another terminal
./scripts/start_frontend.sh
```

You can also use the `-r` flag with the frontend script to check/update requirements:
```bash
./scripts/start_frontend.sh -r
```

3. Access the application:
- Frontend: http://localhost:8501
- Backend API: http://localhost:5001/api

### Project Structure

```
loadapp4/
├── backend/
│   ├── app.py              # Flask-RESTful backend
│   └── config.py           # Configuration management
├── frontend/
│   └── streamlit_app.py    # Streamlit frontend
├── scripts/
│   ├── start_backend.sh    # Backend startup script
│   ├── start_frontend.sh   # Frontend startup script
│   └── run_tests.sh        # Test runner script
├── tests/
│   ├── backend/            # Backend tests
│   ├── frontend/           # Frontend tests
│   └── conftest.py         # Test configuration
├── .env                    # Environment variables (not in version control)
├── template.env            # Environment template
├── .gitignore             # Git ignore file
├── README.md              # Project documentation
└── requirements.txt        # Python dependencies
```

### Configuration System

The project uses a robust configuration system based on Pydantic:

1. **Environment Variables**: Managed through `.env` file
2. **Configuration Classes**:
   - `DatabaseSettings`: Database-specific configuration
   - `APISettings`: External API settings (OpenAI, etc.)
   - `ServiceSettings`: Service configuration (ports, hosts, etc.)

Key configuration files:
- `template.env`: Template for environment variables
- `backend/config.py`: Pydantic configuration classes

### Port Configuration

- Backend (Flask): 5001 (Note: 5000 is avoided due to Apple AirTunes conflict)
- Frontend (Streamlit): 8501

### Testing

The project includes a comprehensive test suite with a convenient test runner script:

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

# Show test runner help
./scripts/run_tests.sh --help
```

The test suite includes:
- Backend API tests
- Frontend component tests
- Configuration tests
- Integration tests

## Development Guidelines

1. **Environment Management**:
   - Always use the virtual environment
   - Keep `requirements.txt` updated
   - Use `.env` for environment variables

2. **Code Style**:
   - Follow clean architecture principles
   - Use type hints
   - Follow Google-style docstrings

3. **Testing Best Practices**:
   - Write tests for new features
   - Maintain test coverage above 60%
   - Run tests before committing changes
   - Use appropriate test markers (backend/frontend)

4. **Configuration**:
   - Never commit `.env` files
   - Update `template.env` when adding new configuration options
   - Use the configuration system for all settings

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes (following conventional commit format)
4. Push to the branch
5. Create a Pull Request

## License

[Add license information here]
