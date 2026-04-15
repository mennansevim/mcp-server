# Compilation & Syntax Rules for Shell
## Priority: CRITICAL
**If ANY of these rules are violated, mark as CRITICAL and set block_merge=true**

## General Rules

### Missing Keywords
- ❌ **NEVER remove language keywords** without proper replacement
  - `if`, `then`, `else`, `fi`
  - `for`, `in`, `do`, `done`
  - `while`, `do`, `done`
  - `case`, `in`, `esac`

### Syntax Errors
- ❌ Missing semicolons or line breaks
- ❌ Unmatched quotes, parentheses, or brackets
- ❌ Invalid variable names
- ❌ Typos in keywords or identifiers

## Language-Specific Rules for Shell

### Variable Declaration
- ❌ **CRITICAL:** Missing `=` or incorrect variable assignment
  - ✅ CORRECT: `var="value"`
  - ❌ WRONG: `var "value"` (missing `=` - SYNTAX ERROR)

### Conditional Statements
- ❌ **CRITICAL:** Missing `if` or `then` keywords
  - ✅ CORRECT: `if [ -f file ]; then echo "File exists"; fi`
  - ❌ WRONG: `[ -f file ]; echo "File exists"` (missing `if` - SYNTAX ERROR)

### Loops
- ❌ **CRITICAL:** Missing `for` or `while` keywords
  - ✅ CORRECT: `for file in *.txt; do echo "$file"; done`
  - ❌ WRONG: `file in *.txt; do echo "$file"; done` (missing `for` - SYNTAX ERROR)

### Functions
- ❌ **CRITICAL:** Missing `()` or incorrect function definition
  - ✅ CORRECT: `my_function() { echo "Hello World"; }`
  - ❌ WRONG: `my_function { echo "Hello World"; }` (missing `()` - SYNTAX ERROR)

### Quoting
- ❌ **CRITICAL:** Missing or incorrect quotes
  - ✅ CORRECT: `echo "Hello World"`
  - ❌ WRONG: `echo Hello World` (missing quotes - may cause word splitting)

### Redirection
- ❌ **CRITICAL:** Missing or incorrect redirection operators
  - ✅ CORRECT: `echo "Hello World" > file.txt`
  - ❌ WRONG: `echo "Hello World" file.txt` (missing `>` - SYNTAX ERROR)

## Severity Guidelines
| Severity | Description |
| --- | --- |
| CRITICAL | Compilation errors, syntax errors, or incorrect syntax that prevents the script from running |
| HIGH | Potential security vulnerabilities, incorrect variable assignments, or missing error handling |
| MEDIUM | Code style issues, inconsistent indentation, or missing comments |
| LOW | Minor issues, such as unnecessary whitespace or redundant code |

## Checklist
- [ ] Check for missing or incorrect keywords
- [ ] Verify syntax and indentation
- [ ] Check for variable declaration and assignment issues
- [ ] Review conditional statements and loops
- [ ] Validate function definitions and calls
- [ ] Check for quoting and redirection issues
- [ ] Review code for security vulnerabilities and best practices