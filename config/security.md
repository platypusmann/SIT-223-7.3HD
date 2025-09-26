# Security scanning configuration
# This file defines security scan configurations

# Bandit configuration (embedded in pyproject.toml)
# See pyproject.toml [tool.bandit] section

# pip-audit configuration
# Run: pip-audit --format=json --output=reports/pip-audit.json

# Trivy configuration  
# Run: trivy image --format json --output reports/trivy.json <image_name>

# For Jenkins pipeline security scanning:
# 1. Bandit - Python code security analysis
# 2. pip-audit - Python dependency vulnerability scanning  
# 3. Trivy - Container image vulnerability scanning