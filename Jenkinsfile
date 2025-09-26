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
              
              # Check for pip3.11 or create link
              if ! command -v pip3.11 &> /dev/null; then
                if python3.11 -m pip --version &> /dev/null; then
                  echo "pip available via 'python3.11 -m pip'"
                  # Create a pip3.11 wrapper script
                  echo '#!/bin/bash' > $HOME/.local/bin/pip3.11
                  echo 'python3.11 -m pip "$@"' >> $HOME/.local/bin/pip3.11
                  chmod +x $HOME/.local/bin/pip3.11
                else
                  echo "⚠️  pip not immediately available, will bootstrap in next stage"
                fi
              else
                echo "✅ pip3.11 found: $(pip3.11 --version)"
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
            
            # Check Docker
            echo "Checking Docker..."
            if ! command -v docker &> /dev/null; then
              echo "❌ ERROR: Docker not found!"
              echo "SOLUTION: Contact Jenkins admin to install Docker"
              exit 1
            fi
            if ! docker info &> /dev/null; then
              echo "❌ ERROR: Docker daemon not accessible!"
              echo "Current user groups: $(groups)"
              echo "SOLUTION: Add Jenkins user to docker group: sudo usermod -aG docker $(whoami)"
              exit 1
            fi
            echo "✅ Docker accessible: $(docker --version)"
            
            # Check network connectivity
            echo "Checking network connectivity..."
            if ! curl -s --connect-timeout 10 https://pypi.org > /dev/null; then
              echo "❌ ERROR: Cannot reach PyPI!"
              echo "SOLUTION: Check network/firewall settings"
              exit 1
            fi
            echo "✅ Network connectivity OK"
            echo
          '''
        }
        sh """
          # Source Python environment if available
          if [ -f \$HOME/.jenkins_python_env ]; then
            source \$HOME/.jenkins_python_env
          fi
          
          # Bootstrap pip for Python 3.11 with better error handling
          echo "=== PYTHON SETUP ==="
          echo "Using Python: \$(which python3.11)"
          echo "Python version: \$(python3.11 --version)"
          
          # Try multiple methods to ensure pip is available
          if ! python3.11 -m pip --version &> /dev/null; then
            echo "pip not available, attempting installation..."
            
            # Method 1: ensurepip
            python3.11 -m ensurepip --upgrade --user 2>/dev/null || {
              echo "ensurepip failed, trying get-pip.py..."
              
              # Method 2: get-pip.py
              curl -fsSL --retry 3 --retry-delay 5 https://bootstrap.pypa.io/get-pip.py -o get-pip.py || {
                echo "❌ ERROR: Cannot download get-pip.py"
                echo "SOLUTION: Check network connectivity or contact admin"
                exit 1
              }
              
              python3.11 get-pip.py --user || {
                echo "❌ ERROR: get-pip.py installation failed"
                exit 1
              }
              rm -f get-pip.py
            }
          fi
          
          # Verify pip is now working
          if ! python3.11 -m pip --version &> /dev/null; then
            echo "❌ ERROR: pip still not working after installation attempts"
            exit 1
          fi
          echo "✅ pip available: \$(python3.11 -m pip --version)"
          
          # Ensure PATH includes ~/.local/bin
          export PATH="\${HOME}/.local/bin:\${PATH}"
          
          # Upgrade pip
          python3.11 -m pip install --upgrade pip --user --quiet
          
          # Install project dependencies
          echo "Installing project dependencies..."
          if [ -f pyproject.toml ]; then
            python3.11 -m pip install --user -e . --quiet || {
              echo "❌ ERROR: Project installation failed"
              echo "Trying individual dependency installation..."
              python3.11 -m pip install --user fastapi uvicorn pandas pandera --quiet
            }
          elif [ -f requirements.txt ]; then
            python3.11 -m pip install --user -r requirements.txt --quiet
          fi
          
          # Install testing and development tools
          echo "Installing development tools..."
          python3.11 -m pip install --user pytest pytest-cov ruff mypy bandit pip-audit coverage requests --quiet || {
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
              ruff check app/ etl/ expectations/ tests/
              ruff format --check app/ etl/ expectations/ tests/
            """
          }
        }
        stage('MyPy') {
          steps {
            sh "mypy app/ etl/ expectations/ || true"
          }
        }
      }
    }

    stage('Security') {
      steps {
        sh """
          # Bandit JSON
          bandit -q -r app etl expectations -f json -o reports/bandit.json || true

          # pip-audit JSON (nonzero exit if vulns); capture exit for gating
          set +e
          pip-audit -f json -o reports/pip-audit.json
          echo \$? > reports/pip-audit.exit
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
          junit 'reports/junit.xml'
          publishHTML([
            allowMissing: true,
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
      steps {
        script {
          def image = docker.build("${IMAGE_NAME}:${IMAGE_TAG}")
          sh """
            if ! command -v trivy >/dev/null 2>&1; then
              curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh | sh -s -- -b /usr/local/bin
            fi
            trivy image --scanners vuln --format json -o reports/trivy.json ${IMAGE_NAME}:${IMAGE_TAG} || true
          """
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