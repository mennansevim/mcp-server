# Compilation & Syntax Rules for Go
## Priority: CRITICAL
**If ANY of these rules are violated, mark as CRITICAL and set block_merge=true**

## General Rules

### Missing Keywords
- ❌ **NEVER remove language keywords** without proper replacement
  - `func`, `var`, `const`, `type`
  - `if`, `else`, `switch`, `case`
  - `for`, `range`, `break`, `continue`

### Syntax Errors
- ❌ Missing semicolons (not applicable in Go, but missing newline can cause issues)
- ❌ Unmatched braces, brackets, parentheses
- ❌ Invalid variable/method names
- ❌ Typos in keywords or identifiers

## Language-Specific Rules for Go

### Variable Declaration
1. **Variable Declaration**
   - ❌ **CRITICAL:** Missing `:=` or `var` keyword causes compilation errors
   - ✅ CORRECT: `var name string = "test"` or `name := "test"`
   - ❌ WRONG: `name = "test"` (variable not declared - COMPILATION ERROR)

2. **Type Mismatches**
   - ❌ **CRITICAL:** Type mismatches cause compilation errors
   - ❌ **CRITICAL:** Cannot assign incompatible types
   - ✅ CORRECT: `var count int = 5` or `var name string = "test"`
   - ❌ WRONG: `var count int = "test"` (string cannot be assigned to int - COMPILATION ERROR)

3. **Missing Keywords**
   - ❌ **CRITICAL:** Missing `return` statement in functions
   - ❌ **CRITICAL:** Missing `func` keyword
   - ✅ CORRECT: `func getName() string { return name }`
   - ❌ WRONG: `getName() string { return name }` (missing func - COMPILATION ERROR)

4. **Error Handling**
   - ❌ **CRITICAL:** Not checking errors from functions that return errors
   - ✅ CORRECT: `file, err := os.Open("file.txt"); if err != nil { ... }`
   - ❌ WRONG: `file, _ := os.Open("file.txt")` (ignoring potential error)

5. **Concurrency**
   - ❌ **CRITICAL:** Not waiting for goroutines to finish
   - ✅ CORRECT: Using `WaitGroup` or channels to synchronize goroutines
   - ❌ WRONG: Starting a goroutine without waiting for it to finish

### Severity Guidelines
| Severity | Description |
| --- | --- |
| CRITICAL | Compilation errors, syntax errors, or critical logic errors |
| HIGH | Potential runtime errors, incorrect usage of language features |
| MEDIUM | Code organization, naming conventions, best practices |
| LOW | Minor issues, formatting, code style |

### Checklist
- Use `:=` for short variable declarations
- Use `var` for explicit type declarations
- Check errors from functions that return errors
- Use `WaitGroup` or channels for concurrency
- Avoid using `panic` for error handling
- Follow Go naming conventions (e.g., `camelCase` for variable and function names)