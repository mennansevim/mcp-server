# Compilation & Syntax Rules for Python
## Priority: CRITICAL
**If ANY of these rules are violated, mark as CRITICAL and set block_merge=true**

## General Rules

### Missing Keywords
- ❌ **NEVER remove language keywords** without proper replacement
  - `async`, `await`, `def`, `class`

### Syntax Errors
- ❌ Unmatched braces, brackets, parentheses
- ❌ Invalid variable/method names
- ❌ Typos in keywords or identifiers

## Language-Specific Rules for Python

### Indentation
- ❌ **CRITICAL:** Incorrect indentation breaks code blocks (SyntaxError)
- ❌ **CRITICAL:** Mixing tabs and spaces causes IndentationError
- ✅ CORRECT: Use 4 spaces consistently
- ❌ WRONG: Mixing tabs and spaces, or inconsistent indentation

### Variable Declaration & Type Mismatches
- ❌ **CRITICAL:** Type mismatches cause runtime errors (TypeError)
- ❌ **CRITICAL:** Cannot perform operations on incompatible types
- ✅ CORRECT: `count: int = 5` or `name: str = "test"`
- ❌ WRONG: `count: int = "test"` (type mismatch - RUNTIME ERROR)
- ❌ WRONG: `result = "5" + 3` (string + int - TypeError)

### Missing Keywords
- ❌ **CRITICAL:** Missing `await` in async functions causes coroutine not awaited
- ✅ CORRECT: `await async_function()` or `result = await api.call()`
- ❌ WRONG: `async_function()` (returns coroutine, not result - RUNTIME ERROR)
- ❌ **CRITICAL:** Missing `async` keyword before `def` when using `await`

### Import Errors
- ❌ **CRITICAL:** Missing imports cause NameError
- ❌ **CRITICAL:** Typos in import names cause ImportError
- ✅ CORRECT: `from module import function` or `import module`
- ❌ WRONG: `from modul import function` (typo - ImportError)

### Attribute Errors
- ❌ **CRITICAL:** Accessing non-existent attributes causes AttributeError
- ❌ **CRITICAL:** Typos in method/attribute names
- ✅ CORRECT: `obj.method()` or `obj.attribute`
- ❌ WRONG: `obj.methd()` (typo - AttributeError) or `obj._attribute` (if not private)

### Severity Guidelines
| Severity | Description |
| --- | --- |
| CRITICAL | Compilation errors, syntax errors, or runtime errors that prevent the code from running |
| HIGH | Potential runtime errors, type mismatches, or attribute errors that may cause issues |
| MEDIUM | Code organization, naming conventions, or best practices that can improve readability and maintainability |
| LOW | Minor issues, such as formatting or whitespace inconsistencies |

### Checklist
- Use consistent indentation (4 spaces)
- Check for missing keywords (async, await, def, class)
- Verify variable declarations and type annotations
- Ensure proper import statements
- Avoid attribute errors by checking attribute names
- Use try-except blocks for error handling
- Follow PEP 8 guidelines for code style and conventions