# Contributing to SpectrumSnek 🐍📻

Thank you for your interest in contributing to SpectrumSnek 🐍📻! We welcome contributions from the community - join the radio snake pit!

## Development Setup

1. **Fork and Clone**
   ```bash
   git clone https://github.com/yourusername/spectrumsnek.git
   cd spectrumsnek
   ```

2. **Set up Development Environment**
   ```bash
   # Install system dependencies
   ./setup.sh --system-deps

   # Create virtual environment
   python3 -m venv venv
   source venv/bin/activate

   # Install Python dependencies
   pip install -r requirements.txt
   pip install -r requirements-dev.txt  # Development dependencies
   ```

3. **Run Tests**
   ```bash
   python -m pytest
   ```

## Code Style

We follow PEP 8 style guidelines. Please ensure your code:
- Uses 4 spaces for indentation
- Has proper docstrings
- Includes type hints where appropriate
- Passes flake8 linting

## Adding New Tools

1. **Create Module Structure**
   ```
   your_tool/
   ├── __init__.py       # Module metadata and entry point
   ├── tool.py          # Main implementation
   ├── web_tool.py      # Optional web interface
   └── README.md        # Tool documentation
   ```

2. **Implement Required Functions**
   ```python
   # __init__.py
   MODULE_INFO = {
       "name": "Your Tool Name",
       "description": "Brief description",
       "version": "1.0.0",
       "author": "Your Name",
       "features": ["feature1", "feature2"]
   }

   def get_module_info():
       return MODULE_INFO

   def run():
       # Main entry point
       pass
   ```

3. **Add to Main Loader**
   Update `main.py` to include your new module in the module loader.

4. **Update Documentation**
   - Add tool to README.md
   - Update feature list
   - Include usage examples

## Testing

- Write unit tests for new functionality
- Test with actual RTL-SDR hardware when possible
- Include demo/test modes for CI/CD
- Test web interfaces if applicable

## Pull Request Process

1. Create a feature branch: `git checkout -b feature/your-feature`
2. Make your changes and ensure tests pass
3. Update documentation as needed
4. Commit with clear, descriptive messages
5. Push to your fork and create a pull request
6. Address any review feedback

## Reporting Issues

When reporting bugs, please include:
- Operating system and version
- Python version
- RTL-SDR hardware details
- Steps to reproduce
- Expected vs actual behavior
- Log output (if applicable)

## License

By contributing, you agree that your contributions will be licensed under the MIT License.