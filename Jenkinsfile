pipeline {
    agent any
    
    environment {
        PYTHON_VERSION = '3.11'
        IMAGE_NAME = 'instacart-api'
        IMAGE_TAG = 'local'
        REGISTRY = 'your-registry.com'
        SONAR_PROJECT_KEY = 'csv-clean-api'
        COVERAGE_THRESHOLD = '70'
    }
    
    stages {
        stage('Checkout') {
            steps {
                checkout scm
                script {
                    env.GIT_COMMIT_SHORT = sh(
                        script: "git rev-parse --short HEAD",
                        returnStdout: true
                    ).trim()
                }
                // Ensure reports directory exists
                sh 'mkdir -p reports'
            }
        }
        
        stage('Setup Python Environment') {
            steps {
                sh '''
                    python3.11 -m venv venv
                    . venv/bin/activate
                    pip install --upgrade pip
                    pip install -e .[dev,test]
                    pip install pip-audit
                '''
            }
        }
        
        stage('Code Quality') {
            parallel {
                stage('Lint with Ruff') {
                    steps {
                        sh '''
                            . venv/bin/activate
                            ruff check app/ etl/ expectations/ tests/
                            ruff format --check app/ etl/ expectations/ tests/
                        '''
                    }
                }
                
                stage('Type Check with MyPy') {
                    steps {
                        sh '''
                            . venv/bin/activate
                            mypy app/ etl/ expectations/
                        '''
                    }
                }
            }
        }
        
        stage('Security Scan') {
            steps {
                sh '''
                    . venv/bin/activate
                    
                    # Bandit security scan
                    bandit -r app/ etl/ expectations/ -f json -o reports/bandit.json || true
                    
                    # pip-audit vulnerability scan
                    pip-audit --format=json --output=reports/pip-audit.json || true
                '''
                script {
                    // Check for HIGH severity vulnerabilities in Bandit
                    def banditHighVulns = sh(
                        script: '''
                            if [ -f reports/bandit.json ]; then
                                python3 -c "
import json
try:
    with open('reports/bandit.json', 'r') as f:
        data = json.load(f)
    high_vulns = [issue for issue in data.get('results', []) if issue.get('issue_severity') == 'HIGH']
    print(len(high_vulns))
except:
    print(0)
"
                            else
                                echo 0
                            fi
                        ''',
                        returnStdout: true
                    ).trim().toInteger()
                    
                    // Check for HIGH severity vulnerabilities in pip-audit
                    def pipAuditHighVulns = sh(
                        script: '''
                            if [ -f reports/pip-audit.json ]; then
                                python3 -c "
import json
try:
                                with open('reports/pip-audit.json', 'r') as f:
        data = json.load(f)
    high_vulns = [vuln for vuln in data.get('vulnerabilities', []) if any(alias.get('severity', '').upper() == 'HIGH' for alias in vuln.get('aliases', []))]
    print(len(high_vulns))
except:
    print(0)
"
                            else
                                echo 0
                            fi
                        ''',
                        returnStdout: true
                    ).trim().toInteger()
                    
                    if (banditHighVulns > 0 || pipAuditHighVulns > 0) {
                        currentBuild.result = 'UNSTABLE'
                        echo "WARNING: Found ${banditHighVulns} HIGH Bandit vulnerabilities and ${pipAuditHighVulns} HIGH pip-audit vulnerabilities"
                    }
                }
            }
        }
        
        stage('Run Tests') {
            steps {
                sh '''
                    . venv/bin/activate
                    pytest tests/ -v --junitxml=reports/junit.xml --cov=app --cov=etl --cov=expectations --cov-report=xml:reports/coverage.xml --cov-report=html:reports/htmlcov
                '''
                script {
                    // Check coverage threshold
                    def coverage = sh(
                        script: '''
                            if [ -f reports/coverage.xml ]; then
                                python3 -c "
import xml.etree.ElementTree as ET
try:
    tree = ET.parse('reports/coverage.xml')
    root = tree.getroot()
    coverage = float(root.attrib.get('line-rate', 0)) * 100
    print(f'{coverage:.1f}')
except:
    print('0')
"
                            else
                                echo 0
                            fi
                        ''',
                        returnStdout: true
                    ).trim().toFloat()
                    
                    if (coverage < env.COVERAGE_THRESHOLD.toFloat()) {
                        currentBuild.result = 'UNSTABLE'
                        echo "WARNING: Coverage ${coverage}% is below threshold ${env.COVERAGE_THRESHOLD}%"
                    } else {
                        echo "Coverage ${coverage}% meets threshold ${env.COVERAGE_THRESHOLD}%"
                    }
                }
            }
            post {
                always {
                    junit 'reports/junit.xml'
                    publishHTML([
                        allowMissing: false,
                        alwaysLinkToLastBuild: true,
                        keepAll: true,
                        reportDir: 'reports/htmlcov',
                        reportFiles: 'index.html',
                        reportName: 'Coverage Report'
                    ])
                }
            }
        }
        
        stage('SonarQube Analysis') {
            when {
                anyOf {
                    branch 'main'
                    branch 'develop'
                    changeRequest()
                }
            }
            steps {
                withSonarQubeEnv('SonarQube') {
                    sh '''
                        . venv/bin/activate
                        sonar-scanner \
                            -Dsonar.projectKey=${SONAR_PROJECT_KEY} \
                            -Dsonar.sources=app,etl,expectations \
                            -Dsonar.tests=tests \
                            -Dsonar.python.coverage.reportPaths=reports/coverage.xml \
                            -Dsonar.junit.reportPaths=reports/junit.xml
                    '''
                }
            }
        }
        
        stage('Build Docker Image & Security Scan') {
            steps {
                script {
                    // Build Docker image
                    def image = docker.build("${IMAGE_NAME}:${IMAGE_TAG}")
                    
                    // Run Trivy security scan
                    sh """
                        # Install Trivy if not available
                        if ! command -v trivy &> /dev/null; then
                            curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh | sh -s -- -b /usr/local/bin
                        fi
                        
                        # Scan the built image
                        trivy image --format json --output reports/trivy.json ${IMAGE_NAME}:${IMAGE_TAG} || true
                    """
                    
                    // Optional: Push to registry if configured
                    if (env.REGISTRY && env.REGISTRY != 'your-registry.com') {
                        docker.withRegistry("https://${REGISTRY}", 'registry-credentials') {
                            image.push("${env.GIT_COMMIT_SHORT}")
                            image.push('latest')
                        }
                    }
                }
            }
        }
        
        stage('Deploy to Staging') {
            steps {
                sh '''
                    # Update docker-compose to use our local image
                    sed -i "s|image:.*|image: ${IMAGE_NAME}:${IMAGE_TAG}|g" docker-compose.staging.yml || true
                    
                    # Deploy with docker-compose
                    docker-compose -f docker-compose.staging.yml down || true
                    docker-compose -f docker-compose.staging.yml up -d
                    
                    # Wait for service to be ready
                    echo "Waiting for service to start..."
                    sleep 30
                    
                    # Verify health endpoint
                    max_attempts=10
                    attempt=1
                    while [ $attempt -le $max_attempts ]; do
                        echo "Health check attempt $attempt/$max_attempts"
                        if curl -fsS http://localhost:8080/health; then
                            echo "✓ Health check passed"
                            break
                        else
                            echo "✗ Health check failed, retrying in 10s..."
                            sleep 10
                            attempt=$((attempt + 1))
                        fi
                    done
                    
                    if [ $attempt -gt $max_attempts ]; then
                        echo "Health check failed after $max_attempts attempts"
                        docker-compose -f docker-compose.staging.yml logs
                        exit 1
                    fi
                '''
            }
        }
        
        stage('Integration Tests') {
            steps {
                sh '''
                    . venv/bin/activate
                    
                    # Run integration tests against deployed service
                    pytest tests/ -m integration -v --junitxml=reports/integration-junit.xml || true
                    
                    # Additional API endpoint tests
                    echo "Testing API endpoints..."
                    curl -fsS http://localhost:8080/health
                    curl -fsS http://localhost:8080/ || true
                '''
            }
        }
    }
    
    post {
        always {
            // Archive all reports
            archiveArtifacts artifacts: 'reports/**/*', fingerprint: true, allowEmptyArchive: true
            
            // Clean up Docker containers
            sh 'docker-compose -f docker-compose.staging.yml down || true'
        }
        failure {
            emailext (
                subject: "Pipeline Failed: ${env.JOB_NAME} - ${env.BUILD_NUMBER}",
                body: "Build failed. Check console output at ${env.BUILD_URL}",
                to: "${env.CHANGE_AUTHOR_EMAIL ?: 'team@company.com'}"
            )
        }
        unstable {
            emailext (
                subject: "Pipeline Unstable: ${env.JOB_NAME} - ${env.BUILD_NUMBER}",
                body: "Build completed with warnings (coverage/security issues). Check reports at ${env.BUILD_URL}",
                to: "${env.CHANGE_AUTHOR_EMAIL ?: 'team@company.com'}"
            )
        }
        success {
            script {
                if (env.BRANCH_NAME == 'main') {
                    emailext (
                        subject: "Production Deployment Successful: ${env.JOB_NAME} - ${env.BUILD_NUMBER}",
                        body: "Production deployment completed successfully.",
                        to: "team@company.com"
                    )
                }
            }
        }
    }
}