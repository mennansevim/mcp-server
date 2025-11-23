# Linter Rules

## Priority: MEDIUM to HIGH (Compilation Errors: CRITICAL)
**Linter kuralları kod kalitesini ve tutarlılığını sağlar**

**⚠️ IMPORTANT:** Linter also catches compilation errors! If code won't compile, mark as CRITICAL.

---

## General Linter Rules

### Code Style
- ✅ **ALWAYS** follow language-specific style guides
- ✅ Use consistent indentation (spaces or tabs, but not both)
- ✅ Follow naming conventions
- ✅ Remove unused imports/variables
- ✅ Remove dead code

### Formatting
- ✅ Consistent spacing around operators
- ✅ Proper line length limits (usually 80-120 characters)
- ✅ Consistent quote style (single vs double quotes)
- ✅ Trailing whitespace removed

---

## Language-Specific Linter Rules

### Python
- ✅ Use `flake8`, `pylint`, or `ruff` for linting
- ✅ Follow PEP 8 style guide
- ✅ Maximum line length: 79 or 99 characters
- ✅ Use 4 spaces for indentation (never tabs)
- ✅ Import order: standard library → third-party → local
- ✅ Remove unused imports
- ✅ Use `snake_case` for functions and variables
- ✅ Use `PascalCase` for classes

**Common Issues:**
```python
# Bad: Unused import
import os
import sys  # Never used

# Good: Only import what you need
import os

# Bad: Line too long
result = some_very_long_function_name(parameter1, parameter2, parameter3, parameter4, parameter5)

# Good: Break into multiple lines
result = some_very_long_function_name(
    parameter1, parameter2, parameter3, parameter4, parameter5
)
```

### C# / .NET
- ✅ Use StyleCop or EditorConfig
- ✅ Follow Microsoft C# Coding Conventions
- ✅ Use `PascalCase` for public members
- ✅ Use `camelCase` for private fields and local variables
- ✅ Remove unused `using` statements
- ✅ Remove unused variables

**Common Issues:**
```csharp
// Bad: Unused using
using System.Collections.Generic;
using System.Linq;  // Never used

// Good: Only necessary usings
using System.Collections.Generic;

// Bad: Inconsistent naming
public string userName;  // Should be UserName
private string UserName;  // Should be userName

// Good: Consistent naming
public string UserName;
private string _userName;
```

### JavaScript / TypeScript
- ✅ Use ESLint with appropriate rules
- ✅ Follow Airbnb or Google style guide
- ✅ Use `camelCase` for variables and functions
- ✅ Use `PascalCase` for classes/components
- ✅ Use `UPPER_SNAKE_CASE` for constants
- ✅ Remove unused variables/imports
- ✅ Use `const` instead of `let` when possible
- ✅ No `var` declarations

**Common Issues:**
```javascript
// Bad: Unused variable
const unusedVar = 42;
const result = calculate();

// Good: Remove unused variables
const result = calculate();

// Bad: Using var
var name = "test";

// Good: Use const or let
const name = "test";
```

---

## Compilation Errors Caught by Linter

### Missing Keywords
❌ **CRITICAL:** Missing language keywords cause compilation errors
- Missing `await` in async calls (C#, JavaScript, Python, TypeScript)
- Missing `var`, `let`, `const` (JavaScript, TypeScript)
- Missing `$` prefix (PHP)
- Missing `let`, `let mut` (Rust)
- Missing `:=` or `var` (Go)
- Missing `def` (Python, Ruby)
- Missing `function` (PHP, JavaScript)
- Missing `fn` (Rust)
- Missing `func` (Go)

### Type Mismatches
❌ **CRITICAL:** Type mismatches cause compilation/runtime errors
- Assigning incompatible types (e.g., `string = 1`, `int = "test"`)
- Type mismatches in function parameters
- Type mismatches in return values
- **Check EVERY assignment for type compatibility**

### Invalid Property/Method Names
❌ **CRITICAL:** Typos in property/method names cause errors
- Typos in property names (e.g., `PropertyNameCaseInsensitive` → `_PropertyNameCaseInsensitive`)
- Typos in method names
- Invalid attribute access (Python AttributeError)
- Invalid property access (JavaScript/TypeScript)

### Syntax Errors
❌ **CRITICAL:** Syntax errors prevent compilation
- Missing semicolons (C#, Java, JavaScript)
- Unmatched braces, brackets, parentheses
- Incorrect indentation (Python)
- Missing `end` keyword (Ruby)
- Missing closing braces

## Common Linter Violations

### Unused Code
❌ **MEDIUM:** Remove unused imports, variables, functions
- Unused imports increase bundle size
- Unused variables indicate incomplete refactoring
- Dead code confuses maintainers

### Inconsistent Formatting
❌ **LOW:** Inconsistent spacing, indentation, or quotes
- Makes code harder to read
- Causes unnecessary diff noise
- Violates team standards

### Naming Conventions
❌ **MEDIUM:** Violating language naming conventions
- Reduces code readability
- Confuses other developers
- Violates language best practices

### Line Length
⚠️ **LOW:** Lines exceeding recommended length
- Harder to read on smaller screens
- Violates style guides
- Can indicate code complexity

---

## Linter Configuration

### Recommended Tools by Language

| Language | Linter | Formatter |
|----------|--------|-----------|
| Python | flake8, pylint, ruff | black, autopep8 |
| C# | StyleCop, Roslyn Analyzers | dotnet format |
| JavaScript/TypeScript | ESLint | Prettier |
| Java | Checkstyle, SpotBugs | Google Java Format |
| Go | golint, golangci-lint | gofmt |
| Rust | clippy | rustfmt |

---

## Checklist

**CRITICAL CHECKS (Compilation Errors):**
- [ ] All language keywords present? (`await`, `var`, `let`, `const`, `$`, `fn`, `func`, `def`, etc.)
- [ ] No type mismatches? (check every assignment)
- [ ] All property/method names correct? (no typos)
- [ ] All syntax correct? (semicolons, braces, brackets, indentation)
- [ ] Will this code compile/run?

**Code Quality Checks:**
- [ ] All linter errors fixed
- [ ] Code formatted consistently
- [ ] Unused imports/variables removed
- [ ] Naming conventions followed
- [ ] Line length within limits
- [ ] No trailing whitespace
- [ ] Consistent indentation
- [ ] Proper import ordering

---

## Severity Guidelines

| Issue | Severity |
|-------|----------|
| **COMPILATION ERRORS** (missing keywords, type mismatches, syntax errors) | **CRITICAL** |
| Missing `await` keyword | **CRITICAL** |
| Type mismatch (e.g., `string = 1`) | **CRITICAL** |
| Invalid property/method name (typo) | **CRITICAL** |
| Missing variable declaration (`var`, `let`, `const`, `$`, etc.) | **CRITICAL** |
| Missing semicolon (if required) | **CRITICAL** |
| Unmatched braces/brackets | **CRITICAL** |
| Incorrect indentation (Python) | **CRITICAL** |
| Unused imports causing build warnings | **MEDIUM** |
| Unused variables | **LOW** |
| Inconsistent formatting | **LOW** |
| Naming convention violations | **MEDIUM** |
| Line length violations | **LOW** |
| Dead code | **MEDIUM** |
| Missing type hints (TypeScript/Python) | **MEDIUM** |

---

## Integration

### Pre-commit Hooks
✅ **RECOMMENDED:** Run linter before commit
```bash
# Example pre-commit hook
#!/bin/sh
flake8 . || exit 1
```

### CI/CD Integration
✅ **REQUIRED:** Run linter in CI pipeline
- Fail build on linter errors (configurable)
- Report linter warnings in PR comments
- Enforce consistent code style across team

---

## Best Practices

1. **Configure linter rules** in project root (`.eslintrc`, `pyproject.toml`, etc.)
2. **Use formatters** to auto-fix style issues
3. **Fix linter errors** before submitting PR
4. **Document exceptions** if linter rule must be disabled
5. **Keep linter config** in version control

