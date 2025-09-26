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
        VENV_PATH = 'venv'
        
        // Docker configuration
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
                    echo "Setting up Python ${PYTHON_VERSION} environment..."
                }
                
                sh '''
                    # Check if Python is available
                    python3 --version || python --version
                    
                    # Bootstrap pip if missing
                    python3 -m ensurepip --upgrade 2>/dev/null || python -m ensurepip --upgrade 2>/dev/null || true
                    
                    # Ensure pip is available
                    python3 -m pip --version || python -m pip --version
                    
                    # Create virtual environment
                    python3 -m venv ${VENV_PATH} || python -m venv ${VENV_PATH}
                    
                    # Activate virtual environment and upgrade pip
                    . ${VENV_PATH}/bin/activate
                    pip install --upgrade pip setuptools wheel
                    
                    # Install dependencies
                    pip install -r requirements.txt
                    
                    # Verify installation
                    pip list
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
                    . ${VENV_PATH}/bin/activate
                    
                    # Move raw data to correct location if needed
                    if [ -d "data" ] && [ ! -d "data/raw" ]; then
                        echo "Moving data files to data/raw/"
                        mkdir -p data/raw
                        mv data/*.csv data/raw/ 2>/dev/null || true
                    fi
                    
                    # Run ETL pipeline
                    echo "Starting ETL pipeline..."
                    python -m etl.clean --raw-data-path data/raw --clean-data-path ${DATA_CLEAN_DIR}
                    
                    # Verify ETL outputs
                    ls -la ${DATA_CLEAN_DIR}/
                    
                    if [ -f "${DATA_CLEAN_DIR}/instacart_clean.csv" ]; then
                        echo "ETL completed successfully - clean data file created"
                        wc -l ${DATA_CLEAN_DIR}/instacart_clean.csv
                    else
                        echo "ERROR: ETL failed - no clean data file found"
                        exit 1
                    fi
                    
                    if [ -f "${DATA_CLEAN_DIR}/validation_results.json" ]; then
                        echo "Validation results:"
                        cat ${DATA_CLEAN_DIR}/validation_results.json
                    fi
                '''
            }
        }
        
        stage('Test') {
            steps {
                script {
                    echo "=== STAGE 4: TEST ==="
                    echo "Running unit tests with coverage reporting..."
                }
                
                sh '''
                    . ${VENV_PATH}/bin/activate
                    
                    # Run tests with coverage
                    echo "Running pytest with coverage..."
                    pytest --junitxml=${REPORTS_DIR}/junit.xml \\
                           --cov=app --cov=etl \\
                           --cov-report=xml:${REPORTS_DIR}/coverage.xml \\
                           --cov-report=html:${REPORTS_DIR}/coverage \\
                           --cov-report=term-missing \\
                           -v
                    
                    # Extract coverage percentage
                    COVERAGE_PERCENT=$(python -c "
import xml.etree.ElementTree as ET
tree = ET.parse('${REPORTS_DIR}/coverage.xml')
root = tree.getroot()
coverage = float(root.attrib['line-rate']) * 100
print(f'{coverage:.1f}')
")
                    echo "Coverage: ${COVERAGE_PERCENT}%"
                    echo "${COVERAGE_PERCENT}" > ${REPORTS_DIR}/coverage_percent.txt
                '''
            }
            
            post {
                always {
                    // Publish test results
                    publishTestResults testResultsPattern: 'reports/junit.xml'
                    
                    // Publish coverage report
                    publishHTML([
                        allowMissing: false,
                        alwaysLinkToLastBuild: true,
                        keepAll: true,
                        reportDir: 'reports/coverage',
                        reportFiles: 'index.html',
                        reportName: 'Coverage Report'
                    ])
                }
            }
        }
        
        stage('Code Quality') {
            steps {
                script {
                    echo "=== STAGE 5: CODE QUALITY ==="
                    echo "Running code quality checks..."
                }
                
                sh '''
                    . ${VENV_PATH}/bin/activate
                    
                    # Run ruff linting
                    echo "Running ruff linting..."
                    ruff check . --output-format=json > ${REPORTS_DIR}/ruff.json || true
                    ruff check . --output-format=text || true
                    
                    # Run mypy type checking
                    echo "Running mypy type checking..."
                    mypy app/ etl/ --junit-xml ${REPORTS_DIR}/mypy.xml || true
                    mypy app/ etl/ || true
                    
                    # Generate code quality summary
                    echo "Code Quality Summary:" > ${REPORTS_DIR}/quality_summary.txt
                    echo "===================" >> ${REPORTS_DIR}/quality_summary.txt
                    echo "Ruff issues: $(cat ${REPORTS_DIR}/ruff.json | python -c 'import json,sys; print(len(json.load(sys.stdin)))' 2>/dev/null || echo 'N/A')" >> ${REPORTS_DIR}/quality_summary.txt
                    echo "MyPy issues: $(grep -c 'error:' ${REPORTS_DIR}/mypy.xml 2>/dev/null || echo '0')" >> ${REPORTS_DIR}/quality_summary.txt
                    
                    cat ${REPORTS_DIR}/quality_summary.txt
                '''
            }
        }
        
        stage('Security') {
            steps {
                script {
                    echo "=== STAGE 6: SECURITY ==="
                    echo "Running security scans..."
                }
                
                sh '''
                    . ${VENV_PATH}/bin/activate
                    
                    # Run Bandit security scan
                    echo "Running Bandit security scan..."
                    bandit -r app/ etl/ -f json -o ${REPORTS_DIR}/bandit.json || true
                    bandit -r app/ etl/ || true
                    
                    # Run pip-audit for dependency vulnerabilities
                    echo "Running pip-audit..."
                    pip-audit --format=json --output=${REPORTS_DIR}/pip-audit.json || true
                    pip-audit || true
                    
                    # Create security summary
                    echo "Security Scan Summary:" > ${REPORTS_DIR}/security_summary.txt
                    echo "=====================" >> ${REPORTS_DIR}/security_summary.txt
                    
                    # Count Bandit issues
                    BANDIT_ISSUES=$(cat ${REPORTS_DIR}/bandit.json | python -c 'import json,sys; data=json.load(sys.stdin); print(len(data.get("results", [])))' 2>/dev/null || echo '0')
                    echo "Bandit issues: ${BANDIT_ISSUES}" >> ${REPORTS_DIR}/security_summary.txt
                    
                    # Count pip-audit vulnerabilities
                    PIP_AUDIT_ISSUES=$(cat ${REPORTS_DIR}/pip-audit.json | python -c 'import json,sys; data=json.load(sys.stdin); print(len(data.get("vulnerabilities", [])))' 2>/dev/null || echo '0')
                    echo "Dependency vulnerabilities: ${PIP_AUDIT_ISSUES}" >> ${REPORTS_DIR}/security_summary.txt
                    
                    cat ${REPORTS_DIR}/security_summary.txt
                    
                    # Set build status based on security issues
                    if [ "${BANDIT_ISSUES}" -gt "0" ] || [ "${PIP_AUDIT_ISSUES}" -gt "0" ]; then
                        echo "SECURITY_ISSUES=true" > ${REPORTS_DIR}/security_status.env
                    else
                        echo "SECURITY_ISSUES=false" > ${REPORTS_DIR}/security_status.env
                    fi
                '''
            }
        }
        
        stage('Docker Build & Security Scan') {
            steps {
                script {
                    echo "=== STAGE 7: DOCKER BUILD & TRIVY SCAN ==="
                    echo "Building Docker image and scanning for vulnerabilities..."
                }
                
                sh '''
                    # Build Docker image
                    echo "Building Docker image..."
                    docker build -t ${DOCKER_IMAGE}:${DOCKER_TAG} .
                    docker tag ${DOCKER_IMAGE}:${DOCKER_TAG} ${DOCKER_IMAGE}:latest
                    
                    # Install Trivy if not available
                    if ! command -v trivy &> /dev/null; then
                        echo "Installing Trivy..."
                        curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh | sh -s -- -b /usr/local/bin
                    fi
                    
                    # Run Trivy security scan
                    echo "Running Trivy container scan..."
                    trivy image --format json --output ${REPORTS_DIR}/trivy.json ${DOCKER_IMAGE}:${DOCKER_TAG} || true
                    trivy image --format table ${DOCKER_IMAGE}:${DOCKER_TAG} || true
                    
                    # Create Trivy summary
                    TRIVY_CRITICAL=$(cat ${REPORTS_DIR}/trivy.json | python -c 'import json,sys; data=json.load(sys.stdin); print(sum(len([v for v in result.get("Vulnerabilities", []) if v.get("Severity") == "CRITICAL"]) for result in data.get("Results", [])))' 2>/dev/null || echo '0')
                    TRIVY_HIGH=$(cat ${REPORTS_DIR}/trivy.json | python -c 'import json,sys; data=json.load(sys.stdin); print(sum(len([v for v in result.get("Vulnerabilities", []) if v.get("Severity") == "HIGH"]) for result in data.get("Results", [])))' 2>/dev/null || echo '0')
                    
                    echo "Trivy Critical: ${TRIVY_CRITICAL}" >> ${REPORTS_DIR}/security_summary.txt
                    echo "Trivy High: ${TRIVY_HIGH}" >> ${REPORTS_DIR}/security_summary.txt
                    
                    # Update security status
                    if [ "${TRIVY_CRITICAL}" -gt "0" ]; then
                        echo "TRIVY_CRITICAL=true" >> ${REPORTS_DIR}/security_status.env
                    fi
                '''
            }
        }
        
        stage('Deploy') {
            steps {
                script {
                    echo "=== STAGE 8: DEPLOY ==="
                    echo "Deploying to staging environment..."
                }
                
                sh '''
                    # Stop existing containers
                    docker-compose -f docker-compose.staging.yml down || true
                    
                    # Deploy with docker-compose
                    echo "Starting staging deployment..."
                    DOCKER_IMAGE_TAG=${DOCKER_TAG} docker-compose -f docker-compose.staging.yml up -d
                    
                    # Wait for application to be ready
                    echo "Waiting for application to start..."
                    sleep 30
                    
                    # Check if container is running
                    docker ps | grep instacart-api-staging
                '''
            }
        }
        
        stage('Monitoring & Health Checks') {
            steps {
                script {
                    echo "=== STAGE 9: MONITORING & HEALTH CHECKS ==="
                    echo "Running health checks and monitoring tests..."
                }
                
                sh '''
                    # Health check endpoint
                    echo "Testing health endpoint..."
                    HEALTH_RESPONSE=$(curl -s -w "%{http_code}" http://localhost:8000/health)
                    echo "Health check response: ${HEALTH_RESPONSE}"
                    
                    if echo "${HEALTH_RESPONSE}" | grep -q "200"; then
                        echo "Health check passed"
                        echo "HEALTH_CHECK=passed" > ${REPORTS_DIR}/health_status.txt
                    else
                        echo "Health check failed"
                        echo "HEALTH_CHECK=failed" > ${REPORTS_DIR}/health_status.txt
                    fi
                    
                    # Test API endpoints
                    echo "Testing API endpoints..."
                    
                    # Test summary endpoint
                    curl -s http://localhost:8000/summary > ${REPORTS_DIR}/api_summary_test.json || echo "Summary endpoint failed"
                    
                    # Test filter endpoint
                    curl -s "http://localhost:8000/filter?limit=5" > ${REPORTS_DIR}/api_filter_test.json || echo "Filter endpoint failed"
                    
                    # Test validation endpoint
                    curl -s http://localhost:8000/validations/last > ${REPORTS_DIR}/api_validation_test.json || echo "Validation endpoint failed"
                    
                    # Create monitoring summary
                    echo "API Monitoring Summary:" > ${REPORTS_DIR}/monitoring_summary.txt
                    echo "======================" >> ${REPORTS_DIR}/monitoring_summary.txt
                    echo "Health Check: $(cat ${REPORTS_DIR}/health_status.txt | cut -d'=' -f2)" >> ${REPORTS_DIR}/monitoring_summary.txt
                    echo "Summary endpoint: $([ -f ${REPORTS_DIR}/api_summary_test.json ] && echo 'OK' || echo 'FAILED')" >> ${REPORTS_DIR}/monitoring_summary.txt
                    echo "Filter endpoint: $([ -f ${REPORTS_DIR}/api_filter_test.json ] && echo 'OK' || echo 'FAILED')" >> ${REPORTS_DIR}/monitoring_summary.txt
                    echo "Validation endpoint: $([ -f ${REPORTS_DIR}/api_validation_test.json ] && echo 'OK' || echo 'FAILED')" >> ${REPORTS_DIR}/monitoring_summary.txt
                    
                    cat ${REPORTS_DIR}/monitoring_summary.txt
                '''
            }
        }
        
        stage('Coverage Gate') {
            steps {
                script {
                    echo "=== STAGE 10: COVERAGE GATE ==="
                    echo "Checking coverage threshold..."
                }
                
                sh '''
                    # Check coverage threshold
                    if [ -f "${REPORTS_DIR}/coverage_percent.txt" ]; then
                        COVERAGE=$(cat ${REPORTS_DIR}/coverage_percent.txt)
                        echo "Current coverage: ${COVERAGE}%"
                        echo "Required coverage: ${COVERAGE_THRESHOLD}%"
                        
                        if [ $(echo "${COVERAGE} < ${COVERAGE_THRESHOLD}" | bc -l) -eq 1 ]; then
                            echo "Coverage ${COVERAGE}% is below threshold ${COVERAGE_THRESHOLD}%"
                            echo "COVERAGE_GATE=failed" > ${REPORTS_DIR}/coverage_gate.txt
                        else
                            echo "Coverage gate passed"
                            echo "COVERAGE_GATE=passed" > ${REPORTS_DIR}/coverage_gate.txt
                        fi
                    else
                        echo "Coverage file not found - marking as failed"
                        echo "COVERAGE_GATE=failed" > ${REPORTS_DIR}/coverage_gate.txt
                    fi
                '''
                
                script {
                    // Check if coverage gate failed and mark build as unstable
                    def coverageGate = readFile('reports/coverage_gate.txt').trim()
                    if (coverageGate.contains('failed')) {
                        currentBuild.result = 'UNSTABLE'
                        echo "Build marked as UNSTABLE due to low coverage"
                    }
                }
            }
        }
        
        stage('Release') {
            when {
                anyOf {
                    branch 'main'
                    branch 'master'
                }
            }
            steps {
                script {
                    echo "=== STAGE 11: RELEASE ==="
                    echo "Preparing release artifacts..."
                }
                
                sh '''
                    # Create release summary
                    echo "Release Summary for Build ${BUILD_NUMBER}" > ${REPORTS_DIR}/release_summary.txt
                    echo "=======================================" >> ${REPORTS_DIR}/release_summary.txt
                    echo "Git Commit: ${GIT_COMMIT}" >> ${REPORTS_DIR}/release_summary.txt
                    echo "Docker Image: ${DOCKER_IMAGE}:${DOCKER_TAG}" >> ${REPORTS_DIR}/release_summary.txt
                    echo "Build Date: $(date)" >> ${REPORTS_DIR}/release_summary.txt
                    echo "" >> ${REPORTS_DIR}/release_summary.txt
                    
                    # Add quality metrics to release summary
                    cat ${REPORTS_DIR}/quality_summary.txt >> ${REPORTS_DIR}/release_summary.txt
                    echo "" >> ${REPORTS_DIR}/release_summary.txt
                    cat ${REPORTS_DIR}/security_summary.txt >> ${REPORTS_DIR}/release_summary.txt
                    echo "" >> ${REPORTS_DIR}/release_summary.txt
                    cat ${REPORTS_DIR}/monitoring_summary.txt >> ${REPORTS_DIR}/release_summary.txt
                    
                    cat ${REPORTS_DIR}/release_summary.txt
                    
                    # Tag Docker image for release (if no critical security issues)
                    if [ ! -f "${REPORTS_DIR}/security_status.env" ] || ! grep -q "TRIVY_CRITICAL=true" ${REPORTS_DIR}/security_status.env; then
                        docker tag ${DOCKER_IMAGE}:${DOCKER_TAG} ${DOCKER_IMAGE}:release-${BUILD_NUMBER}
                        echo "Docker image tagged for release: ${DOCKER_IMAGE}:release-${BUILD_NUMBER}"
                    else
                        echo "Release skipped due to critical security vulnerabilities"
                    fi
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
            
            // Clean up Docker images (keep last 5 builds)
            sh '''
                # Clean old images
                docker images ${DOCKER_IMAGE} --format "table {{.Repository}}:{{.Tag}}" | grep -v latest | tail -n +6 | xargs -r docker rmi || true
            '''
        }
        
        success {
            script {
                echo "✅ Pipeline completed successfully!"
                
                // Check for security issues and mark as unstable if found
                sh '''
                    if [ -f "${REPORTS_DIR}/security_status.env" ]; then
                        if grep -q "SECURITY_ISSUES=true\\|TRIVY_CRITICAL=true" ${REPORTS_DIR}/security_status.env; then
                            echo "Security issues detected - build will be marked as unstable"
                            exit 1
                        fi
                    fi
                '''
            }
        }
        
        failure {
            echo "❌ Pipeline failed!"
        }
        
        unstable {
            echo "⚠️ Pipeline completed with warnings (unstable build)"
        }
        
        cleanup {
            // Clean workspace but keep reports
            sh 'rm -rf ${VENV_PATH} || true'
        }
    }
}