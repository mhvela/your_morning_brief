# Type Checking and Code Quality Rules

## Type Safety Requirements

**⚠️ MANDATORY: All Python code must pass mypy strict mode**

- Pre-commit hooks run `mypy app/` automatically before every commit
- Commits are BLOCKED if type checking fails
- GitHub Actions runs identical mypy checks in CI

## Environment Setup

### One-Time Setup

```bash
# Install dev dependencies to match CI exactly
conda run -n ymb-py311 pip install -e ./backend[dev]
```

### Type Checking Commands

```bash
# Local type checking
make typecheck                           # Run mypy on all Python code
conda run -n ymb-py311 mypy app/        # Backend-specific type checking

# Verify environment consistency
conda run -n ymb-py311 which python
conda run -n ymb-py311 which mypy
```

## Writing Type-Safe Code

### 1. Always Add Type Hints to Functions

```python
# ✅ CORRECT: Complete type annotations
def process_articles(articles: list[Article], source_id: int) -> dict[str, int]:
    result: dict[str, int] = {"processed": 0, "errors": 0}
    return result

# ❌ INCORRECT: Missing type annotations
def process_articles(articles, source_id):
    result = {"processed": 0, "errors": 0}
    return result
```

### 2. Handle Optional Values Explicitly

```python
# ✅ CORRECT: Proper None handling
existing_source.credibility_score = validated_source.credibility_score or 0.5
existing_source.is_active = (
    validated_source.is_active if validated_source.is_active is not None else True
)

# ❌ INCORRECT: Direct assignment of Optional to non-Optional
existing_source.credibility_score = validated_source.credibility_score  # May be None
```

### 3. Use Explicit Type Annotations for Complex Returns

```python
# ✅ CORRECT: Explicit type annotation
cleaned: str = bleach.clean(content, tags=[], strip=True)
parsed_date: datetime = date_parser.parse(date_str)

# ❌ INCORRECT: Relies on Any inference
cleaned = bleach.clean(content, tags=[], strip=True)  # Returns Any
```

## MyPy Configuration Understanding

The project uses `ignore_missing_imports = true` in `backend/pyproject.toml`:

```python
# ✅ WORKS WITHOUT type: ignore (due to ignore_missing_imports = true)
import feedparser
entries = feedparser.parse(url).entries

# ❌ UNNECESSARY: type: ignore comment for missing imports
import feedparser  # type: ignore
entries = feedparser.parse(url).entries  # type: ignore

# ✅ STILL NEEDED: type: ignore for actual type issues
result: str = some_function_returning_any()  # type: ignore[assignment]
```

## Common MyPy Errors & Solutions

| Error                                          | Solution                                       |
| ---------------------------------------------- | ---------------------------------------------- |
| `Function is missing a return type annotation` | Add `-> ReturnType` or `-> None`               |
| `Incompatible types in assignment`             | Check Optional types, use proper None handling |
| `Call to untyped function`                     | Add type hints to function definition          |
| `Need type annotation for variable`            | Add explicit type: `var: Type = value`         |
| `Returning Any from function`                  | Add explicit type annotation for clarity       |

## Troubleshooting Type Issues

### Environment Inconsistency

If mypy fails locally but passes in CI (or vice versa):

```bash
# 1. Verify environment consistency
conda run -n ymb-py311 which python
conda run -n ymb-py311 which mypy

# 2. Reinstall dependencies to match CI
conda run -n ymb-py311 pip install -e ./backend[dev]

# 3. Check for unnecessary type: ignore comments
grep -r "type: ignore" backend/app/
```

### Required Type Imports

```python
from typing import Any, Optional, Union, Dict, List
from sqlalchemy.orm import Session
from app.models.source import Source
```

## Code Quality Standards

### Backend Quality Requirements

- **Linting**: ruff and black formatting
- **Type Hints**: All public functions and endpoints
- **Testing**: pytest with deterministic tests
- **Documentation**: Clear function/class documentation for public APIs
- **Error Handling**: Proper exception handling with typed errors

### Frontend Quality Requirements

- **TypeScript**: Strict mode with zero type errors
- **ESLint**: Zero warnings policy
- **Testing**: Vitest with good coverage
- **Accessibility**: WCAG basics compliance

### CI Quality Gates

All code must pass these automated checks:

- **Backend**: ruff, black, mypy, pytest, security tests
- **Frontend**: eslint, tsc --noEmit, unit tests
- **Security**: SAST scanning, dependency vulnerability checks
- **Performance**: Security overhead validation (<50ms per request)
