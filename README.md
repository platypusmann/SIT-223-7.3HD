
```bash
# Setup environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -e .[dev]

# Run ETL pipeline with sample data (for testing)
python -m etl.clean --sample

# Run ETL pipeline with full data (requires Kaggle download)
python -m etl.clean

# Start FastAPI server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### ETL Pipeline Options

```bash
# Use sample data for quick testing
python -m etl.clean --sample

# Use full dataset (default)
python -m etl.clean

# Custom input/output directories
python -m etl.clean --raw-dir /path/to/raw --clean-dir /path/to/clean

# Enable debug logging
python -m etl.clean --sample --log-level DEBUG
```

## 🐳 Docker Run

```bash
# Build image
docker build -t instacart-etl-api .

# Run container
docker run -p 8000:8000 -v $(pwd)/data:/app/data instacart-etl-api
```

## 🔗 API Endpoints

```bash
# Health check
curl http://localhost:8000/health

# Data summary statistics
curl http://localhost:8000/summary

# Filter products by category
curl "http://localhost:8000/filter?category=dairy-eggs&limit=10"

# Latest validation results
curl http://localhost:8000/validations/last
```

## 🧪 Tests & Reports

```bash
# Run tests with coverage
pytest tests/ --junitxml=reports/junit.xml --cov=app --cov=etl --cov-report=xml:reports/coverage.xml

# View reports
open reports/coverage.xml    # Coverage report
open reports/junit.xml       # Test results
```

## 🔄 CI/CD Pipeline Overview

**7-Stage Jenkins Pipeline:**
1. **Checkout** - Git clone and commit info extraction
2. **Setup** - Python environment and dependency installation  
3. **Quality** - Ruff linting, MyPy type checking, security scans
4. **Test** - Pytest execution with coverage reporting
5. **Analysis** - SonarQube code quality and technical debt analysis
6. **Build** - Docker image creation and registry push
7. **Deploy** - Staging deployment and integration testing

## 📸 Evidence Checklist

**Screenshots to capture for submission:**

- [ ] Jenkins pipeline overview (all 7 stages)
- [ ] Successful pipeline execution logs
- [ ] SonarQube dashboard showing code quality metrics
- [ ] Test coverage report (>80% target)
- [ ] API endpoints working (curl responses)
- [ ] Docker container running status
- [ ] ETL pipeline processing raw data
- [ ] Data validation results and schema compliance

**Files to include:**
- [ ] `reports/junit.xml` - Test results
- [ ] `reports/coverage.xml` - Coverage metrics  
- [ ] `sonar-project.properties` - Quality gate config
- [ ] `Jenkinsfile` - Complete pipeline definition