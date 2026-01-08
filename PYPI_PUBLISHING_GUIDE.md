# Publishing to PyPI - Step-by-Step Guide

## Prerequisites Completed ✅

1. ✅ Created `src/__init__.py` - Makes src a proper Python package
2. ✅ Updated `pyproject.toml` - Added PyPI metadata and build configuration
3. ✅ Created `MANIFEST.in` - Specifies files to include in distribution
4. ✅ LICENSE file exists - MIT License
5. ✅ README.md exists - Professional documentation

## Before You Proceed

### 1. Update Your Email in pyproject.toml

Open `pyproject.toml` and replace `your.email@example.com` with your real email address:

```toml
authors = [
    {name = "Ole Johan Bondahl", email = "your.real.email@example.com"}
]
```

### 2. Install Build Tools

```bash
pip install --upgrade build twine
```

## Publishing Process

### Step 1: Build Your Package

```bash
# From the project root directory
python -m build
```

This creates two files in `dist/`:
- `wireviz_yaml_generator-0.1.0.tar.gz` (source distribution)
- `wireviz_yaml_generator-0.1.0-py3-none-any.whl` (wheel distribution)

### Step 2: Create PyPI Accounts

1. **Test PyPI** (for testing): https://test.pypi.org/account/register/
2. **PyPI** (production): https://pypi.org/account/register/

### Step 3: Create API Tokens

**Test PyPI:**
1. Go to https://test.pypi.org/manage/account/
2. Scroll to "API tokens"
3. Click "Add API token"
4. Name: `wireviz-yaml-generator-test`
5. Scope: "Entire account" (or specific project after first upload)
6. Copy the token (starts with `pypi-...`)

**PyPI:**
1. Go to https://pypi.org/manage/account/
2. Scroll to "API tokens"
3. Click "Add API token"
4. Name: `wireviz-yaml-generator`
5. Scope: "Entire account" (or specific project after first upload)
6. Copy the token (starts with `pypi-...`)

### Step 4: Upload to Test PyPI (Recommended First)

```bash
python -m twine upload --repository testpypi dist/*
```

When prompted:
- Username: `__token__`
- Password: (paste your Test PyPI token)

**Verify on Test PyPI:**
- Check: https://test.pypi.org/project/wireviz-yaml-generator/

**Test Installation from Test PyPI:**
```bash
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ wireviz-yaml-generator
```

### Step 5: Upload to PyPI (Production)

Once you've verified everything works on Test PyPI:

```bash
python -m twine upload dist/*
```

When prompted:
- Username: `__token__`
- Password: (paste your PyPI token)

**Verify on PyPI:**
- Check: https://pypi.org/project/wireviz-yaml-generator/

### Step 6: Test Installation

```bash
pip install wireviz-yaml-generator
```

## Using Your Published Package

Once published, anyone can install with:

```bash
pip install wireviz-yaml-generator
```

They can then use it in Python:

```python
from src import Connector, Cable, Connection
from src.data_access import SqliteDataSource
from src.workflow_manager import WorkflowManager

# Use the library...
```

Or run the CLI:

```bash
wireviz-generator
```

## Updating Your Package

When you make changes and want to publish a new version:

1. **Update version** in `pyproject.toml`:
   ```toml
   version = "0.1.1"  # or "0.2.0", etc.
   ```

2. **Update version** in `src/__init__.py`:
   ```python
   __version__ = "0.1.1"
   ```

3. **Rebuild**:
   ```bash
   # Clean old builds
   rm -rf dist/ build/ *.egg-info
   
   # Build new version
   python -m build
   ```

4. **Upload**:
   ```bash
   python -m twine upload dist/*
   ```

## Troubleshooting

### "File already exists"
- You've already uploaded this version
- Increment the version number and rebuild

### "Invalid distribution file"
- Delete `dist/` folder and rebuild
- Make sure `pyproject.toml` is valid

### Import errors after installation
- Check that `src/__init__.py` exists
- Verify package structure in the wheel file:
  ```bash
  unzip -l dist/*.whl
  ```

## Alternative: Using .pypirc for Credentials

Instead of entering credentials each time, create `~/.pypirc`:

```ini
[distutils]
index-servers =
    pypi
    testpypi

[pypi]
username = __token__
password = pypi-your-actual-token-here

[testpypi]
repository = https://test.pypi.org/legacy/
username = __token__
password = pypi-your-test-token-here
```

Then upload with just:
```bash
python -m twine upload --repository testpypi dist/*
python -m twine upload dist/*
```

## Package Name

Your package will be available as:
- **Package name on PyPI**: `wireviz-yaml-generator`
- **Import name in Python**: `from src import ...`
- **CLI command**: `wireviz-generator`

## Notes

- Version `0.1.0` indicates this is an initial release
- Use semantic versioning: MAJOR.MINOR.PATCH
- You cannot re-upload the same version (must increment)
- Test PyPI is completely separate from production PyPI

## Next Steps After Publishing

1. Add badge to README:
   ```markdown
   [![PyPI version](https://badge.fury.io/py/wireviz-yaml-generator.svg)](https://badge.fury.io/py/wireviz-yaml-generator)
   ```

2. Update README with installation instructions:
   ```markdown
   pip install wireviz-yaml-generator
   ```

3. Consider setting up GitHub Actions for automated publishing on releases

---

**Ready to publish? Start with Step 1!**
