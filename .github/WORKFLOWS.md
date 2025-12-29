# CI/CD Workflows for Agentic Models

This repository includes comprehensive GitHub Actions workflows for Continuous Integration and Continuous Deployment (CI/CD) of Agentic AI models.

## 📋 Available Workflows

### 1. CI - Agentic Models (`ci.yml`)
**Triggers:** Push/PR to `main` or `develop` branches, manual dispatch

**Jobs:**
- **Lint Code:** Runs Ruff, Black, isort, and mypy to ensure code quality
- **Run Tests:** Tests across Python 3.9, 3.10, 3.11, and 3.12 with pytest and coverage reporting
- **Build Package:** Builds the Python package and uploads artifacts

### 2. Model Validation (`model-validation.yml`)
**Triggers:** Push/PR to `main` or `develop` (when Python or model files change), manual dispatch

**Jobs:**
- **Validate Agentic Models:** Checks model file structure, validates Python syntax, and tests imports
- **Validate Time Series Components:** Ensures time series libraries are available for USD/COP analysis

### 3. Security Scan (`security.yml`)
**Triggers:** Push/PR to `main` or `develop`, daily at 2 AM UTC, manual dispatch

**Jobs:**
- **Dependency Security Check:** Runs Safety and pip-audit to check for vulnerable dependencies
- **Code Security Scan:** Uses Bandit to scan for security issues in code
- **Secret Scanning:** Uses Gitleaks to detect exposed secrets
- **CodeQL Analysis:** GitHub's semantic code analysis for security vulnerabilities

### 4. Code Quality (`code-quality.yml`)
**Triggers:** Push/PR to `main` or `develop`, manual dispatch

**Jobs:**
- **Code Quality Analysis:** Calculates cyclomatic complexity, maintainability index, and runs Pylint/Flake8
- **Documentation Check:** Validates docstring coverage and style
- **Dependency Graph:** Generates and uploads dependency tree visualization

### 5. Model Deployment (`deploy.yml`)
**Triggers:** Release published, manual dispatch with environment selection

**Jobs:**
- **Prepare Models:** Validates and packages models for deployment
- **Deploy to Staging:** Deploys models to staging environment
- **Deploy to Production:** Deploys models to production (manual approval required)
- **Post-Deployment Health Check:** Validates deployment success

## 🚀 Usage

### Running Workflows Manually

All workflows can be triggered manually:

1. Go to the "Actions" tab in GitHub
2. Select the workflow you want to run
3. Click "Run workflow"
4. For deployment, select the target environment (staging/production)

### Automatic Triggers

Workflows automatically run on:
- Every push to `main` or `develop` branches
- Every pull request to `main` or `develop` branches
- Daily security scans at 2 AM UTC
- When a new release is published

## 🔧 Configuration

### Python Versions
The test suite runs on Python 3.9, 3.10, 3.11, and 3.12 to ensure compatibility.

### Branch Protection
It's recommended to configure branch protection rules for `main` and `develop` to require:
- CI workflow to pass
- Model validation to pass
- Security scan to pass
- At least one review approval

### Secrets
Some workflows may require secrets to be configured:
- `CODECOV_TOKEN`: For uploading coverage reports (optional)
- Additional secrets for deployment to staging/production environments

## 📊 Status Badges

Add these badges to your README to show workflow status:

```markdown
![CI Status](https://github.com/carlosjimenez88M/agentic-news-trm/workflows/CI%20-%20Agentic%20Models/badge.svg)
![Security Scan](https://github.com/carlosjimenez88M/agentic-news-trm/workflows/Security%20Scan/badge.svg)
![Model Validation](https://github.com/carlosjimenez88M/agentic-news-trm/workflows/Model%20Validation/badge.svg)
```

## 🛠️ Development

### Local Testing
Before pushing, you can run similar checks locally:

```bash
# Install development dependencies
pip install ruff black isort mypy pytest pytest-cov bandit safety

# Run linting
ruff check .
black --check .
isort --check-only .

# Run tests
pytest tests/ --cov

# Run security checks
bandit -r .
safety check
```

## 📝 Notes

- Workflows are designed to be graceful when run on an empty repository (e.g., no tests or models yet)
- Model validation focuses on the USD/COP exchange rate analysis use case
- Security scanning includes both dependency and code-level vulnerability detection
- Deployment workflows support both staging and production environments with proper gates
