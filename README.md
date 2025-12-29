# agentic-news-trm

This project focuses on Agentic AI and Time Series analysis to understand the behavior of the USD/COP exchange rate. It prioritizes a national perspective specifically domestic events within Colombia to assess their correlation with market volatility.

## CI/CD Workflows

This repository includes comprehensive GitHub Actions workflows for automated testing, security scanning, code quality checks, and deployment:

- **CI Pipeline**: Automated testing across Python 3.9-3.12, linting, and package building
- **Model Validation**: Specialized validation for Agentic AI models and time series components
- **Security Scanning**: Daily automated security checks with CodeQL, Bandit, and dependency auditing
- **Code Quality**: Complexity analysis, documentation checks, and maintainability tracking
- **Deployment**: Automated deployment to staging and production environments

See [.github/WORKFLOWS.md](.github/WORKFLOWS.md) for detailed documentation on all available workflows.
