# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-01-28

### Added
- Initial release of dt-toolbox
- Single-line monitoring initialization with `init_monitoring()`
- Decorator-based monitoring with `@monitor`
- Structured JSON logging with rotation
- Unhandled exception capture and reporting
- SMTP email notifications
- Webhook notifications (Slack and Google Chat)
- Log upload to S3/MinIO storage backends
- PII redaction with configurable patterns
- Configuration via env vars, config file, or function arguments
- Comprehensive test suite with 80%+ coverage
- Examples demonstrating success and failure scenarios
- CI/CD pipeline with GitHub Actions
- Pre-commit hooks for code quality
- Docker support

### Features
- **Easy Integration**: One-line initialization
- **Flexible Configuration**: Environment variables > config file > function arguments
- **Structured Logging**: JSON format for easy ingestion by log aggregators
- **Smart Alerting**: Configurable notifications on success/failure
- **Security**: Built-in PII redaction and secrets management
- **Storage**: Automatic log upload for large files
- **Testing**: Comprehensive test coverage with mocked external services

[0.1.0]: https://github.com/abrahamkoloboe27/dt-toolbox/releases/tag/v0.1.0
