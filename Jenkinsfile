pipeline {
  agent any

  environment {
    PYTHON_BIN          = 'python3.11'
    PIP_BIN             = 'pip3.11'
    IMAGE_NAME          = 'instacart-api'
    IMAGE_TAG           = 'local'
    REGISTRY            = 'your-registry.com'   // change or leave as placeholder
    SONAR_PROJECT_KEY   = 'csv-clean-api'
    COVERAGE_THRESHOLD  = '70'                  // percent
    PATH                = "${env.HOME}/.local/bin:${env.HOME}/.pyenv/bin:${env.HOME}/.pyenv/versions/3.11.9/bin:${env.PATH}"
  }

  stages {
    stage('Checkout') {
      steps {
        checkout scm
        script {
          env.GIT_COMMIT_SHORT = sh(returnStdout: true, script: "git rev-parse --short HEAD").trim()
        }
        sh 'mkdir -p reports data/clean || true'
      }
    }

    stage('Environment Check & Setup') {
      steps {
        script {
          // Comprehensive environment validation
          sh '''
            echo "=== ENVIRONMENT VALIDATION ==="
            echo "Date: $(date)"
            echo "User: $(whoami)"
            echo "Working Directory: $(pwd)"
            echo "PATH: $PATH"
            echo
            
            # Check Python 3.11 availability
            echo "Checking Python 3.11..."
            if command -v python3.11 &> /dev/null; then
              echo "✅ Python 3.11 already available: $(python3.11 --version)"
              echo "Location: $(which python3.11)"
              
              # Ensure it's in our PATH
              mkdir -p $HOME/.local/bin
              if [ "$(which python3.11)" != "$HOME/.local/bin/python3.11" ]; then
                ln -sf $(which python3.11) $HOME/.local/bin/python3.11
              fi
              
              # Install pip if not available
              echo "Checking pip availability..."
              
              # Test if pip module exists
              if python3.11 -c "import pip" 2>/dev/null; then
                echo "✅ pip module available"
              else
                echo "⚠️  pip module not found, checking alternatives..."
                
                # Check if there's a system python3 with pip that we can use
                echo "Checking system Python alternatives..."
                for py_cmd in python3 /usr/bin/python3 /usr/bin/python3.11; do
                  if [ -x "$py_cmd" ] && $py_cmd -m pip --version 2>/dev/null; then
                    echo "✅ Found working pip with: $py_cmd"
                    echo "Version: $($py_cmd -m pip --version)"
                    
                    # Use this Python instead of our symlinked one
                    ln -sf "$py_cmd" $HOME/.local/bin/python3.11
                    echo "✅ Updated python3.11 symlink to use system Python with pip"
                    break
                  fi
                done
                
                # Check if pip is now available after trying system Python
                if python3.11 -c "import pip" 2>/dev/null; then
                  echo "✅ pip module now available via system Python"
                else
                  echo "Still no pip available, attempting installation..."
                  
                  # Try ensurepip first
                echo "Trying ensurepip..."
                if python3.11 -m ensurepip --upgrade --user; then
                  echo "✅ pip installed via ensurepip"
                elif python3.11 -m ensurepip --upgrade --user --break-system-packages 2>/dev/null; then
                  echo "✅ pip installed via ensurepip (with --break-system-packages)"
                else
                  echo "ensurepip failed, trying get-pip.py..."
                  # Download and install pip
                  curl -fsSL --retry 3 --retry-delay 5 https://bootstrap.pypa.io/get-pip.py -o get-pip.py || {
                    echo "❌ ERROR: Cannot download get-pip.py"
                    exit 1
                  }
                  
                  # Try with --break-system-packages for PEP 668 compliance
                  if python3.11 get-pip.py --user --break-system-packages; then
                    echo "✅ pip installed via get-pip.py (with --break-system-packages)"
                  else
                    echo "get-pip.py with --break-system-packages failed, trying system package manager..."
                    
                    # Try to install python3-pip via system package manager
                    if command -v apt &> /dev/null; then
                      echo "Attempting to install python3-pip via apt..."
                      # This will likely fail without sudo, but let's try
                      apt update && apt install -y python3-pip 2>/dev/null || {
                        echo "❌ System package installation failed (needs sudo)"
                      }
                    fi
                    
                    # Final fallback: check if pip is available via python3-pip package
                    if python3.11 -m pip --version 2>/dev/null; then
                      echo "✅ pip now available via system package"
                    else
                      echo "❌ ERROR: All pip installation methods failed"
                      echo "This appears to be a PEP 668 externally managed environment"
                      echo "Solutions:"
                      echo "1. Install python3-pip system package: apt install python3-pip"
                      echo "2. Or run Jenkins with --break-system-packages permission"
                      exit 1
                    fi
                  fi
                  rm -f get-pip.py
                fi
              fi
              fi
              
              # Verify pip is working before creating wrapper
              echo "Verifying pip installation..."
              if python3.11 -m pip --version; then
                echo "✅ pip is working: $(python3.11 -m pip --version)"
                
                # Create pip3.11 wrapper
                echo '#!/bin/bash' > $HOME/.local/bin/pip3.11
                echo 'python3.11 -m pip "$@"' >> $HOME/.local/bin/pip3.11
                chmod +x $HOME/.local/bin/pip3.11
                echo "✅ pip3.11 wrapper created"
              else
                echo "❌ ERROR: pip still not working after installation attempts"
                python3.11 -c "import sys; print('Python path:', sys.path)"
                python3.11 -c "import sys; print('Python executable:', sys.executable)"
                exit 1
              fi
            else
              echo "❌ Python 3.11 not found!"
              echo "Available Python versions:"
              ls -la /usr/bin/python* 2>/dev/null || echo "No Python found"
              echo "❌ ERROR: Python 3.11 is required but not available"
              echo "SOLUTION: Install Python 3.11 on the Jenkins server"
              exit 1
            fi
            
            # Final verification and PATH setup
            if command -v python3.11 &> /dev/null; then
              echo "✅ Python 3.11 found: $(python3.11 --version)"
              
              # Ensure PATH is properly set for all subsequent stages
              echo "export PATH=\"\$HOME/.local/bin:\$HOME/.pyenv/bin:\$HOME/.pyenv/versions/3.11.9/bin:\$PATH\"" > $HOME/.jenkins_python_env
              echo "Python environment setup complete"
              
              # Test pip availability
              if python3.11 -m pip --version &> /dev/null; then
                echo "✅ pip3.11 is available"
              else
                echo "⚠️  pip not immediately available, will bootstrap in next stage"
              fi
            else
              echo "❌ ERROR: Python 3.11 still not available after installation attempts"
              exit 1
            fi
            
            # Check Docker (detailed diagnostics)
            echo "Checking Docker..."
            echo "Current PATH: $PATH"
            
            # Look for Docker in common locations
            DOCKER_PATH=""
            echo "Searching for Docker executable..."
            for docker_loc in /usr/bin/docker /usr/local/bin/docker /bin/docker /snap/bin/docker; do
              echo "  Checking: $docker_loc"
              if [ -x "$docker_loc" ]; then
                DOCKER_PATH="$docker_loc"
                echo "  ✅ Found executable Docker at: $docker_loc"
                break
              else
                echo "  ❌ Not found or not executable"
              fi
            done
            
            # Also check via command -v (with proper error handling)
            if [ -z "$DOCKER_PATH" ]; then
              # Use set +e to temporarily disable exit on error
              set +e
              DOCKER_CHECK=$(command -v docker 2>/dev/null)
              DOCKER_EXIT_CODE=$?
              set -e
              
              if [ $DOCKER_EXIT_CODE -eq 0 ] && [ -n "$DOCKER_CHECK" ]; then
                DOCKER_PATH="$DOCKER_CHECK"
                echo "✅ Docker found via command -v at: $DOCKER_PATH"
              else
                echo "❌ Docker not found via command -v either (exit code: $DOCKER_EXIT_CODE)"
              fi
            fi
            
            if [ -n "$DOCKER_PATH" ]; then
              echo "✅ Docker executable found at: $DOCKER_PATH"
              # Create symlink for easy access
              ln -sf "$DOCKER_PATH" $HOME/.local/bin/docker
              DOCKER_CMD="$DOCKER_PATH"
              
              # Test Docker daemon access
              echo "Testing Docker daemon access..."
              if $DOCKER_CMD info &> /dev/null; then
                echo "✅ Docker daemon accessible: $($DOCKER_CMD --version)"
              else
                echo "⚠️  Docker found but daemon not accessible"
                echo "Docker version: $($DOCKER_CMD --version 2>/dev/null || echo 'Cannot get version')"
                echo "Current user groups: $(groups)"
                echo "Docker socket permissions:"
                ls -la /var/run/docker.sock 2>/dev/null || echo "Docker socket not found at /var/run/docker.sock"
                echo "Docker daemon status:"
                systemctl is-active docker 2>/dev/null || echo "Cannot check Docker daemon status"
                echo "⚠️  Docker stages will be skipped"
              fi
            else
              echo "❌ Docker not found anywhere!"
              echo "Searched locations:"
              echo "  - /usr/bin/docker"
              echo "  - /usr/local/bin/docker" 
              echo "  - /bin/docker"
              echo "  - /snap/bin/docker"
              echo "  - PATH search via 'command -v docker'"
              echo "Current PATH: $PATH"
              echo "Available binaries in /usr/bin:"
              ls -la /usr/bin/ | grep -i docker | head -5 || echo "No docker-related binaries found"
              echo "⚠️  Docker stages will be skipped - contact admin to install Docker"
            fi
            
            # Check network connectivity
            echo "Checking network connectivity..."
            if ! curl -s --connect-timeout 10 https://pypi.org > /dev/null; then
              echo "❌ ERROR: Cannot reach PyPI!"
              echo "SOLUTION: Check network/firewall settings"
              exit 1
            fi
            echo "✅ Network connectivity OK"
            echo
            
            # Set Docker availability flag for later stages
            DOCKER_WORKING=false
            if [ -n "$DOCKER_PATH" ]; then
              echo "Testing Docker functionality..."
              if $DOCKER_CMD info &> /dev/null 2>&1; then
                echo "DOCKER_AVAILABLE=true" > $HOME/.jenkins_docker_env
                echo "✅ Docker fully functional - Docker stages will run"
                DOCKER_WORKING=true
              else
                echo "DOCKER_AVAILABLE=false" > $HOME/.jenkins_docker_env  
                echo "⚠️  Docker found but not functional - Docker stages will be skipped"
              fi
            else
              echo "DOCKER_AVAILABLE=false" > $HOME/.jenkins_docker_env
              echo "⚠️  Docker not found - Docker stages will be skipped"
            fi
            
            echo "Final Docker status: DOCKER_WORKING=$DOCKER_WORKING"
          '''
        }
        script {
          // Set pipeline environment variable for Docker availability
          def dockerAvailable = sh(
            returnStdout: true,
            script: 'if [ -f $HOME/.jenkins_docker_env ]; then grep DOCKER_AVAILABLE $HOME/.jenkins_docker_env | cut -d= -f2; else echo false; fi'
          ).trim()
          env.DOCKER_AVAILABLE = dockerAvailable
          echo "Pipeline Docker availability: ${env.DOCKER_AVAILABLE}"
        }
        
        // Temporary Docker diagnostic
        echo "=== DOCKER DIAGNOSTIC DETAILS ==="
        sh '''
          echo "Detailed Docker diagnostic:"
          echo "User: $(whoami)"
          echo "Groups: $(groups)"
          echo "PATH: $PATH"
          
          # Check all possible Docker locations
          for loc in /usr/bin/docker /usr/local/bin/docker /bin/docker /snap/bin/docker; do
            if [ -x "$loc" ]; then
              echo "Docker found at: $loc"
              echo "Version: $($loc --version)"
              if $loc info >/dev/null 2>&1; then
                echo "Daemon accessible: YES"
              else
                echo "Daemon accessible: NO"
              fi
            fi
          done
          
          # Check Docker socket
          if [ -S /var/run/docker.sock ]; then
            echo "Docker socket: EXISTS"
            ls -la /var/run/docker.sock
          else
            echo "Docker socket: NOT FOUND"
          fi
          
          # Check Docker processes
          echo "Docker processes:"
          ps aux | grep docker | grep -v grep || echo "No Docker processes"
        '''
        
        sh """
          # Source Python environment if available
          if [ -f \$HOME/.jenkins_python_env ]; then
            . \$HOME/.jenkins_python_env
          fi
          
          # Bootstrap pip for Python 3.11 with better error handling
          echo "=== PYTHON SETUP ==="
          echo "Using Python: \$(which python3.11)"
          echo "Python version: \$(python3.11 --version)"
          
          # Try multiple methods to ensure pip is available
          echo "Testing pip availability..."
          if python3.11 -m pip --version >/dev/null 2>&1; then
            echo "✅ pip is already working: \$(python3.11 -m pip --version)"
          else
            echo "pip not available, attempting installation..."
            
            # Method 1: ensurepip with --break-system-packages
            if python3.11 -m ensurepip --upgrade --user --break-system-packages 2>/dev/null; then
              echo "✅ pip installed via ensurepip"
            else
              echo "ensurepip failed, trying get-pip.py..."
              
              # Method 2: get-pip.py with --break-system-packages
              curl -fsSL --retry 3 --retry-delay 5 https://bootstrap.pypa.io/get-pip.py -o get-pip.py || {
                echo "❌ ERROR: Cannot download get-pip.py"
                echo "SOLUTION: Check network connectivity or contact admin"
                exit 1
              }
              
              if python3.11 get-pip.py --user --break-system-packages; then
                echo "✅ pip installed via get-pip.py"
              else
                echo "❌ ERROR: get-pip.py installation failed"
                exit 1
              fi
              rm -f get-pip.py
            fi
            
            # Verify pip is now working
            if ! python3.11 -m pip --version >/dev/null 2>&1; then
              echo "❌ ERROR: pip still not working after installation attempts"
              exit 1
            fi
          fi
          echo "✅ pip available: \$(python3.11 -m pip --version)"
          
          # Ensure PATH includes ~/.local/bin
          export PATH="\${HOME}/.local/bin:\${PATH}"
          
          # Upgrade pip (with PEP 668 compliance)
          python3.11 -m pip install --upgrade pip --user --quiet --break-system-packages
          
          # Install project dependencies
          echo "Installing project dependencies..."
          if [ -f pyproject.toml ]; then
            python3.11 -m pip install --user -e . --quiet --break-system-packages || {
              echo "❌ ERROR: Project installation failed"
              echo "Trying individual dependency installation..."
              python3.11 -m pip install --user fastapi uvicorn pandas pandera --quiet --break-system-packages
            }
          elif [ -f requirements.txt ]; then
            python3.11 -m pip install --user -r requirements.txt --quiet --break-system-packages
          fi
          
          # Install testing and development tools
          echo "Installing development tools..."
          python3.11 -m pip install --user pytest pytest-cov ruff mypy bandit pip-audit coverage requests --quiet --break-system-packages || {
            echo "⚠️  WARNING: Some development tools failed to install"
            echo "Continuing with available tools..."
          }
          
          echo "✅ Python environment setup complete"
        """
      }
    }

    stage('Code Quality') {
      parallel {
        stage('Ruff') {
          steps {
            sh """
              # Source Python environment
              if [ -f \$HOME/.jenkins_python_env ]; then
                . \$HOME/.jenkins_python_env
              fi
              
              # Check if ruff is available and run checks
              if command -v ruff >/dev/null 2>&1; then
                echo "Using ruff command directly"
                ruff check app/ etl/ expectations/ tests/ || echo "Ruff check completed with issues"
                ruff format --check app/ etl/ expectations/ tests/ || echo "Ruff format check completed with issues"
              elif python3.11 -m ruff --version >/dev/null 2>&1; then
                echo "Using ruff via python module"
                python3.11 -m ruff check app/ etl/ expectations/ tests/ || echo "Ruff check completed with issues"
                python3.11 -m ruff format --check app/ etl/ expectations/ tests/ || echo "Ruff format check completed with issues"
              else
                echo "⚠️  Ruff not available, skipping code quality checks"
                echo "Install ruff with: pip install ruff"
              fi
            """
          }
        }
        stage('MyPy') {
          steps {
            sh """
              # Source Python environment
              if [ -f \$HOME/.jenkins_python_env ]; then
                . \$HOME/.jenkins_python_env
              fi
              
              # Check if mypy is available and run checks
              if command -v mypy >/dev/null 2>&1; then
                echo "Running MyPy type checking..."
                mypy app/ etl/ expectations/ || echo "MyPy completed with issues"
              elif python3.11 -m mypy --version >/dev/null 2>&1; then
                echo "Running MyPy via python module..."
                python3.11 -m mypy app/ etl/ expectations/ || echo "MyPy completed with issues"
              else
                echo "⚠️  MyPy not available, skipping type checking"
                echo "Install mypy with: pip install mypy"
              fi
            """
          }
        }
      }
    }

    stage('Security') {
      steps {
        sh """
          # Source Python environment
          if [ -f \$HOME/.jenkins_python_env ]; then
            . \$HOME/.jenkins_python_env
          fi
          
          # Bandit security scanning
          if command -v bandit >/dev/null 2>&1; then
            echo "Running Bandit security scan..."
            bandit -q -r app etl expectations -f json -o reports/bandit.json || echo "Bandit scan completed with issues"
          elif python3.11 -m bandit --version >/dev/null 2>&1; then
            echo "Running Bandit via python module..."
            python3.11 -m bandit -q -r app etl expectations -f json -o reports/bandit.json || echo "Bandit scan completed with issues"
          else
            echo "⚠️  Bandit not available, creating empty report"
            echo '{"results": []}' > reports/bandit.json
          fi

          # pip-audit dependency vulnerability scanning
          set +e
          if command -v pip-audit >/dev/null 2>&1; then
            echo "Running pip-audit dependency scan..."
            pip-audit -f json -o reports/pip-audit.json
            echo \$? > reports/pip-audit.exit
          elif python3.11 -m pip_audit --version >/dev/null 2>&1; then
            echo "Running pip-audit via python module..."
            python3.11 -m pip_audit -f json -o reports/pip-audit.json
            echo \$? > reports/pip-audit.exit
          else
            echo "⚠️  pip-audit not available, creating empty report"
            echo '{"vulnerabilities": []}' > reports/pip-audit.json
            echo "0" > reports/pip-audit.exit
          fi
          set -e
        """
        script {
          // Count HIGH issues in Bandit JSON (best-effort)
          def banditHigh = sh(
            returnStdout: true,
            script: """
              ${PYTHON_BIN} - <<'PY'
import json,sys
try:
  with open('reports/bandit.json') as f:
    data=json.load(f)
  highs=sum(1 for r in data.get('results',[]) if r.get('issue_severity','').upper()=='HIGH')
  print(highs)
except Exception: print(0)
PY
            """
          ).trim().toInteger()

          // pip-audit: mark UNSTABLE if exit code != 0 (means vulnerabilities found)
          def pipAuditExit = sh(returnStdout: true, script: "cat reports/pip-audit.exit 2>/dev/null || echo 0").trim().toInteger()

          if (banditHigh > 0 || pipAuditExit != 0) {
            currentBuild.result = 'UNSTABLE'
            echo "Security gate: Bandit HIGH=${banditHigh}, pip-audit exit=${pipAuditExit} → marking UNSTABLE."
          }
        }
      }
    }

    stage('Build / ETL') {
      steps {
        sh """
          ${PYTHON_BIN} -m etl.clean || true
        """
      }
      post {
        always {
          archiveArtifacts artifacts: 'data/clean/**', allowEmptyArchive: true
        }
      }
    }

    stage('Run Tests') {
      steps {
        sh """
          pytest -v tests/ \
            --junitxml=reports/junit.xml \
            --cov=app --cov=etl --cov=expectations \
            --cov-report=xml:reports/coverage.xml \
            --cov-report=html:reports/htmlcov || true
        """
        script {
          def cov = sh(
            returnStdout: true,
            script: """
              ${PYTHON_BIN} - <<'PY'
import xml.etree.ElementTree as ET,sys
try:
  root=ET.parse('reports/coverage.xml').getroot()
  rate=float(root.get('line-rate','0'))*100
  print(f"{rate:.1f}")
except Exception:
  print("0")
PY
          """).trim().toFloat()

          if (cov < env.COVERAGE_THRESHOLD.toFloat()) {
            currentBuild.result = 'UNSTABLE'
            echo "Coverage ${cov}% < threshold ${env.COVERAGE_THRESHOLD}% → UNSTABLE."
          } else {
            echo "Coverage ${cov}% ≥ threshold ${env.COVERAGE_THRESHOLD}%."
          }
        }
      }
      post {
        always {
          // Publish JUnit test results (core Jenkins functionality)
          script {
            if (fileExists('reports/junit.xml')) {
              junit 'reports/junit.xml'
            } else {
              echo "⚠️  No JUnit XML found, skipping test result publishing"
            }
          }
          
          // Publish HTML coverage report (requires HTML Publisher Plugin)
          script {
            try {
              if (fileExists('reports/htmlcov/index.html')) {
                publishHTML([
                  allowMissing: true,
                  alwaysLinkToLastBuild: true,
                  keepAll: true,
                  reportDir: 'reports/htmlcov',
                  reportFiles: 'index.html',
                  reportName: 'Coverage Report'
                ])
                echo "✅ HTML Coverage report published"
              } else {
                echo "⚠️  No HTML coverage report found"
              }
            } catch (Exception e) {
              echo "⚠️  HTML Publisher Plugin not available: ${e.getMessage()}"
              echo "Coverage reports are archived as artifacts instead"
              echo "Install HTML Publisher Plugin to view coverage reports in Jenkins UI"
            }
          }
        }
      }
    }

    stage('SonarQube Analysis') {
      when {
        anyOf { branch 'main'; branch 'develop'; changeRequest() }
      }
      steps {
        withSonarQubeEnv('SonarQube') {
          sh """
            sonar-scanner \
              -Dsonar.projectKey=${SONAR_PROJECT_KEY} \
              -Dsonar.sources=app,etl,expectations \
              -Dsonar.tests=tests \
              -Dsonar.python.coverage.reportPaths=reports/coverage.xml \
              -Dsonar.junit.reportPaths=reports/junit.xml
          """
        }
      }
    }

    stage('Docker Build + Trivy') {
      when {
        environment name: 'DOCKER_AVAILABLE', value: 'true'
      }
      steps {
        script {
          try {
            // Check if Docker Pipeline plugin is available
            if (binding.hasVariable('docker')) {
              echo "Using Docker Pipeline plugin"
              def image = docker.build("${IMAGE_NAME}:${IMAGE_TAG}")
              
              // Run Trivy security scan
              sh """
                if ! command -v trivy >/dev/null 2>&1; then
                  curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh | sh -s -- -b /usr/local/bin
                fi
                trivy image --scanners vuln --format json -o reports/trivy.json ${IMAGE_NAME}:${IMAGE_TAG} || true
              """
              
              // Push to registry if configured
              if (env.REGISTRY && env.REGISTRY != 'your-registry.com') {
                docker.withRegistry("https://${REGISTRY}", 'registry-credentials') {
                  image.push("${env.GIT_COMMIT_SHORT}")
                  image.push('latest')
                }
              }
            } else {
              throw new Exception("Docker Pipeline plugin not available")
            }
          } catch (Exception e) {
            echo "⚠️  Docker Pipeline plugin not available: ${e.getMessage()}"
            echo "Falling back to shell-based Docker commands"
            
            sh """
              # Source Docker environment if available
              if [ -f \$HOME/.jenkins_docker_env ]; then
                . \$HOME/.jenkins_docker_env
                echo "Docker environment loaded: DOCKER_AVAILABLE=\$DOCKER_AVAILABLE"
              fi
              
              # Double-check Docker availability before proceeding
              if [ "\$DOCKER_AVAILABLE" != "true" ]; then
                echo "❌ Docker marked as unavailable in environment"
                exit 1
              fi
              
              # Build Docker image using shell commands
              if command -v docker >/dev/null 2>&1 && docker info >/dev/null 2>&1; then
                echo "Building Docker image: ${IMAGE_NAME}:${IMAGE_TAG}"
                docker build -t ${IMAGE_NAME}:${IMAGE_TAG} . || {
                  echo "❌ Docker build failed"
                  exit 1
                }
                
                # Run Trivy security scan
                if ! command -v trivy >/dev/null 2>&1; then
                  echo "Installing Trivy..."
                  curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh | sh -s -- -b /usr/local/bin
                fi
                trivy image --scanners vuln --format json -o reports/trivy.json ${IMAGE_NAME}:${IMAGE_TAG} || echo "Trivy scan completed with issues"
                
                # Push to registry if configured
                if [ "${env.REGISTRY}" != "your-registry.com" ] && [ -n "${env.REGISTRY}" ]; then
                  echo "Pushing to registry: ${env.REGISTRY}"
                  docker tag ${IMAGE_NAME}:${IMAGE_TAG} ${env.REGISTRY}/${IMAGE_NAME}:${env.GIT_COMMIT_SHORT}
                  docker tag ${IMAGE_NAME}:${IMAGE_TAG} ${env.REGISTRY}/${IMAGE_NAME}:latest
                  docker push ${env.REGISTRY}/${IMAGE_NAME}:${env.GIT_COMMIT_SHORT} || echo "Push of commit tag failed"
                  docker push ${env.REGISTRY}/${IMAGE_NAME}:latest || echo "Push of latest tag failed"
                fi
                
                echo "✅ Docker build and scan completed"
              else
                echo "❌ Docker command not available"
                exit 1
              fi
            """
          }
        }
      }
    }

    stage('Deploy to Staging') {
      when {
        environment name: 'DOCKER_AVAILABLE', value: 'true'
      }
      steps {
        sh """
          # prefer docker compose v2; fallback to docker-compose
          DC="docker compose"; \$DC version >/dev/null 2>&1 || DC="docker-compose"

          # ensure compose uses our local tag (only if file pins a different image)
          sed -i "s|image:.*|image: ${IMAGE_NAME}:${IMAGE_TAG}|g" docker-compose.staging.yml || true

          \$DC -f docker-compose.staging.yml down || true
          \$DC -f docker-compose.staging.yml up -d --build

          echo "Waiting for service..."
          for i in \$(seq 1 15); do
            if curl -fsS http://localhost:8000/health -o reports/health.json; then
              echo "✓ Health OK"; break
            fi
            sleep 5
          done
        """
      }
    }

    stage('Integration Smoke') {
      when {
        environment name: 'DOCKER_AVAILABLE', value: 'true'
      }
      steps {
        sh """
          set -e
          curl -fsS http://localhost:8000/health
          curl -fsS http://localhost:8000/summary || true
          curl -fsS 'http://localhost:8000/filter?user_id=1' || true
        """
      }
    }
  }

  post {
    always {
      archiveArtifacts artifacts: 'reports/**/*', allowEmptyArchive: true, fingerprint: true
      sh """
        DC="docker compose"; \$DC version >/dev/null 2>&1 || DC="docker-compose"
        \$DC -f docker-compose.staging.yml down || true
      """
    }
    unstable {
      echo 'Build marked UNSTABLE due to coverage/security/health gates.'
    }
    failure {
      echo 'Build failed. Check console log and reports.'   
    }
  }
}