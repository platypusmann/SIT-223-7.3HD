# Instacart Data API - SIT223 Task 7.3HD

A complete end-to-end CI/CD pipeline for processing and serving Instacart dataset through a REST API.

## 🏗️ Architecture Overview

```
📦 Project Structure
├── 📂 app/                    # FastAPI application
│   ├── main.py               # API endpoints
│   └── __init__.py
├── 📂 etl/                   # ETL pipeline
│   ├── clean.py              # Data processing
│   └── __init__.py
├── 📂 tests/                 # Test suite
│   ├── test_etl.py          # ETL tests
│   ├── test_api.py          # API tests
│   ├── test_integration.py  # Integration tests
│   └── conftest.py          # Test configuration
├── 📂 data/
│   ├── raw/                 # Raw CSV files (not in repo)
│   └── clean/               # Processed data
├── 📂 reports/              # Generated reports
├── 📂 config/               # Configuration files
├── 🐳 Dockerfile           # Container configuration
├── 🐳 docker-compose.staging.yml
├── 🔧 Jenkinsfile          # CI/CD pipeline
├── 📋 requirements.txt     # Python dependencies
└── 📚 README.md            # This file
```

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Docker & Docker Compose
- Git

### 1. Local Development Setup

```bash
# Clone repository
git clone <your-repo-url>
cd csv-clean-api

# Move your Instacart CSV files to data/raw/
mkdir -p data/raw
# Copy: aisles.csv, departments.csv, orders.csv, products.csv, order_products__*.csv

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run ETL pipeline
python -m etl.clean --raw-data-path data/raw --clean-data-path data/clean

# Start API server
uvicorn app.main:app --reload --port 8000
```

### 2. Docker Deployment

```bash
# Build and run with Docker Compose
docker-compose -f docker-compose.staging.yml up --build

# API will be available at http://localhost:8000
```

### 3. Running Tests

```bash
# Run all tests with coverage
pytest

# Run specific test categories
pytest -m unit        # Unit tests only
pytest -m integration # Integration tests only
pytest -m "not slow"  # Skip slow tests

# Generate coverage report
pytest --cov=app --cov=etl --cov-report=html
```

## 📡 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | API information |
| `/health` | GET | Health check with data availability |
| `/summary` | GET | Dataset summary statistics |
| `/filter` | GET | Filter and query dataset |
| `/validations/last` | GET | Last ETL validation results |
| `/docs` | GET | Interactive API documentation |

### Example API Usage

```bash
# Health check
curl http://localhost:8000/health

# Get dataset summary
curl http://localhost:8000/summary

# Filter products by department
curl "http://localhost:8000/filter?department=produce&limit=10"

# Get validation results
curl http://localhost:8000/validations/last
```

## 🔧 Jenkins Pipeline

The CI/CD pipeline includes **7 comprehensive stages**:

### Stage Overview
1. **Build** - Setup environment & run ETL
2. **Test** - Unit tests with coverage reporting
3. **Code Quality** - Ruff linting & MyPy type checking
4. **Security** - Bandit, pip-audit, Trivy scans
5. **Deploy** - Docker staging deployment
6. **Release** - Tag and prepare artifacts
7. **Monitoring** - Health checks and API validation

### Pipeline Features
- ✅ JUnit XML test reports
- 📊 Coverage reporting with 70% threshold
- 🔍 Security vulnerability scanning
- 🐳 Docker image building and scanning
- 📈 Quality gate enforcement
- 🚨 Build status management (UNSTABLE for warnings)

### Artifacts Generated
- `reports/junit.xml` - Test results
- `reports/coverage.xml` - Coverage report
- `reports/bandit.json` - Security scan results
- `reports/trivy.json` - Container vulnerability scan
- `data/clean/` - Processed dataset

## 🛠️ Development Workflow

### Code Quality Standards
```bash
# Lint code
ruff check .

# Type checking
mypy app/ etl/

# Security scan
bandit -r app/ etl/

# Format code (optional)
black app/ etl/ tests/
```

### ETL Pipeline Details

The ETL pipeline (`etl/clean.py`) performs:
1. **Data Loading** - Reads CSV files from `data/raw/`
2. **Data Merging** - Joins products, aisles, departments
3. **Data Validation** - Schema validation and quality checks
4. **Data Enhancement** - Computed fields and analytics
5. **Output Generation** - Clean CSV + validation JSON

### API Design

FastAPI application features:
- **Pydantic models** for request/response validation
- **Async endpoints** for better performance
- **Error handling** with proper HTTP status codes
- **CORS support** for frontend integration
- **Health checks** for container orchestration

## 🔒 Security & Quality

### Security Measures
- 🛡️ **Bandit** - Python security linting
- 🔍 **pip-audit** - Dependency vulnerability scanning
- 🐳 **Trivy** - Container image security scanning
- 👤 **Non-root Docker user** for container security

### Quality Assurance
- 📏 **Ruff** - Fast Python linter
- 🔍 **MyPy** - Static type checking
- 🧪 **Pytest** - Comprehensive test suite
- 📊 **Coverage** - 70% minimum threshold

## 🐳 Docker Configuration

### Multi-stage Build
- Base: Python 3.11 slim
- Security: Non-root user
- Health checks: Built-in endpoint monitoring
- Optimization: Layer caching for faster builds

### Staging Environment
- Port: 8000
- Health checks: 30s intervals
- Volume mounts: Data persistence
- Network: Isolated bridge network

## 📊 Monitoring & Observability

### Health Monitoring
- Application health endpoint
- Container health checks
- API endpoint validation
- Data availability verification

### Metrics Collection
- Test coverage metrics
- Code quality scores
- Security vulnerability counts
- API response times

## 🚨 Troubleshooting

### Common Issues

**ETL Pipeline Fails:**
```bash
# Check data files exist
ls -la data/raw/

# Check Python environment
python --version
pip list

# Run with verbose logging
python -m etl.clean --raw-data-path data/raw --clean-data-path data/clean
```

**API Won't Start:**
```bash
# Check port availability
netstat -an | grep 8000

# Check data files
ls -la data/clean/

# Run with debug mode
uvicorn app.main:app --reload --log-level debug
```

**Docker Issues:**
```bash
# Check container logs
docker logs instacart-api-staging

# Check container health
docker ps
docker inspect instacart-api-staging
```

### Jenkins Pipeline Issues

**Pipeline Fails at ETL Stage:**
- Ensure raw data files are in `data/raw/`
- Check Python environment setup
- Verify file permissions

**Tests Fail:**
- Check test data availability
- Verify virtual environment activation
- Review test logs in Jenkins console

**Security Scans Mark Build Unstable:**
- Review Bandit findings in `reports/bandit.json`
- Check pip-audit results for dependency vulnerabilities
- Examine Trivy scan for container vulnerabilities

## 📚 Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)
- [Jenkins Pipeline Documentation](https://www.jenkins.io/doc/book/pipeline/)
- [Instacart Dataset](https://www.kaggle.com/c/instacart-market-basket-analysis)

## 👥 Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

## 📄 License

This project is created for educational purposes (SIT223 Task 7.3HD).

---

**Built with ❤️ for SIT223 High Distinction Task**