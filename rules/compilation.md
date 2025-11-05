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

2. **Variable Declarations**
   - ❌ C# **requires** type or `var` keyword for local variables
   - ✅ CORRECT: `var name = "test";` or `string name = "test";`
   - ❌ WRONG: `name = "test";` (missing declaration)

3. **Type System**
   - ❌ Removing generic type parameters: `List<T>` → `List`
   - ❌ Changing nullable types: `string?` → `string`
   - ❌ Type mismatches in assignments

4. **Required Elements**
   - ❌ Removing `using` statements that are needed
   - ❌ Removing base class or interface implementations
   - ❌ Breaking inheritance chain

### JavaScript / TypeScript
1. **Variable Declaration**
   - ❌ Removing `let`, `const`, or `var` keyword
   - ✅ CORRECT: `let x = 5;` or `const y = 10;`
   - ❌ WRONG: `x = 5;` (creates global variable)

2. **Type Annotations (TypeScript)**
   - ❌ Removing type annotations in strict mode
   - ❌ Changing interface/type definitions used by other files

### Python
1. **Indentation**
   - ❌ Incorrect indentation breaks code blocks
   - ❌ Mixing tabs and spaces

2. **Type Hints**
   - ⚠️ Removing type hints reduces type safety

### Java
1. **Access Modifiers**
   - ❌ Removing `public`, `private`, `protected`
   - ❌ Removing `static` from static members

2. **Type System**
   - ❌ Generic type erasure issues
   - ❌ Incorrect type casting

---

## Examples

### ❌ CRITICAL ERROR: Removed `static` keyword
```diff
- static PullRequestReviewEvent DetermineReviewEvent(ReviewResponse review)
+ PullRequestReviewEvent DetermineReviewEvent(ReviewResponse review)
```
**Impact:** Non-static method cannot be called without object instance. BUILD FAILS.

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
| Removed language keyword | **CRITICAL** | ✅ YES |
| Syntax error | **CRITICAL** | ✅ YES |
| Typo in identifier | **HIGH** | ⚠️ Maybe |
| Missing semicolon (if required) | **CRITICAL** | ✅ YES |
| Breaking API change | **HIGH** | ⚠️ Maybe |

---

## Detection Checklist

When reviewing code, ALWAYS check:
- [ ] Are all language keywords present?
- [ ] Is variable declaration syntax correct?
- [ ] Are all braces/brackets matched?
- [ ] Will this code compile in the target language?
- [ ] Are there any breaking API changes?

