# C# Compilation Rules

## Priority: CRITICAL
**If ANY of these rules are violated, mark as CRITICAL and set block_merge=true**

---

## CRITICAL: Async/Await Keywords

### Missing `await` Keyword
❌ **CRITICAL:** Removing `await` from async method calls causes compilation errors

**Bad:**
```csharp
// Missing await - COMPILATION ERROR
writer.WriteLineAsync(JsonSerializer.Serialize(error));
```

**Good:**
```csharp
// await is REQUIRED for async methods
await writer.WriteLineAsync(JsonSerializer.Serialize(error));
```

**Impact:** C# compiler requires `await` when calling async methods. Without it, the method returns a `Task` instead of executing, causing compilation errors.

---

## CRITICAL: Type Mismatches

### Incompatible Type Assignments
❌ **CRITICAL:** Cannot assign incompatible types

**Bad:**
```csharp
string? line = 1;  // COMPILATION ERROR: Cannot convert int to string
int count = "test"; // COMPILATION ERROR: Cannot convert string to int
```

**Good:**
```csharp
string? line = null;     // Correct: null can be assigned to nullable string
string? line = "test";   // Correct: string literal
int count = 0;           // Correct: integer literal
```

**Impact:** C# is strongly typed. Type mismatches cause immediate compilation failures.

---

## CRITICAL: Invalid Property/Method Names

### Property Name Typos
❌ **CRITICAL:** Changing property names incorrectly breaks compilation

**Bad:**
```csharp
var options = new JsonSerializerOptions {
    _PropertyNameCaseInsensitive = true,  // COMPILATION ERROR: Property doesn't exist
    PropertyNameCaseInsensitiv = true,    // COMPILATION ERROR: Typo in property name
};
```

**Good:**
```csharp
var options = new JsonSerializerOptions {
    PropertyNameCaseInsensitive = true,  // Correct property name
    AllowTrailingCommas = true,
};
```

**Common Mistakes:**
- Adding underscore prefix to properties (only valid for private fields)
- Typos in property names (case-sensitive!)
- Using wrong property names from different classes

**Impact:** Invalid property names cause compilation errors. C# property names are case-sensitive and must match exactly.

---

## Variable Declarations

### Missing Type or `var`
❌ **CRITICAL:** C# requires explicit type or `var` keyword

**Bad:**
```csharp
line = "test";  // COMPILATION ERROR: Variable not declared
```

**Good:**
```csharp
var line = "test";        // Correct: var keyword
string line = "test";     // Correct: explicit type
string? line = null;      // Correct: nullable type
```

---

## Method Modifiers

### Removing Keywords
❌ **CRITICAL:** Removing method modifiers breaks compilation

**Bad:**
```csharp
// Removed static - breaks all callers
PullRequestReviewEvent DetermineReviewEvent(ReviewResponse review)

// Removed async - signature mismatch
Task<ReviewResponse> ReviewAsync(string patch)
```

**Good:**
```csharp
static PullRequestReviewEvent DetermineReviewEvent(ReviewResponse review)
async Task<ReviewResponse> ReviewAsync(string patch)
```

---

## Nullable Reference Types

### Nullable Type Changes
❌ **CRITICAL:** Changing nullable types incorrectly

**Bad:**
```csharp
string? line = null;
// Later changed to:
string line = null;  // May cause warnings/errors if nullable reference types enabled
```

**Good:**
```csharp
string? line = null;  // Correct: nullable string
string line = "test"; // Correct: non-nullable with value
```

---

## Generic Type Parameters

### Removing Generic Parameters
❌ **CRITICAL:** Removing generic type parameters breaks compilation

**Bad:**
```csharp
List items = new List();  // COMPILATION ERROR: List requires type parameter
```

**Good:**
```csharp
List<string> items = new List<string>();
var items = new List<string>();  // Also correct with var
```

---

## Examples

### ❌ CRITICAL ERROR: Removed `await`
```diff
- await writer.WriteLineAsync(JsonSerializer.Serialize(error));
+ writer.WriteLineAsync(JsonSerializer.Serialize(error));
```
**Impact:** Missing `await` causes compilation error. Method returns `Task` instead of executing.

### ❌ CRITICAL ERROR: Type mismatch
```diff
- string? line;
+ string? line = 1;
```
**Impact:** Cannot assign `int` to `string?`. COMPILATION ERROR.

### ❌ CRITICAL ERROR: Invalid property name
```diff
- PropertyNameCaseInsensitive = true,
+ _PropertyNameCaseInsensitive = true,
```
**Impact:** `_PropertyNameCaseInsensitive` is not a valid property. COMPILATION ERROR.

---

## Detection Checklist

When reviewing C# code, ALWAYS check:
- [ ] Is `await` present for ALL async method calls?
- [ ] Are all type assignments compatible? (no `string? = 1`)
- [ ] Are all property names correct? (check exact spelling, case-sensitive)
- [ ] Are property names valid? (no underscore prefix unless private field)
- [ ] Are all variable declarations present? (`var` or explicit type)
- [ ] Are method modifiers correct? (`static`, `async`, `public`, etc.)
- [ ] Will this code compile without errors?

---

## Severity Guidelines

| Violation | Severity | Block Merge |
|-----------|----------|-------------|
| Missing `await` keyword | **CRITICAL** | ✅ YES |
| Type mismatch | **CRITICAL** | ✅ YES |
| Invalid property name | **CRITICAL** | ✅ YES |
| Missing variable declaration | **CRITICAL** | ✅ YES |
| Removed method modifier | **CRITICAL** | ✅ YES |
| Missing generic type parameter | **CRITICAL** | ✅ YES |

---

## Common C# Compilation Errors to Catch

1. **CS4014**: "Because this call is not awaited, execution continues..."
   - **Cause:** Missing `await` keyword
   - **Fix:** Add `await` before async method call

2. **CS0029**: "Cannot implicitly convert type 'X' to type 'Y'"
   - **Cause:** Type mismatch
   - **Fix:** Use correct type or explicit cast

3. **CS0117**: "'Type' does not contain a definition for 'Property'"
   - **Cause:** Invalid property name
   - **Fix:** Check property name spelling and case

4. **CS0103**: "The name 'variable' does not exist in the current context"
   - **Cause:** Missing variable declaration
   - **Fix:** Add `var` or explicit type declaration

**ALWAYS mark these as CRITICAL and block merge!**

