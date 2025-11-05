# Code Review Rules

Bu klasör, AI code reviewer tarafından kullanılan detaylı rule dosyalarını içerir.

## 📋 Mevcut Rule Dosyaları

| Dosya | Kategori | Açıklama |
|-------|----------|----------|
| `compilation.md` | **CRITICAL** | Syntax ve compilation hataları |
| `security.md` | **CRITICAL** | Güvenlik açıkları ve best practices |
| `dotnet-fundamentals.md` | **HIGH** | .NET/C# temel kuralları |
| `performance.md` | **MEDIUM** | Performance optimizasyonları |
| `best-practices.md` | **LOW** | Code quality ve best practices |

---

## 🔧 Nasıl Çalışır?

### 1. Otomatik Yükleme

AI reviewer, `config.yaml`'deki `focus` alanlarına göre ilgili rule'ları otomatik yükler:

```yaml
review:
  focus:
    - compilation       # → compilation.md
    - security         # → security.md
    - performance      # → performance.md
    - dotnet           # → dotnet-fundamentals.md
    - best_practices   # → best-practices.md
```

### 2. Rule Mapping

```python
RULE_FILES = {
    "compilation": "compilation.md",
    "security": "security.md",
    "performance": "performance.md",
    "dotnet": "dotnet-fundamentals.md",
    "best_practices": "best-practices.md",
    "code_quality": "best-practices.md",
    "bugs": "compilation.md",
}
```

### 3. AI Prompt Enhancement

Rule'lar AI prompt'una eklenir:

```
[AI Review Prompt]
---
## SPECIFIC RULES TO FOLLOW:

## Rules for: COMPILATION
[compilation.md içeriği]

## Rules for: SECURITY
[security.md içeriği]
---
Apply these rules strictly when reviewing the code above.
```

---

## 📝 Yeni Rule Ekleme

### 1. Rule Dosyası Oluştur

```bash
touch rules/my-custom-rule.md
```

### 2. Rule İçeriğini Yaz

```markdown
# My Custom Rules

## Priority: CRITICAL/HIGH/MEDIUM/LOW

### Rule 1
❌ **Don't do this**
✅ **Do this instead**

### Examples
...
```

### 3. Mapping Ekle

`services/ai_reviewer.py`:

```python
RULE_FILES = {
    "my_custom": "my-custom-rule.md",
    # ...
}
```

### 4. Config'e Ekle

`config.yaml`:

```yaml
review:
  focus:
    - my_custom
```

---

## 🎯 Rule Yazma Best Practices

### 1. Clear Structure
```markdown
# Category Name

## Priority: [CRITICAL|HIGH|MEDIUM|LOW]

### Rule Name
❌ **Bad Example**
✅ **Good Example**

**Impact:** Açıkla
**Severity:** CRITICAL
```

### 2. Concrete Examples

Soyut kurallar yerine **kod örnekleri** verin:

```csharp
// ❌ Bad
var query = $"SELECT * FROM Users WHERE id={userId}";

// ✅ Good
var query = "SELECT * FROM Users WHERE id=@userId";
```

### 3. Severity Guidelines

| Severity | Kullanım |
|----------|----------|
| **CRITICAL** | Build fail, security vulnerability, data loss |
| **HIGH** | Logic errors, major performance issues |
| **MEDIUM** | Minor performance issues, code smell |
| **LOW** | Style issues, minor improvements |

### 4. Checklist Format

Her rule dosyasının sonuna checklist ekleyin:

```markdown
## Checklist
- [ ] SQL injection prevented
- [ ] Input validation implemented
- [ ] Error handling proper
```

---

## 🧪 Testing Rules

### Test Edelim

1. **Rule dosyasını oluştur**
2. **Redeploy et:** `./redeploy.sh`
3. **PR aç ve gözlemle**

### Debug

```python
# Log'larda rule yüklenmesini kontrol et
logger.info("loaded_rules", area=area, file=rule_file)
```

---

## 📚 Rule File Templates

### Minimal Template

```markdown
# Rule Category

## Priority: MEDIUM

### Rule Name
Description

❌ Bad:
\`\`\`language
bad code
\`\`\`

✅ Good:
\`\`\`language
good code
\`\`\`

## Checklist
- [ ] Check 1
- [ ] Check 2
```

### Full Template

```markdown
# Rule Category

## Priority: CRITICAL

Description of category.

---

## Rule Section 1

### Specific Rule
Details

❌ **Bad:**
\`\`\`language
bad code example
\`\`\`
**Impact:** What happens

✅ **Good:**
\`\`\`language
good code example
\`\`\`
**Why:** Explanation

---

## Severity Guidelines

| Issue | Severity |
|-------|----------|
| Issue 1 | CRITICAL |
| Issue 2 | HIGH |

---

## Checklist
- [ ] Item 1
- [ ] Item 2
```

---

## 🔄 Rule Maintenance

### Regular Updates
- Yeni pattern'ler ekle
- False positive'leri düzelt
- Team feedback'e göre güncelle

### Versioning
Rule'lar git ile versiyonlanır:

```bash
git log rules/compilation.md
```

---

## 💡 Tips

1. **Spesifik ol:** "Code quality" yerine "N+1 query" de
2. **Örnek ver:** Her kural için en az 1 örnek
3. **Severity belirt:** Her violation için severity level
4. **Dile özel:** C# kuralları .NET file'da, Python kuralları Python file'da

---

## 🎓 Best Rule Examples

### Compilation (CRITICAL)
```markdown
### ❌ CRITICAL: Removed `static` keyword
Impact: BUILD FAILS - Method can't be called statically
Severity: CRITICAL
Block Merge: YES
```

### Security (CRITICAL)
```markdown
### ❌ CRITICAL: SQL Injection
Always use parameterized queries
Severity: CRITICAL
```

### Performance (MEDIUM)
```markdown
### ⚠️ N+1 Query
Use Include() to eager load related data
Severity: HIGH
```

---

**Happy Rule Writing! 🎉**

