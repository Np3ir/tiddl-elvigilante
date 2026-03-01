<<<<<<< HEAD
# 🍴 About This Fork

## 📌 Overview

**tiddl** is an independent fork of the excellent [oskvr37/tiddl](https://github.com/oskvr37/tiddl) project with significant improvements focused on **Python 3.10+ compatibility, production-grade quality, and comprehensive documentation**.

---

## 🎯 Why This Fork Exists

### Original Project Status
The original `tiddl` project by @oskvr37 is excellent, but had specific limitations:

1. **Python 3.13+ Only**
   - Requires Python 3.13 or higher
   - Excludes users on Python 3.10, 3.11, 3.12

2. **Pydantic v2 Dependency**
   - Uses `pydantic>=2.12.4`
   - Conflicts with certain Python 3.14 scenarios
   - More complex setup

3. **Limited Documentation**
   - Basic README
   - Minimal examples
   - No contribution guidelines

4. **Monolithic Structure**
   - 47 files in single `tiddl/` directory
   - Harder to navigate and extend
   - Not optimized for team collaboration

### Our Solution
This fork addresses these limitations while maintaining compatibility with the original.

---

## ✨ What We Improved

### 1. **Python 3.10+ Support** (CRITICAL)
```python
# Original (requires 3.13+):
requires-python = ">=3.13"

# Our Fork (supports 3.10+):
requires-python = ">=3.10"
```

Now works on:
- ✅ Python 3.10
- ✅ Python 3.11
- ✅ Python 3.12
- ✅ Python 3.13
- ✅ Python 3.14+

### 2. **Pydantic v1 Compatibility**
```python
# Original:
pydantic >= 2.12.4  # Uses .model_validate()

# Our Fork:
pydantic < 2.0      # Uses .parse_obj()
```

Benefits:
- ✅ Tested with Python 3.14
- ✅ Simpler setup
- ✅ No forward reference issues
- ✅ Stable and reliable

### 3. **Professional Architecture**
=======
# About This Fork

## 📖 Context

This project is an **independent fork** of the excellent [oskvr37/tiddl](https://github.com/oskvr37/tiddl) project.

**Original Repository**: https://github.com/oskvr37/tiddl  
**Original Author**: @oskvr37 and contributors  
**Original License**: MIT  

---

## 🎯 Why This Fork?

### Problem: Python 3.10 Incompatibility

The original `tiddl` project, while excellent, had several limitations:

1. **No Python 3.10 Support** 
   - Used `tomllib` (Python 3.11+ only)
   - Would crash immediately on Python 3.10

2. **Older Architecture**
   - Flat file structure (39 files in root)
   - Mixed concerns (CLI, API, Auth in same directory)
   - Not optimized for scaling

4. **Outdated Documentation**
   - Limited setup instructions
   - No contribution guidelines
   - Missing modern Python packaging

---

## ✅ What We Improved

### 1. **Python 3.10+ Compatibility** (CRITICAL)
```python
# Original (❌ BREAKS on Python 3.10):
from tomllib import loads as parse_toml

# Our Fix (✅ WORKS on 3.10+):
try:
    from tomllib import loads as parse_toml      # Python 3.11+
except ImportError:
    from tomli import loads as parse_toml         # Python 3.10
```

**Result**: Works on Python 3.10, 3.11, 3.12, 3.13, 3.14+

### 2. **Professional Architecture**
>>>>>>> 51f206d9cee155d16ba05c48767a0da1772ff3c1
```
Original (39 flat files):
├── api.py
├── auth.py
├── downloader.py
└── ... (all mixed)

<<<<<<< HEAD
Our Fork (52 organized files):
├── cli/           # User interface layer
├── core/          # Business logic
│   ├── api/       # TIDAL API integration
│   ├── auth/      # Authentication
│   ├── metadata/  # Metadata processing
│   └── utils/     # Utilities
├── tests/         # Test suite
└── docs/          # Documentation
```

Benefits:
=======
Our Structure (52 organized files):
├── cli/          # User interface layer
├── core/         # Business logic
│   ├── api/      # TIDAL API
│   ├── auth/     # Authentication
│   ├── metadata/ # Metadata processing
│   └── utils/    # Utilities
├── tests/        # Test suite
└── docs/         # Documentation
```

**Benefits**:
>>>>>>> 51f206d9cee155d16ba05c48767a0da1772ff3c1
- Clear separation of concerns
- Easier to extend and maintain
- Better for team collaboration
- Scales to larger projects

<<<<<<< HEAD
### 4. **Production-Grade Documentation**
```
README.md         - Overview and quick start
USAGE.md          - Detailed command examples
CONFIG.md         - Configuration reference
FORK.md           - This file (fork information)
CONTRIBUTING.md   - How to contribute
CHANGELOG.md      - Version history
DESIGN_CONSTRAINTS.md - Design principles
```

### 5. **Modern Python Standards**
- ✅ PEP 517/518 packaging (`pyproject.toml`)
- ✅ Type hints throughout
- ✅ `.editorconfig` for consistency
- ✅ Comprehensive error handling
- ✅ Professional `.gitignore`

### 6. **Complete Test Suite**
- ✅ Unit tests included
- ✅ Regression tests
- ✅ CI/CD ready

---

## 📊 Feature Comparison

| Feature | Original | This Fork |
|---------|----------|-----------|
| **Python 3.10** | ❌ NO | ✅ YES |
| **Python 3.11** | ❌ NO | ✅ YES |
| **Python 3.12** | ❌ NO | ✅ YES |
| **Python 3.13+** | ✅ YES | ✅ YES |
| **Pydantic v2** | ✅ YES | ❌ NO |
| **Pydantic v1** | ❌ NO | ✅ YES |
| **TIDAL Downloads** | ✅ YES | ✅ YES |
| **Metadata** | ✅ YES | ✅ YES |
| **Unicode Support** | ✅ YES | ✅ YES |
| **Architecture** | Flat | Modular |
| **Documentation** | Basic | Comprehensive |
| **Type Hints** | Partial | Complete |
| **Test Suite** | Minimal | Included |
| **Contributing Guide** | ❌ NO | ✅ YES |

---

## 🔄 How This Fork Works

### Installation Independence
```bash
# Install directly from this fork
pip install git+https://github.com/yourusername/tiddl.git

# No need to install original
# This fork is completely standalone
```

### Separate Maintenance
- ✅ Separate repository
- ✅ Independent issue tracking
- ✅ Own release cycle
- ✅ Can coexist with original if needed

### Contributing Back
If you find improvements that benefit the original:
1. Notify @oskvr37
2. Open PR on original repository
3. We'll also maintain in our fork

---

## 🤝 Relationship with Original

### Acknowledgments
We deeply respect the original work by @oskvr37. This fork:
- ✅ Maintains the core functionality
- ✅ Preserves the spirit of the original
- ✅ Credits the original author
- ✅ Links back to original repository
- ✅ Licensed under the same MIT license

### Differences
- More conservative approach to dependencies
- Focus on broader Python version support
- Enhanced documentation and examples
- Modular architecture for maintainability

### Compatibility
- ✅ Same core commands: `tiddl download url https://...`
- ✅ Same TIDAL features
- ✅ Compatible download formats
- ✅ Can migrate between versions

---

## 📈 When to Use Each

### Use Original (oskvr37/tiddl)
- You have Python 3.13+
- You want latest Pydantic v2
- You prefer minimal dependencies
- You want upstream development

### Use This Fork (tiddl)
- You need Python 3.10-3.12 support
- You have Python 3.14 with dependency issues
- You want comprehensive documentation
- You need modular codebase
- You want stable, tested version
- You plan to contribute improvements

---

## 🚀 Getting Started

### Installation
```bash
pip install git+https://github.com/yourusername/tiddl.git
```

### First Steps
```bash
# Authenticate
tiddl auth

# Download something
tiddl download url https://tidal.com/album/497662013
```

### Configuration
```bash
# Edit your config
nano ~/.tiddl/config.toml
```

See [CONFIG.md](CONFIG.md) for all options.

---

## 🤝 Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for:
- How to report issues
- How to submit pull requests
- Development setup
- Code style guidelines

---

## 📜 License

MIT License - Same as original project

See [LICENSE](LICENSE) file for details.

---

## 🔗 Links

- **This Fork**: https://github.com/yourusername/tiddl
- **Original Project**: https://github.com/oskvr37/tiddl
- **Original Author**: @oskvr37
- **TIDAL**: https://tidal.com

---

## 📝 Version History

- **v1.0.0** (March 2026) - Initial production release
  - Python 3.10+ support
  - Pydantic v1 compatibility
  - Production-grade documentation
  - Modular architecture

See [CHANGELOG.md](CHANGELOG.md) for detailed history.

---

**Thank you to @oskvr37 for the original excellent project!** 🙏

This fork stands on the shoulders of giants.
=======
### 3. **Modern Python Standards**
- ✅ PEP 563 annotations (`from __future__ import annotations`)
- ✅ `pyproject.toml` for modern packaging
- ✅ Complete type hints
- ✅ `.editorconfig` for consistency
- ✅ Professional `.gitignore`

### 4. **Production-Grade Quality**
- ✅ Complete documentation (README, CONFIG, USAGE, CONTRIBUTING)
- ✅ Contribution guidelines
- ✅ CHANGELOG with version history
- ✅ Test suite included
- ✅ Comprehensive error handling

### 5. **Installation Independence**
- ✅ No need to install original `tiddl`
- ✅ Standalone `pip install -r requirements.txt`
- ✅ Works completely independently
- ✅ Can coexist with original if needed

---

## 📊 Comparison Table

| Feature | Original | This Fork |
|---------|----------|-----------|
| **Python 3.10** | ❌ No | ✅ Yes |
| **Python 3.11+** | ✅ Yes | ✅ Yes |
| **Architecture** | Flat | Layered |
| **pyproject.toml** | ❌ No | ✅ Yes |
| **Type Hints** | 🟡 Partial | ✅ Complete |
| **Documentation** | 🟡 Basic | ✅ Comprehensive |
| **Contributing Guide** | ❌ No | ✅ Yes |
| **Test Suite** | ❌ No | ✅ Yes |
| **Independence** | Standalone | Standalone |

---

## 🔄 How to Use This Fork

### Option A: Fresh Install (Recommended)
```bash
# Clone THIS repository
git clone https://github.com/yourusername/tiddl.git
cd tiddl

# Install (completely independent)
pip install -r requirements.txt

# Run
python -m cli auth
```

### Option B: Migrate from Original
If you're using the original `tiddl`:

```bash
# You can keep BOTH installed - they don't conflict!
# Original: uses "from tiddl.xxx" 
# This fork: also uses "from tiddl.xxx" but different implementation

# To switch:
pip uninstall tiddl  # If installed via pip
pip install -r requirements.txt
```

### Option C: Have Both
The namespaces are the same, so you'd need to manage them:

```bash
# Original in one virtual env
python3.11 -m venv env-original
source env-original/bin/activate
pip install tiddl

# This fork in another
python3.10 -m venv env-fork
source env-fork/bin/activate
pip install -r requirements.txt
```

---

## 🙏 Acknowledgments

**Big thanks to**:
- [@oskvr37](https://github.com/oskvr37) - Original `tiddl` creator and maintainer
- All original contributors
- The TIDAL downloader community

This fork stands on the shoulders of the excellent work already done.

---

## 📋 Staying Updated

### Original Project Updates
If the original project gets updates you want, you can:

1. **Check what changed**: Compare commits
2. **Port features**: Adapt relevant changes to our architecture
3. **Keep independent**: You control which updates you adopt

### This Fork Updates
We'll maintain:
- Python compatibility (3.10+)
- Security updates
- Performance improvements
- Documentation enhancements

---

## 🤝 Contributing to This Fork

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

We welcome:
- Bug reports
- Feature requests
- Documentation improvements
- Code contributions
- Python compatibility fixes

---

## ⚖️ License

This fork maintains the **MIT License** from the original, providing:
- ✅ Personal use
- ✅ Modification
- ✅ Distribution
- ✅ Commercial use

See [LICENSE](LICENSE) for full terms.

---

## 🔗 Related Links

- **Original Project**: https://github.com/oskvr37/tiddl
- **TIDAL Website**: https://tidal.com
- **Python Downloads**: https://python.org
- **MIT License**: https://opensource.org/licenses/MIT

---

## ❓ FAQs

**Q: Can I use this alongside the original?**  
A: They use the same namespace (`tiddl`), so you'd need separate virtual environments.

**Q: Will you keep this in sync with the original?**  
A: We maintain compatibility, but this fork has its own direction (modern Python, architecture).

**Q: Is this officially affiliated with the original?**  
A: No, this is an independent fork. We acknowledge and credit the original.

**Q: Can I contribute?**  
A: Yes! See [CONTRIBUTING.md](CONTRIBUTING.md).

**Q: What if the original adds Python 3.10 support?**  
A: Then both projects would be compatible with 3.10. Choose whichever fits your needs better.

---

## 📞 Getting Help

1. **Issues**: Check existing GitHub issues
2. **Documentation**: Read [README.md](README.md), [CONFIG.md](CONFIG.md), [USAGE.md](USAGE.md)
3. **Code**: Look at the well-organized structure in `cli/` and `core/`
4. **Examples**: Check command examples in [USAGE.md](USAGE.md)

---

## 🎓 Learning Resources

This fork is a good example of:
- Python 3.10+ compatibility patterns
- Modern Python packaging (PEP 563, pyproject.toml)
- Architectural refactoring
- Open source attribution practices

---

**Version**: 1.0.0  
**Last Updated**: March 1, 2026  
**Status**: Stable and Production-Ready

---

Thank you for using this fork! 🚀
>>>>>>> 51f206d9cee155d16ba05c48767a0da1772ff3c1
