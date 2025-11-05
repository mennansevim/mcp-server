# 🚀 GitHub Actions ile MCP Server Kurulumu

## 📋 Adım 1: Secrets Ekleyin

GitHub repo'nuzda: **Settings** → **Secrets and variables** → **Actions** → **New repository secret**

### Gerekli Secrets:

```
GROQ_API_KEY
  Value: gsk_your_actual_groq_key_here
  
GROQ_MODEL
  Value: llama-3.3-70b-versatile
  
AI_PROVIDER
  Value: groq

REVIEW_MAX_PATCH_BYTES (opsiyonel)
  Value: 350000

REVIEW_INCLUDE_PATTERNS (opsiyonel)
  Value: **/*.cs,**/*.ts,**/*.js,**/*.py,**/*.java,**/*.go,**/*.rb,**/*.rs,**/*.cpp,**/*.h,**/*.csproj,**/*.sln,**/*.yml,**/*.yaml
```

**Not:** `GITHUB_TOKEN` otomatik olarak sağlanır, eklemenize gerek yok!

---

## 📝 Adım 2: Workflow Dosyasını Ekleyin

Repo'nuzda bu dosyayı oluşturun:

```
.github/workflows/ai-code-review.yml
```

İçeriği:
- ✅ Groq LLM kullanır
- ✅ Secret variables kullanır
- ✅ Dosya pattern filtresi var
- ✅ Diff boyut limiti var
- ✅ Otomatik PR yorum yapar

---

## 🧪 Adım 3: Test Edin

### Test PR Açın:

```bash
git checkout -b test/ai-review

# Test dosyası ekle
cat > test.py << 'EOF'
def unsafe_query(user_input):
    # SQL Injection vulnerability
    query = f"SELECT * FROM users WHERE id = {user_input}"
    return db.execute(query)
EOF

git add test.py
git commit -m "Add test function"
git push -u origin test/ai-review

# PR aç
gh pr create --title "Test AI Review" --body "Testing MCP integration"
```

### Beklenen Sonuç:

PR'da **2-3 dakika içinde** şu yorumu göreceksiniz:

```markdown
## 🤖 AI Code Review

**Score:** 3/10 🔴

### 📝 Summary
Critical security vulnerability detected: SQL Injection

### 📊 Issues Found
- Total: **2**
- 🔴 Critical: **1**
- 🟠 High: **1**

### ⚠️ Issues Details

#### 🔴 1. SQL Injection Vulnerability
**Severity:** CRITICAL
**Location:** `test.py` (Line: 3)

The query uses f-string formatting with user input...

**💡 Suggestion:**
> Use parameterized queries...
```

---

## 🎯 Workflow Özellikleri

### ✅ Yapabilecekleri:

1. **Otomatik Review**: Her PR'da otomatik çalışır
2. **Dosya Filtreleme**: Sadece belirtilen dosya tiplerini inceler
3. **Boyut Kontrolü**: Çok büyük PR'lar için uyarı verir
4. **Güncelleme**: PR her güncellendiğinde review'ı günceller
5. **Detaylı Raporlama**: 
   - Security issues
   - Performance problems
   - Code quality
   - Best practices

### 🎨 Konfigürasyon:

Workflow dosyasındaki env variables'ı değiştirebilirsiniz:

```yaml
env:
  GROQ_MODEL: ${{ secrets.GROQ_MODEL || 'llama-3.3-70b-versatile' }}
  REVIEW_MAX_PATCH_BYTES: ${{ secrets.REVIEW_MAX_PATCH_BYTES || '350000' }}
```

---

## 🔧 Gelişmiş Ayarlar

### Sadece Belirli Dosyaları İncele:

Secret: `REVIEW_INCLUDE_PATTERNS`
```
**/*.cs,**/*.py,**/*.js
```

### Review Tetikleyicilerini Değiştir:

```yaml
on:
  pull_request:
    types: [opened, synchronize]  # reopened'ı çıkar
    paths:
      - 'src/**'  # Sadece src klasörü
      - '!**/*.md'  # Markdown hariç
```

### Farklı Model Kullan:

Secret: `GROQ_MODEL`
```
llama-3.1-70b-versatile
mixtral-8x7b-32768
```

---

## 🐛 Sorun Giderme

### Workflow çalışmıyor

1. **Actions sekmesini kontrol edin**
   - Repo → Actions → "AI Code Review" workflow'unu bulun
   - Hataları görün

2. **Secrets'ları kontrol edin**
   ```bash
   # Settings → Secrets and variables → Actions
   # GROQ_API_KEY var mı?
   ```

3. **Permissions'ları kontrol edin**
   ```yaml
   permissions:
     contents: read
     pull-requests: write  # Bu olmalı!
   ```

### Review yorumu gelmiyor

1. **Workflow log'larını kontrol edin**
   - Actions → Latest run → "Post Review Comment"
   - Hata mesajını okuyun

2. **GITHUB_TOKEN permissions**
   - Repo → Settings → Actions → General
   - Workflow permissions: "Read and write permissions" seçili mi?

3. **Manuel test**
   ```bash
   # Local'de test edin
   cd /Users/sevimm/Documents/Projects/mcp-server
   python test_ai_review.py
   ```

### Groq API hatası

```
Error: The api_key client option must be set
```

**Çözüm:** Secrets'ta `GROQ_API_KEY` var mı kontrol edin:
- Settings → Secrets and variables → Actions
- "GROQ_API_KEY" secret'ını ekleyin

---

## 📊 Maliyet ve Limitler

### Groq (Ücretsiz Tier):
- ✅ Günde ~6,000 requests
- ✅ Token limit: ~14,000/gün
- ✅ Hız: 2-3 saniye/review

### GitHub Actions:
- ✅ Public repo: Sınırsız
- ⚠️ Private repo: 2,000 dakika/ay (ücretsiz)
- ℹ️ Bu workflow: ~1-2 dakika/PR

**Tahmini:** 1,000-2,000 PR/ay review yapabilirsiniz!

---

## 🎁 Bonus: Badge Ekleyin

README.md'nize ekleyin:

```markdown
[![AI Code Review](https://github.com/OWNER/REPO/actions/workflows/ai-code-review.yml/badge.svg)](https://github.com/OWNER/REPO/actions/workflows/ai-code-review.yml)
```

Değiştirin:
- `OWNER`: GitHub kullanıcı adınız
- `REPO`: Repository adınız

---

## ✅ Checklist

Kurulum tamamlandı mı?

- [ ] Secrets eklendi (GROQ_API_KEY, GROQ_MODEL)
- [ ] Workflow dosyası oluşturuldu (.github/workflows/ai-code-review.yml)
- [ ] Test PR açıldı
- [ ] Review yorumu geldi
- [ ] README'ye badge eklendi

**Hepsi ✅ ise tebrikler! 🎉**

---

**Artık her PR otomatik olarak AI review alacak! 🤖✨**


