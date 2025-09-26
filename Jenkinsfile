stage('Setup Python (bootstrap pip if missing)') {
  environment {
    PYTHON_BIN = 'python3.11'
    PIP_BIN    = 'pip3.11'
  }
  steps {
    sh """
      set -e
      # ensure PATH includes user site executables
      export PATH="\$HOME/.local/bin:\$PATH"

      # 1) Make sure pip exists for python3.11
      if ! ${PYTHON_BIN} -m pip --version >/dev/null 2>&1; then
        echo '[Bootstrap] pip not found for python3.11 — trying ensurepip...'
        if ${PYTHON_BIN} -m ensurepip --version >/dev/null 2>&1; then
          ${PYTHON_BIN} -m ensurepip --upgrade
        else
          echo '[Bootstrap] ensurepip not available — using get-pip.py'
          curl -sS https://bootstrap.pypa.io/get-pip.py -o /tmp/get-pip.py
          ${PYTHON_BIN} /tmp/get-pip.py --user
        fi
      fi

      # 2) Upgrade pip and install deps (no venv in CI)
      ${PYTHON_BIN} -m pip install --upgrade pip --user

      if [ -f pyproject.toml ]; then
        ${PYTHON_BIN} -m pip install --user -e .
      elif [ -f requirements.txt ]; then
        ${PYTHON_BIN} -m pip install --user -r requirements.txt
      fi

      # 3) Tooling for the rest of the stages
      ${PYTHON_BIN} -m pip install --user \
        pytest pytest-cov ruff mypy bandit pip-audit coverage requests fastapi uvicorn || true
    """
  }
}
