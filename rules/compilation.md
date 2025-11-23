# Compilation & Syntax Rules

## Priority: CRITICAL
**If ANY of these rules are violated, mark as CRITICAL and set block_merge=true**

---

## General Rules

### Missing Keywords
- ❌ **NEVER remove language keywords** without proper replacement
  - `static`, `const`, `var`, `let`, `async`, `await`
  - `public`, `private`, `protected`, `internal`
  - `abstract`, `virtual`, `override`

### Syntax Errors
- ❌ Missing semicolons (C#, Java, JavaScript)
- ❌ Unmatched braces, brackets, parentheses
- ❌ Invalid variable/method names
- ❌ Typos in keywords or identifiers

---

## Language-Specific Rules

### C# / .NET
1. **Method Modifiers**
   - ❌ Removing `static` from static methods breaks all callers
   - ❌ Removing `async` from async methods requires signature change
   - ❌ Changing access modifiers (public → private) breaks API

2. **Async/Await Keywords**
   - ❌ **CRITICAL:** Removing `await` from async method calls causes compilation errors
   - ❌ **CRITICAL:** `await` keyword MUST be present when calling async methods
   - ✅ CORRECT: `await writer.WriteLineAsync(...);`
   - ❌ WRONG: `writer.WriteLineAsync(...);` (missing await - COMPILATION ERROR)

3. **Variable Declarations**
   - ❌ C# **requires** type or `var` keyword for local variables
   - ✅ CORRECT: `var name = "test";` or `string name = "test";`
   - ❌ WRONG: `name = "test";` (missing declaration)

4. **Type System & Type Mismatches**
   - ❌ **CRITICAL:** Type mismatches cause compilation errors
   - ❌ **CRITICAL:** Cannot assign incompatible types (e.g., int to string)
   - ✅ CORRECT: `string? line = null;` or `string? line = "test";`
   - ❌ WRONG: `string? line = 1;` (int cannot be assigned to string - COMPILATION ERROR)
   - ❌ Removing generic type parameters: `List<T>` → `List`
   - ❌ Changing nullable types: `string?` → `string`

5. **Property Names & API Surface**
   - ❌ **CRITICAL:** Changing property names breaks compilation if property doesn't exist
   - ❌ **CRITICAL:** Adding underscore prefix to property names is WRONG unless it's a private field
   - ✅ CORRECT: `PropertyNameCaseInsensitive = true` (JsonSerializerOptions property)
   - ❌ WRONG: `_PropertyNameCaseInsensitive = true` (property doesn't exist - COMPILATION ERROR)
   - ❌ Typos in property names: `PropertyNameCaseInsensitive` → `_PropertyNameCaseInsensitive`

6. **Required Elements**
   - ❌ Removing `using` statements that are needed
   - ❌ Removing base class or interface implementations
   - ❌ Breaking inheritance chain

### JavaScript / TypeScript
1. **Variable Declaration**
   - ❌ **CRITICAL:** Removing `let`, `const`, or `var` keyword causes compilation errors
   - ✅ CORRECT: `let x = 5;` or `const y = 10;`
   - ❌ WRONG: `x = 5;` (creates global variable - may cause runtime errors)

2. **Async/Await Keywords**
   - ❌ **CRITICAL:** Missing `await` in async functions causes unhandled Promise
   - ✅ CORRECT: `await fetch(url);` or `const result = await api.call();`
   - ❌ WRONG: `fetch(url);` (returns Promise, not result - COMPILATION/RUNTIME ERROR)
   - ❌ **CRITICAL:** Removing `await` from `await Promise.all([...])` or `await asyncFunction()`

3. **Type Annotations (TypeScript)**
   - ❌ **CRITICAL:** Type mismatches in TypeScript cause compilation errors
   - ❌ **CRITICAL:** Cannot assign incompatible types (e.g., `string` to `number`)
   - ✅ CORRECT: `const count: number = 5;` or `const name: string = "test";`
   - ❌ WRONG: `const count: number = "test";` (string cannot be assigned to number - COMPILATION ERROR)
   - ❌ Removing type annotations in strict mode
   - ❌ Changing interface/type definitions used by other files

4. **Property/Method Names**
   - ❌ **CRITICAL:** Typos in property names cause runtime errors
   - ❌ **CRITICAL:** Invalid property access (e.g., `obj.proprty` instead of `obj.property`)
   - ✅ CORRECT: `obj.property` or `obj.method()`
   - ❌ WRONG: `obj._property` (if not a private field) or `obj.proprty` (typo)

5. **Import/Export Statements**
   - ❌ **CRITICAL:** Missing or incorrect import statements
   - ❌ **CRITICAL:** Typos in import paths or module names
   - ✅ CORRECT: `import { func } from './module';`
   - ❌ WRONG: `import { func } from './modul';` (typo - COMPILATION ERROR)

### Python
1. **Indentation**
   - ❌ **CRITICAL:** Incorrect indentation breaks code blocks (SyntaxError)
   - ❌ **CRITICAL:** Mixing tabs and spaces causes IndentationError
   - ✅ CORRECT: Use 4 spaces consistently
   - ❌ WRONG: Mixing tabs and spaces, or inconsistent indentation

2. **Variable Declaration & Type Mismatches**
   - ❌ **CRITICAL:** Type mismatches cause runtime errors (TypeError)
   - ❌ **CRITICAL:** Cannot perform operations on incompatible types
   - ✅ CORRECT: `count: int = 5` or `name: str = "test"`
   - ❌ WRONG: `count: int = "test"` (type mismatch - RUNTIME ERROR)
   - ❌ WRONG: `result = "5" + 3` (string + int - TypeError)

3. **Missing Keywords**
   - ❌ **CRITICAL:** Missing `await` in async functions causes coroutine not awaited
   - ✅ CORRECT: `await async_function()` or `result = await api.call()`
   - ❌ WRONG: `async_function()` (returns coroutine, not result - RUNTIME ERROR)
   - ❌ **CRITICAL:** Missing `async` keyword before `def` when using `await`

4. **Import Errors**
   - ❌ **CRITICAL:** Missing imports cause NameError
   - ❌ **CRITICAL:** Typos in import names cause ImportError
   - ✅ CORRECT: `from module import function` or `import module`
   - ❌ WRONG: `from modul import function` (typo - ImportError)

5. **Attribute Errors**
   - ❌ **CRITICAL:** Accessing non-existent attributes causes AttributeError
   - ❌ **CRITICAL:** Typos in method/attribute names
   - ✅ CORRECT: `obj.method()` or `obj.attribute`
   - ❌ WRONG: `obj.methd()` (typo - AttributeError) or `obj._attribute` (if not private)

### Java
1. **Access Modifiers**
   - ❌ **CRITICAL:** Removing `public`, `private`, `protected` breaks compilation
   - ❌ **CRITICAL:** Removing `static` from static members causes compilation errors
   - ✅ CORRECT: `public static void main(String[] args)`
   - ❌ WRONG: `static void main(String[] args)` (missing public - COMPILATION ERROR)

2. **Type System & Type Mismatches**
   - ❌ **CRITICAL:** Type mismatches cause compilation errors
   - ❌ **CRITICAL:** Cannot assign incompatible types (e.g., `String str = 1;`)
   - ✅ CORRECT: `String str = "test";` or `int count = 5;`
   - ❌ WRONG: `String str = 1;` (int cannot be assigned to String - COMPILATION ERROR)
   - ❌ Generic type erasure issues
   - ❌ Incorrect type casting

3. **Method Signatures**
   - ❌ **CRITICAL:** Changing method signatures breaks compilation
   - ❌ **CRITICAL:** Missing return type or parameter types
   - ✅ CORRECT: `public String getName() { return name; }`
   - ❌ WRONG: `public getName() { return name; }` (missing return type - COMPILATION ERROR)

4. **Missing Keywords**
   - ❌ **CRITICAL:** Missing `return` statement in non-void methods
   - ❌ **CRITICAL:** Missing `throws` clause for checked exceptions
   - ✅ CORRECT: `public String getName() throws IOException { return name; }`
   - ❌ WRONG: `public String getName() { }` (missing return - COMPILATION ERROR)

### Go
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

### Rust
1. **Variable Declaration**
   - ❌ **CRITICAL:** Missing `let`, `let mut`, or type annotation
   - ✅ CORRECT: `let name: String = "test".to_string();` or `let mut count = 5;`
   - ❌ WRONG: `name = "test"` (variable not declared - COMPILATION ERROR)

2. **Type Mismatches**
   - ❌ **CRITICAL:** Type mismatches cause compilation errors (very strict)
   - ❌ **CRITICAL:** Cannot assign incompatible types
   - ✅ CORRECT: `let count: i32 = 5;` or `let name: String = "test".to_string();`
   - ❌ WRONG: `let count: i32 = "test";` (string cannot be assigned to i32 - COMPILATION ERROR)

3. **Missing Keywords**
   - ❌ **CRITICAL:** Missing `fn` keyword for functions
   - ❌ **CRITICAL:** Missing `return` or final expression
   - ✅ CORRECT: `fn get_name() -> String { name }` or `fn get_count() -> i32 { return 5; }`
   - ❌ WRONG: `get_name() -> String { name }` (missing fn - COMPILATION ERROR)

### PHP
1. **Variable Declaration**
   - ❌ **CRITICAL:** Missing `$` prefix causes syntax errors
   - ✅ CORRECT: `$name = "test";` or `$count = 5;`
   - ❌ WRONG: `name = "test"` (missing $ - SYNTAX ERROR)

2. **Type Mismatches**
   - ❌ **CRITICAL:** Type mismatches cause runtime errors
   - ❌ **CRITICAL:** Cannot perform operations on incompatible types
   - ✅ CORRECT: `$count = 5;` or `$name = "test";`
   - ❌ WRONG: `$count = "test";` (type mismatch - may cause runtime errors)

3. **Missing Keywords**
   - ❌ **CRITICAL:** Missing `function` keyword
   - ❌ **CRITICAL:** Missing `return` statement
   - ✅ CORRECT: `function getName() { return $name; }`
   - ❌ WRONG: `getName() { return $name; }` (missing function - SYNTAX ERROR)

### Ruby
1. **Variable Declaration**
   - ❌ **CRITICAL:** Wrong variable prefix causes scope issues
   - ✅ CORRECT: `name = "test"` (local) or `@name = "test"` (instance) or `@@name = "test"` (class)
   - ❌ WRONG: Using wrong prefix (e.g., `@name` when should be `name`)

2. **Type Mismatches**
   - ❌ **CRITICAL:** Type mismatches cause runtime errors (NoMethodError, TypeError)
   - ❌ **CRITICAL:** Cannot call methods on incompatible types
   - ✅ CORRECT: `count = 5` or `name = "test"`
   - ❌ WRONG: Calling string methods on integers or vice versa

3. **Missing Keywords**
   - ❌ **CRITICAL:** Missing `def` keyword for methods
   - ❌ **CRITICAL:** Missing `end` keyword
   - ✅ CORRECT: `def get_name; name; end`
   - ❌ WRONG: `get_name; name; end` (missing def - SYNTAX ERROR)

---

## Examples

### ❌ CRITICAL ERROR: Removed `static` keyword
```diff
- static PullRequestReviewEvent DetermineReviewEvent(ReviewResponse review)
+ PullRequestReviewEvent DetermineReviewEvent(ReviewResponse review)
```
**Impact:** Non-static method cannot be called without object instance. BUILD FAILS.

### ❌ CRITICAL ERROR: Removed `await` keyword (C#)
```diff
- await writer.WriteLineAsync(JsonSerializer.Serialize(error));
+ writer.WriteLineAsync(JsonSerializer.Serialize(error));
```
**Impact:** Missing `await` in async method causes compilation error. COMPILATION FAILS.

### ❌ CRITICAL ERROR: Type mismatch (C#)
```diff
- string? line;
+ string? line = 1;
```
**Impact:** Cannot assign `int` to `string?`. COMPILATION ERROR.

### ❌ CRITICAL ERROR: Invalid property name (C#)
```diff
- PropertyNameCaseInsensitive = true,
+ _PropertyNameCaseInsensitive = true,
```
**Impact:** `_PropertyNameCaseInsensitive` is not a valid property of `JsonSerializerOptions`. COMPILATION ERROR.

### ❌ CRITICAL ERROR: Removed `var` keyword (C#)
```diff
- var behavior = Environment.GetEnvironmentVariable("REVIEW_BEHAVIOR") ?? "comment";
+ behavior = Environment.GetEnvironmentVariable("REVIEW_BEHAVIOR") ?? "comment";
```
**Impact:** C# requires variable declaration. COMPILATION ERROR.

### ✅ SAFE: Renamed variable
```diff
- var userName = "test";
+ var username = "test";
```

---

## Severity Guidelines

| Violation | Severity | Block Merge |
|-----------|----------|-------------|
| **ALL LANGUAGES:** Missing `await` keyword from async call | **CRITICAL** | ✅ YES |
| **ALL LANGUAGES:** Type mismatch (e.g., `string? = 1`, `int = "test"`, `const count: number = "test"`) | **CRITICAL** | ✅ YES |
| **ALL LANGUAGES:** Invalid property/method name (typo) | **CRITICAL** | ✅ YES |
| **ALL LANGUAGES:** Missing variable declaration (`var`, `let`, `const`, `$`, `:=`, `let`, etc.) | **CRITICAL** | ✅ YES |
| **ALL LANGUAGES:** Missing function keyword (`function`, `def`, `fn`, `func`) | **CRITICAL** | ✅ YES |
| **ALL LANGUAGES:** Syntax error (missing semicolon, unmatched braces, wrong indentation) | **CRITICAL** | ✅ YES |
| **C#:** Removed `await`, `var`, `static`, `async` | **CRITICAL** | ✅ YES |
| **JavaScript/TypeScript:** Removed `await`, `let`, `const`, `var`, `function` | **CRITICAL** | ✅ YES |
| **Python:** Removed `await`, `async`, `def`, wrong indentation | **CRITICAL** | ✅ YES |
| **Java:** Removed `public`, `private`, `static`, `return` | **CRITICAL** | ✅ YES |
| **Go:** Removed `var`, `:=`, `func`, `return` | **CRITICAL** | ✅ YES |
| **Rust:** Removed `let`, `let mut`, `fn`, `return` | **CRITICAL** | ✅ YES |
| **PHP:** Removed `$`, `function`, `return` | **CRITICAL** | ✅ YES |
| **Ruby:** Removed `def`, `end`, `return` | **CRITICAL** | ✅ YES |
| Typo in identifier (non-critical) | **HIGH** | ⚠️ Maybe |
| Breaking API change | **HIGH** | ⚠️ Maybe |

---

## Detection Checklist

When reviewing code, ALWAYS check EVERY LINE - NO EXCEPTIONS:

**GENERAL CHECKS (All Languages):**
- [ ] Are all language keywords present? (check language-specific keywords below)
- [ ] Is variable declaration syntax correct? (language-specific)
- [ ] Are type assignments compatible? (NO type mismatches - check EVERY assignment)
- [ ] Are property/method names valid? (NO typos, NO incorrect prefixes)
- [ ] Are all braces/brackets/parentheses matched?
- [ ] Will this code compile/run in the target language?
- [ ] Are there any breaking API changes?

**C# SPECIFIC:**
- [ ] Is `await` present for ALL async method calls?
- [ ] Are all property names correct? (check JsonSerializerOptions, etc.)
- [ ] No type mismatches? (e.g., `string? = 1` is WRONG)
- [ ] All variables declared with `var` or explicit type?

**JavaScript/TypeScript SPECIFIC:**
- [ ] Is `await` present for ALL async calls?
- [ ] All variables declared with `let`, `const`, or `var`?
- [ ] No type mismatches in TypeScript? (e.g., `const count: number = "test"` is WRONG)
- [ ] All imports correct? (no typos in paths/module names)

**Python SPECIFIC:**
- [ ] Is `await` present for ALL async calls?
- [ ] Indentation correct? (4 spaces, consistent)
- [ ] No type mismatches? (e.g., `count: int = "test"` is WRONG)
- [ ] All imports correct? (no typos)

**Java SPECIFIC:**
- [ ] All access modifiers present? (`public`, `private`, `protected`)
- [ ] No type mismatches? (e.g., `String str = 1` is WRONG)
- [ ] All methods have return types?
- [ ] `return` statements present in non-void methods?

**Go SPECIFIC:**
- [ ] All variables declared with `var` or `:=`?
- [ ] No type mismatches? (e.g., `var count int = "test"` is WRONG)
- [ ] All functions have `func` keyword?
- [ ] `return` statements present?

**Rust SPECIFIC:**
- [ ] All variables declared with `let` or `let mut`?
- [ ] No type mismatches? (e.g., `let count: i32 = "test"` is WRONG)
- [ ] All functions have `fn` keyword?

**PHP SPECIFIC:**
- [ ] All variables have `$` prefix?
- [ ] All functions have `function` keyword?
- [ ] No type mismatches?

**Ruby SPECIFIC:**
- [ ] All methods have `def` keyword?
- [ ] All blocks have `end` keyword?
- [ ] Correct variable prefixes? (`@` for instance, `@@` for class)

