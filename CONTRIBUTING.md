# Contributing to Production Control System

Thank you for your interest in contributing to the s7 Inc. Production Control System!

## 🚀 Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/YOUR_USERNAME/Project_X_R0.git`
3. Create a feature branch: `git checkout -b feature/your-feature-name`

## 📋 Development Setup

See `STARTUP_GUIDE.md` for detailed setup instructions.

```bash
# Install dependencies
pip install -r ingress-api/requirements.txt
pip install -r dashboard/requirements.txt
pip install -r edge/requirements.txt

# Run tests
pytest
```

## 🔧 How to Contribute

### Reporting Bugs
- Use GitHub Issues
- Include system information (OS, Python version)
- Provide steps to reproduce
- Include error messages and logs

### Suggesting Features
- Open a GitHub Issue with the "enhancement" label
- Describe the use case
- Explain why it's valuable for manufacturing operations

### Code Contributions

#### Code Style
- Follow PEP 8 for Python code
- Use meaningful variable names
- Add docstrings for functions
- Keep functions focused and small

#### Commit Messages
```
feat: Add predictive maintenance dashboard
fix: Resolve OEE calculation error
docs: Update PLC integration guide
refactor: Optimize thermal heatmap rendering
```

#### Pull Request Process
1. Update documentation if needed
2. Add tests for new features
3. Ensure all tests pass
4. Update `README.md` if applicable
5. Request review from maintainers

## 🏭 Domain Knowledge

This is an industrial IoT system. Contributions should consider:
- **Real-time performance** - Manufacturing can't wait
- **Reliability** - Factory downtime is expensive
- **Security** - Production systems are targets
- **Usability** - Operators need simple interfaces

## 📝 Documentation

- API docs: Use docstrings
- User guides: Write in `docs/` folder
- Code comments: Explain "why", not "what"

## 🧪 Testing

```bash
# Run all tests
pytest

# Run specific test
pytest tests/test_oee_calculation.py

# With coverage
pytest --cov=app tests/
```

## 📄 License

By contributing, you agree that your contributions will be licensed under the MIT License.

## 🙏 Questions?

- Open a GitHub Discussion
- Email: [your-email@s7inc.com]

## 🎯 Priority Areas

We're especially looking for contributions in:
- PLC protocol implementations (Siemens, Allen-Bradley)
- Machine learning models for predictive maintenance
- Mobile dashboard optimization
- Localization (non-English languages)
- Performance optimizations

Thank you for helping make manufacturing smarter! 🏭
