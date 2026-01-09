# Contributing to Automated Trading Journal

First off, thank you for considering contributing to this project! 🎉

## How Can I Contribute?

### 🐛 Reporting Bugs

Before creating bug reports, please check existing issues. When creating a bug report, include:

- **Clear title and description**
- **Steps to reproduce**
- **Expected behavior**
- **Actual behavior**
- **Screenshots** (if applicable)
- **Environment details** (OS, Python version, browser)

### 💡 Suggesting Enhancements

Enhancement suggestions are tracked as GitHub issues. When creating an enhancement suggestion, include:

- **Clear title and description**
- **Use case** - why is this enhancement useful?
- **Expected behavior**
- **Mockups or examples** (if applicable)

### 🔧 Pull Requests

1. **Fork** the repository
2. **Create a branch** from `main`
   ```bash
   git checkout -b feature/amazing-feature
   ```
3. **Make your changes**
4. **Test thoroughly**
5. **Commit with clear messages**
   ```bash
   git commit -m "feat: add amazing feature"
   ```
6. **Push to your fork**
   ```bash
   git push origin feature/amazing-feature
   ```
7. **Open a Pull Request**

### 📝 Commit Message Guidelines

Use conventional commits format:

- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation changes
- `style:` - Code style changes (formatting, etc.)
- `refactor:` - Code refactoring
- `test:` - Adding tests
- `chore:` - Maintenance tasks

Examples:
```
feat: add multi-exchange support for Binance
fix: correct balance calculation for margin accounts
docs: update API endpoint documentation
```

## Code Style Guidelines

### Python (Backend)

- Follow **PEP 8**
- Use **type hints** where possible
- Add **docstrings** for functions and classes
- Keep functions **small and focused**

```python
def calculate_position_size(risk_amount: float, stop_loss_pct: float) -> float:
    """
    Calculate position size based on risk parameters.

    Args:
        risk_amount: Amount willing to risk in USDT
        stop_loss_pct: Stop loss percentage (e.g., 2.5 for 2.5%)

    Returns:
        Position size in USDT
    """
    if stop_loss_pct <= 0:
        return 0.0
    return (risk_amount / stop_loss_pct) * 100
```

### JavaScript (Frontend)

- Use **ES6+ syntax**
- Use **const** and **let** (avoid var)
- Add **JSDoc comments** for complex functions
- Keep functions **pure** where possible

```javascript
/**
 * Format currency value with proper decimals
 * @param {number} value - The numeric value
 * @param {number} decimals - Number of decimal places
 * @returns {string} Formatted currency string
 */
function formatCurrency(value, decimals = 2) {
    return `$${value.toFixed(decimals)}`;
}
```

### HTML/CSS

- Use **semantic HTML5** elements
- Follow **BEM naming convention** for CSS classes
- Keep styles **organized and commented**
- Use **CSS Grid/Flexbox** for layouts

## Testing

Before submitting a PR, ensure:

- [ ] All existing tests pass
- [ ] New features have tests
- [ ] Manual testing completed
- [ ] No console errors
- [ ] Works on Chrome, Firefox, Safari

### Manual Testing Checklist

```bash
# Backend tests
python -m pytest tests/

# Frontend checks
- Open DevTools (F12)
- Check Console for errors
- Test all interactive features
- Verify responsive design
```

## Development Setup

1. **Clone your fork**
```bash
git clone https://github.com/YOUR_USERNAME/automated-trading-journal.git
cd automated-trading-journal
```

2. **Set up virtual environment**
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Run in development mode**
```bash
python app.py
```

5. **Make changes and test**

## Project Structure

```
automated-trading-journal/
├── app.py                 # Main Flask application
├── templates/
│   └── single_page.html   # Frontend SPA
├── screenshots/           # User uploads
├── requirements.txt       # Python dependencies
└── trading_journal.db    # SQLite database
```

## Key Areas for Contribution

### 🔥 High Priority
- Multi-exchange support (Binance, OKX)
- Advanced charting with TradingView
- Mobile responsive improvements
- Unit tests and integration tests

### 💡 Feature Requests
- Strategy backtesting
- AI-powered trade analysis
- Export to Excel/CSV
- Dark/Light theme toggle

### 🐛 Known Issues
- Check [Issues](https://github.com/Imbalance983/automated-trading-journal/issues) page

## Questions?

Feel free to:
- Open an issue with the `question` label
- Reach out via GitHub discussions
- Email: [your-email@example.com]

## Code of Conduct

- Be respectful and inclusive
- Provide constructive feedback
- Focus on what is best for the community
- Show empathy towards other contributors

## Recognition

Contributors will be:
- Listed in README.md
- Mentioned in release notes
- Given credit in commits

Thank you for contributing! 🙌
