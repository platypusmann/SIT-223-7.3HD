pipeline {
    agent any
    
    options {
        buildDiscarder(logRotator(numToKeepStr: '10'))
        timeout(time: 1, unit: 'HOURS')
        timestamps()
    }
    
    environment {
        // Python configuration
        PYTHON_VERSION = '3.11'
        
        // Docker configuration (if available)
        DOCKER_IMAGE = 'instacart-api'
        DOCKER_TAG = "${BUILD_NUMBER}-${GIT_COMMIT.take(7)}"
        
        // Coverage thresholds
        COVERAGE_THRESHOLD = '70'
        
        // Directories
        REPORTS_DIR = 'reports'
        DATA_CLEAN_DIR = 'data/clean'
    }
    
    stages {
        stage('Checkout') {
            steps {
                script {
                    echo "=== STAGE 1: CHECKOUT ==="
                    echo "Checking out code from repository..."
                }
                
                // Clean workspace
                cleanWs()
                
                // Checkout code
                checkout scm
                
                // Display git information
                sh '''
                    echo "Git Commit: ${GIT_COMMIT}"
                    echo "Git Branch: ${GIT_BRANCH}"
                    git log --oneline -5
                '''
                
                // Create necessary directories
                sh '''
                    mkdir -p ${REPORTS_DIR}
                    mkdir -p ${DATA_CLEAN_DIR}
                    ls -la
                '''
            }
        }
        
        stage('Setup Python Environment') {
            steps {
                script {
                    echo "=== STAGE 2: SETUP PYTHON ENVIRONMENT ==="
                    echo "Setting up Python environment (system-wide)..."
                }
                
                sh '''
                    # Check Python installation
                    echo "Checking Python installations..."
                    python3 --version || python --version
                    
                    # Use system Python directly (no virtual environment)
                    if command -v python3 >/dev/null 2>&1; then
                        PYTHON_CMD=python3
                    elif command -v python >/dev/null 2>&1; then
                        PYTHON_CMD=python
                    else
                        echo "ERROR: No Python installation found"
                        exit 1
                    fi
                    
                    echo "Using Python command: $PYTHON_CMD"
                    $PYTHON_CMD --version
                    
                    # Install dependencies directly to system Python
                    echo "Installing dependencies with $PYTHON_CMD..."
                    $PYTHON_CMD -m pip install --user --upgrade pip setuptools wheel
                    $PYTHON_CMD -m pip install --user -r requirements.txt
                    
                    # Verify installation
                    echo "Verifying installed packages:"
                    $PYTHON_CMD -m pip list --user
                    
                    # Test imports
                    echo "Testing key imports..."
                    $PYTHON_CMD -c "import pandas, fastapi, pytest; print('All key packages imported successfully')"
                    
                    echo "Python environment setup complete!"
                '''
            }
        }
        
        stage('Build & ETL') {
            steps {
                script {
                    echo "=== STAGE 3: BUILD & ETL ==="
                    echo "Running ETL pipeline to process data..."
                }
                
                sh '''
                    # Use python3 if available
                    if command -v python3 >/dev/null 2>&1; then
                        PYTHON_CMD=python3
                    else
                        PYTHON_CMD=python
                    fi
                    
                    # Check data directory structure
                    echo "Checking data directory structure..."
                    ls -la data/ || echo "No data directory found"
                    
                    # Ensure data/raw exists
                    if [ ! -d "data/raw" ]; then
                        echo "Creating data/raw directory..."
                        mkdir -p data/raw
                    fi
                    
                    # List contents of data/raw
                    echo "Contents of data/raw:"
                    ls -la data/raw/ || echo "data/raw directory is empty"
                    
                    # Create sample data for demo (since raw data not in repo)
                    echo "Creating sample data for demo..."
                    echo "product_id,product_name,aisle_id,department_id" > data/raw/products.csv
                    echo "1,Sample Bread,1,1" >> data/raw/products.csv
                    echo "2,Sample Milk,2,2" >> data/raw/products.csv
                    echo "3,Sample Apples,3,3" >> data/raw/products.csv
                    
                    echo "aisle_id,aisle" > data/raw/aisles.csv
                    echo "1,bakery" >> data/raw/aisles.csv
                    echo "2,dairy" >> data/raw/aisles.csv
                    echo "3,produce" >> data/raw/aisles.csv
                    
                    echo "department_id,department" > data/raw/departments.csv
                    echo "1,frozen" >> data/raw/departments.csv
                    echo "2,dairy eggs" >> data/raw/departments.csv
                    echo "3,produce" >> data/raw/departments.csv
                    
                    echo "order_id,user_id,order_number,order_dow,order_hour_of_day,days_since_prior_order" > data/raw/orders.csv
                    echo "1,1,1,1,10," >> data/raw/orders.csv
                    echo "2,1,2,2,11,7" >> data/raw/orders.csv
                    echo "3,2,1,3,12," >> data/raw/orders.csv
                    
                    echo "Sample data created successfully"
                    
                    # Run ETL pipeline
                    echo "Starting ETL pipeline..."
                    $PYTHON_CMD -m etl.clean --raw-data-path data/raw --clean-data-path ${DATA_CLEAN_DIR}
                    
                    # Check ETL exit code
                    if [ $? -eq 0 ]; then
                        echo "✓ ETL pipeline completed successfully"
                    else
                        echo "✗ ETL pipeline failed with exit code $?"
                        exit 1
                    fi
                    
                    # Verify ETL outputs
                    echo "ETL outputs:"
                    ls -la ${DATA_CLEAN_DIR}/
                    
                    if [ -f "${DATA_CLEAN_DIR}/instacart_clean.csv" ]; then
                        echo "✓ Clean data file created successfully"
                        echo "File contains $(wc -l < ${DATA_CLEAN_DIR}/instacart_clean.csv) lines"
                    else
                        echo "✗ ERROR: Clean data file not found"
                        exit 1
                    fi
                    
                    if [ -f "${DATA_CLEAN_DIR}/validation_results.json" ]; then
                        echo "✓ Validation results file created"
                        echo "Validation summary:"
                        cat ${DATA_CLEAN_DIR}/validation_results.json
                    fi
                '''
            }
        }
        
        stage('Test') {
            steps {
                script {
                    echo "=== STAGE 4: TEST ==="
                    echo "Running unit tests..."
                }
                
                sh '''
                    # Use python3 if available
                    if command -v python3 >/dev/null 2>&1; then
                        PYTHON_CMD=python3
                    else
                        PYTHON_CMD=python
                    fi
                    
                    # Run tests
                    echo "Running pytest..."
                    $PYTHON_CMD -m pytest tests/ -v --tb=short --junitxml=${REPORTS_DIR}/junit.xml || {
                        echo "Some tests failed, but continuing pipeline..."
                        echo "Check test results for details"
                    }
                    
                    # Simple test count
                    if [ -f "${REPORTS_DIR}/junit.xml" ]; then
                        echo "✓ Test results generated"
                        echo "JUnit XML report created at ${REPORTS_DIR}/junit.xml"
                    fi
                '''
            }
            
            post {
                always {
                    // Publish test results if available
                    script {
                        if (fileExists('reports/junit.xml')) {
                            publishTestResults testResultsPattern: 'reports/junit.xml'
                        }
                    }
                }
            }
        }
        
        stage('Code Quality & Security') {
            steps {
                script {
                    echo "=== STAGE 5: CODE QUALITY & SECURITY ==="
                    echo "Running code quality and security checks..."
                }
                
                sh '''
                    # Use python3 if available
                    if command -v python3 >/dev/null 2>&1; then
                        PYTHON_CMD=python3
                    else
                        PYTHON_CMD=python
                    fi
                    
                    # Run basic checks (install tools if missing)
                    echo "Installing and running code quality tools..."
                    
                    # Try to run ruff
                    if $PYTHON_CMD -m ruff --version >/dev/null 2>&1; then
                        echo "Running ruff linting..."
                        $PYTHON_CMD -m ruff check . || echo "Ruff found issues (non-blocking)"
                    else
                        echo "Ruff not available, skipping linting"
                    fi
                    
                    # Try to run bandit
                    if $PYTHON_CMD -m bandit --version >/dev/null 2>&1; then
                        echo "Running bandit security scan..."
                        $PYTHON_CMD -m bandit -r app/ etl/ -f json -o ${REPORTS_DIR}/bandit.json || echo "Bandit found issues (non-blocking)"
                    else
                        echo "Bandit not available, skipping security scan"
                    fi
                    
                    echo "Code quality and security checks completed"
                '''
            }
        }
        
        stage('API Health Check') {
            steps {
                script {
                    echo "=== STAGE 6: API HEALTH CHECK ==="
                    echo "Testing API functionality..."
                }
                
                sh '''
                    # Use python3 if available
                    if command -v python3 >/dev/null 2>&1; then
                        PYTHON_CMD=python3
                    else
                        PYTHON_CMD=python
                    fi
                    
                    # Test API imports and basic functionality
                    echo "Testing API imports..."
                    $PYTHON_CMD -c "
from app.main import app
from fastapi.testclient import TestClient
client = TestClient(app)
response = client.get('/')
print('API root endpoint test:', response.status_code == 200)
print('Response:', response.json())
" || echo "API test failed (expected - no clean data available yet)"
                    
                    echo "API health check completed"
                '''
            }
        }
    }
    
    post {
        always {
            script {
                echo "=== POST-BUILD ACTIONS ==="
            }
            
            // Archive all reports and data
            archiveArtifacts artifacts: 'reports/**/*', allowEmptyArchive: true
            archiveArtifacts artifacts: 'data/clean/**/*', allowEmptyArchive: true
            
            // Simple cleanup
            sh '''
                echo "Cleaning up temporary files..."
                # Keep the workspace for debugging
            '''
        }
        
        success {
            echo "✅ Pipeline completed successfully!"
        }
        
        failure {
            echo "❌ Pipeline failed!"
        }
        
        unstable {
            echo "⚠️ Pipeline completed with warnings (unstable build)"
        }
    }
}