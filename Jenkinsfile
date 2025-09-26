pipeline {
    agent any
    
    environment {
        PYTHON_VERSION = '3.11'
        IMAGE_NAME = 'csv-clean-api'
        REGISTRY = 'your-registry.com'
        SONAR_PROJECT_KEY = 'csv-clean-api'
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
            }
        }
        
        stage('Setup Python Environment') {
            steps {
                sh '''
                    python3.11 -m venv venv
                    . venv/bin/activate
                    pip install --upgrade pip
                    pip install -e .[dev,test]
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
                    pip install bandit safety
                    bandit -r app/ etl/ expectations/ -f json -o bandit-report.json || true
                    safety check --json --output safety-report.json || true
                '''
                archiveArtifacts artifacts: '*-report.json', fingerprint: true
            }
        }
        
        stage('Run Tests') {
            steps {
                sh '''
                    . venv/bin/activate
                    pytest tests/ -v --junitxml=test-results.xml --cov=app --cov=etl --cov=expectations --cov-report=xml --cov-report=html
                '''
            }
            post {
                always {
                    junit 'test-results.xml'
                    publishHTML([
                        allowMissing: false,
                        alwaysLinkToLastBuild: true,
                        keepAll: true,
                        reportDir: 'htmlcov',
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
                            -Dsonar.python.coverage.reportPaths=coverage.xml \
                            -Dsonar.junit.reportPaths=test-results.xml
                    '''
                }
            }
        }
        
        stage('Build Docker Image') {
            steps {
                script {
                    def image = docker.build("${IMAGE_NAME}:${env.GIT_COMMIT_SHORT}")
                    docker.withRegistry("https://${REGISTRY}", 'registry-credentials') {
                        image.push()
                        image.push('latest')
                    }
                }
            }
        }
        
        stage('Deploy to Staging') {
            when {
                branch 'develop'
            }
            steps {
                sh '''
                    docker-compose -f docker-compose.staging.yml down
                    docker-compose -f docker-compose.staging.yml pull
                    docker-compose -f docker-compose.staging.yml up -d
                '''
            }
        }
        
        stage('Integration Tests') {
            when {
                branch 'develop'
            }
            steps {
                sh '''
                    . venv/bin/activate
                    sleep 30  # Wait for service to be ready
                    pytest tests/ -m integration -v
                '''
            }
        }
        
        stage('Deploy to Production') {
            when {
                branch 'main'
            }
            steps {
                input message: 'Deploy to production?', ok: 'Deploy'
                sh '''
                    # Add production deployment commands here
                    echo "Deploying to production..."
                '''
            }
        }
    }
    
    post {
        always {
            cleanWs()
        }
        failure {
            emailext (
                subject: "Pipeline Failed: ${env.JOB_NAME} - ${env.BUILD_NUMBER}",
                body: "Build failed. Check console output at ${env.BUILD_URL}",
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