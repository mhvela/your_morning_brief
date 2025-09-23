# Dependency Management Rules

## Critical Dual-File System

**⚠️ CRITICAL: This project uses TWO dependency files that MUST be kept in sync**

1. **`backend/requirements.txt`**: Runtime dependencies for local development (Conda environment)
2. **`backend/pyproject.toml`**: Development dependencies used by GitHub Actions CI/CD

**Dependency sync failures WILL break CI and block commits.**

## Adding Dependencies

### For Runtime Dependencies

```bash
# 1. Add to requirements.txt
echo "new-package==1.2.3" >> backend/requirements.txt

# 2. Add to pyproject.toml dependencies section
# Edit backend/pyproject.toml and add: "new-package==1.2.3",

# 3. Verify sync (MANDATORY)
make check-deps

# 4. Install locally
conda run -n ymb-py311 pip install new-package==1.2.3
```

### For Development Dependencies

```bash
# Add only to pyproject.toml [project.optional-dependencies.dev]
# Then reinstall dev dependencies
conda run -n ymb-py311 pip install -e ./backend[dev]
```

## Automatic Validation

### Pre-commit Protection

- **Pre-commit hooks** automatically run `make check-deps` before commits
- **Commits are BLOCKED** if dependencies are out of sync
- **Clear error messages** show exactly what to fix

### Example Error Output

```bash
❌ Dependencies in requirements.txt but missing from pyproject.toml:
   - new-package
   - another-package==2.1.0

❌ Dependencies in pyproject.toml but missing from requirements.txt:
   - dev-only-package
```

## Package Management Best Practices

### Always Use Conda Environment

```bash
# ✅ CORRECT: Use conda environment for all backend operations
conda run -n ymb-py311 pip install package-name
conda run -n ymb-py311 pip list
conda run -n ymb-py311 python -m pip freeze

# ❌ INCORRECT: Never use system pip
pip install package-name  # Will install in wrong environment
```

### Version Pinning Strategy

- **Runtime dependencies**: Pin exact versions for reproducibility
- **Development dependencies**: Allow compatible version ranges for flexibility
- **Security libraries**: Always pin to latest secure versions

### Required Security Libraries

```txt
bleach==6.1.0              # HTML sanitization
cryptography==41.0.7       # API key encryption
slowapi==0.1.9             # Rate limiting
chardet==5.2.0             # Safe encoding detection
pydantic>=2.0.0           # Input validation
```

## Dependency Validation Commands

### Daily Workflow Commands

```bash
# Check dependency sync (run before committing)
make check-deps

# Install/update dependencies
conda run -n ymb-py311 pip install -e ./backend[dev]

# Verify environment state
conda run -n ymb-py311 pip list | grep mypy
```

### Troubleshooting Dependency Issues

```bash
# If dependency sync fails
make check-deps  # See what's missing/mismatched

# If environment is corrupted
conda env remove -n ymb-py311
make setup  # Recreate environment

# If CI fails but local passes
conda run -n ymb-py311 pip install -e ./backend[dev]  # Sync with CI
```

## Environment Consistency

### Local vs CI Alignment

The project ensures identical dependencies between:

- Local Conda environment (`ymb-py311`)
- GitHub Actions CI environment
- Production Docker environment

### Environment Verification

```bash
# Verify conda environment setup
conda run -n ymb-py311 python --version  # Should show Python 3.11.x
conda run -n ymb-py311 which python      # Should point to conda env
conda run -n ymb-py311 pip list | grep mypy  # Verify dev tools

# Verify dependency files are in sync
make check-deps  # Should show ✅ All dependencies are in sync
```

## Common Dependency Patterns

### Adding New Features

When implementing new features that require dependencies:

1. Research the package and its security implications
2. Choose the minimal, most secure package for the task
3. Add to both `requirements.txt` and `pyproject.toml`
4. Run `make check-deps` to verify sync
5. Install locally: `conda run -n ymb-py311 pip install package-name`
6. Test the feature with the new dependency
7. Commit both files together

### Upgrading Dependencies

```bash
# 1. Update version in both files
# 2. Install updated version
conda run -n ymb-py311 pip install --upgrade package-name

# 3. Test thoroughly
make test

# 4. Verify sync
make check-deps

# 5. Commit both files
git add backend/requirements.txt backend/pyproject.toml
git commit -m "chore: upgrade package-name to vX.Y.Z"
```

## Security Considerations

### Dependency Security

- Run security scans on all new dependencies
- Monitor for known vulnerabilities
- Keep security-critical packages up to date
- Never install packages from untrusted sources

### Environment Isolation

- Always use the designated conda environment
- Never mix system packages with project packages
- Maintain clean environment for reproducible builds
