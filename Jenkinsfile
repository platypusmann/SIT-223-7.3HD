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
    PATH                = "${env.HOME}/.local/bin:${env.PATH}"
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

    stage('Setup Python (no venv in CI)') {
      steps {
        sh """
          ${PYTHON_BIN} -m pip install --upgrade pip --user
          # install project (editable if pyproject present) or fallback to requirements.txt
          if [ -f pyproject.toml ]; then
            ${PIP_BIN} install --user -e .
          elif [ -f requirements.txt ]; then
            ${PIP_BIN} install --user -r requirements.txt
          fi
          # test & tooling
          ${PIP_BIN} install --user pytest pytest-cov ruff mypy bandit pip-audit coverage requests fastapi uvicorn || true
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
