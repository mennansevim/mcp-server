# MCP AI Code Review Server - Teknik Sunum

> **Proje:** MCP AI Code Review Server  
> **Versiyon:** 1.0.0  
> **Geliştirici:** Mennano  
> **Tarih:** Şubat 2026

---

## SLAYT 1: Kapak

### MCP AI Code Review Server

**Yapay Zeka Destekli, Platform-Bağımsız Otomatik Kod İnceleme Sistemi**

- 4 Platform Desteği (GitHub, GitLab, Bitbucket, Azure DevOps)
- 3 AI Provider (OpenAI, Anthropic/Claude, Groq/Llama)
- 25+ Programlama Dili Desteği
- Otomatik Dil Tespiti ve Dile Özel Rule Sistemi
- MCP Protokolü ile IDE Entegrasyonu
- Config Dashboard ile Merkezi Yönetim

---

## SLAYT 2: Problem Tanımı

### Neden Bu Projeye İhtiyaç Var?

**Mevcut Sorunlar:**

| Problem | Etki |
|---------|------|
| Manuel kod inceleme çok zaman alıyor | Geliştirici verimliliği düşüyor |
| İnsan gözü her hatayı yakalayamıyor | Compilation hataları, güvenlik açıkları kaçıyor |
| Farklı platformlarda farklı araçlar gerekiyor | GitHub'da bir araç, Bitbucket'ta başka bir araç |
| Tutarsız review kalitesi | Reviewer'a bağlı değişen standartlar |
| Mevcut çözümler (CodeRabbit vb.) pahalı ve kısıtlı | Platform bağımlılığı, özelleştirme zorluğu |
| Rule/Standart güncellemeleri manuel | Her güncellemede tüm ekibe bildirim gerekiyor |

**Hedefimiz:**
- Tek webhook endpoint'i ile tüm platformlardan gelen PR'ları otomatik inceleme
- Şirket standartlarına göre özelleştirilebilir AI kuralları
- Self-hosted, tamamen kontrol altında bir çözüm

---

## SLAYT 3: Genel Mimari

### Sistem Mimarisi

```
┌─────────────────────────────────────────────────────────────────────┐
│                        MCP Code Review Server                       │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│   ┌──────────┐     ┌──────────────┐     ┌───────────────────┐      │
│   │ Webhook  │────▶│  Platform    │────▶│    AI Reviewer     │      │
│   │ Handler  │     │  Detection   │     │                   │      │
│   │          │     │              │     │  ┌─────────────┐  │      │
│   └──────────┘     └──────────────┘     │  │   OpenAI    │  │      │
│        ▲                                │  │  (GPT-4)    │  │      │
│        │           ┌──────────────┐     │  ├─────────────┤  │      │
│  ┌─────┴─────┐     │  Language    │     │  │ Anthropic   │  │      │
│  │ Platform  │     │  Detector    │────▶│  │  (Claude)   │  │      │
│  │ Parsers   │     │  (25+ dil)   │     │  ├─────────────┤  │      │
│  │           │     └──────────────┘     │  │   Groq      │  │      │
│  │ - GitHub  │                          │  │  (Llama 3.3)│  │      │
│  │ - GitLab  │     ┌──────────────┐     │  └─────────────┘  │      │
│  │ - Bitbkt  │     │    Rule      │────▶│                   │      │
│  │ - Azure   │     │  Generator   │     └───────────────────┘      │
│  └───────────┘     │  (AI-based)  │              │                 │
│                    └──────────────┘              ▼                 │
│                                        ┌───────────────────┐      │
│   ┌──────────┐     ┌──────────────┐    │ Comment Service   │      │
│   │   MCP    │     │    Diff      │    │ (Summary+Inline)  │      │
│   │  Tools   │     │  Analyzer    │    └───────────────────┘      │
│   │ (SSE)    │     │  (unidiff)   │              │                 │
│   └──────────┘     └──────────────┘              ▼                 │
│                                        ┌───────────────────┐      │
│                                        │ Platform Adapters │      │
│                                        │ (Yorum Gönderme)  │      │
│                                        └───────────────────┘      │
│                                                                     │
├─────────────────────────────────────────────────────────────────────┤
│  Config Dashboard (UI)  │  Rules API  │  Docker/Podman  │  SSE    │
└─────────────────────────────────────────────────────────────────────┘
```

### Review Akışı (5 Adım):

```
1. Webhook Alınır  ───▶  2. Diff Çekilir  ───▶  3. AI İnceleme
       │                       │                       │
       ▼                       ▼                       ▼
  Platform Tespiti       Diff Analizi          Dil Tespiti
  (Header-based)        (unidiff parse)       + Rule Yükleme
                                              + AI Prompt
       │                                           │
       ▼                                           ▼
4. Yorum Gönderimi  ◀──────────────────  5. Status Güncelleme
   (Summary/Inline)                        (Success/Failure)
```

---

## SLAYT 4: Desteklenen Platformlar

### 4 Büyük Platform, Tek Webhook Endpoint

| Platform | Adapter | Parser | CI/CD Entegrasyonu | Durum |
|----------|---------|--------|--------------------|-------|
| **GitHub** | `GitHubAdapter` | `GitHubParser` | GitHub Actions | ✅ Aktif |
| **GitLab** | `GitLabAdapter` | `GitLabParser` | GitLab CI/CD | ✅ Aktif |
| **Bitbucket** | `BitbucketAdapter` | `BitbucketParser` | Bitbucket Pipelines | ✅ Aktif |
| **Azure DevOps** | `AzureAdapter` | `AzureParser` | Azure Pipelines | ✅ Aktif |

### Platform Tespiti - Otomatik Header Algılama

Server, gelen webhook'un hangi platformdan geldiğini **otomatik tespit** eder:

```python
PLATFORM_HEADERS = {
    'x-github-event':    Platform.GITHUB,      # GitHub
    'x-gitlab-event':    Platform.GITLAB,       # GitLab
    'x-event-key':       Platform.BITBUCKET,    # Bitbucket
    'x-vss-activityid':  Platform.AZURE,        # Azure DevOps
}
```

Header bulunamazsa **payload yapısından** da tespit yapabilir (fallback mekanizması).

### Her Platform İçin Tam Destek:

- **Diff Çekme**: PR/MR değişikliklerini API üzerinden çekme
- **Summary Yorum**: PR'a genel değerlendirme yorumu ekleme
- **Inline Yorum**: Sorunlu satırlara doğrudan yorum ekleme
- **Status Güncelleme**: Commit status'u güncelleme (success/failure/pending)
- **Merge Bloklama**: Kritik hatalarda merge'ü engelleme

---

## SLAYT 5: AI Provider Entegrasyonları

### 3 AI Provider - Tam Esneklik

| Provider | Model | Hız | Maliyet | Kullanım Alanı |
|----------|-------|-----|---------|----------------|
| **Groq** | Llama 3.3 70B Versatile | Çok Hızlı | Ücretsiz/Düşük | Varsayılan, yüksek hacimli review |
| **OpenAI** | GPT-4 Turbo | Orta | Orta | Karmaşık kod analizi |
| **Anthropic** | Claude 3.5 Sonnet | Orta | Orta-Yüksek | Detaylı güvenlik analizi |

### OpenAI Entegrasyonu (Yeni Eklenen)

OpenAI entegrasyonu tam olarak eklendi ve diğer provider'lar ile aynı seviyede çalışıyor:

```python
# ai_reviewer.py
elif self.provider == "openai":
    self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    self.model = model or "gpt-4-turbo-preview"
```

**Desteklenen OpenAI Modelleri:**
- `gpt-4-turbo-preview` (varsayılan)
- `gpt-4o`
- `gpt-4o-mini` (maliyet odaklı)
- `o1`, `o1-mini` (reasoning odaklı - gelecek roadmap)

### Provider Değiştirme - Tek Satır Config:

```yaml
# config.yaml
ai:
  provider: "openai"         # openai | anthropic | groq
  model: "gpt-4-turbo-preview"
  temperature: 0.3
  max_tokens: 4096
```

---

## SLAYT 6: Dil Tespiti ve Çoklu Dil Desteği

### 25+ Programlama Dili Otomatik Tespiti

Sistem, PR'daki değişen dosyaların uzantılarından otomatik olarak dili tespit eder:

| Dil Ailesi | Desteklenen Diller | Uzantılar |
|------------|-------------------|-----------|
| **.NET** | C# | `.cs`, `.csx` |
| **JVM** | Java, Kotlin, Scala | `.java`, `.kt`, `.scala` |
| **Web** | JavaScript, TypeScript | `.js`, `.jsx`, `.ts`, `.tsx`, `.mjs` |
| **Scripting** | Python, Ruby, PHP | `.py`, `.rb`, `.php` |
| **Sistem** | Go, Rust, C, C++ | `.go`, `.rs`, `.c`, `.cpp`, `.h` |
| **Mobil** | Swift, Dart | `.swift`, `.dart` |
| **Shell** | Shell, PowerShell | `.sh`, `.bash`, `.ps1` |
| **Data** | SQL, YAML, JSON, XML | `.sql`, `.yaml`, `.json`, `.xml` |
| **Web** | HTML, CSS/SCSS | `.html`, `.css`, `.scss` |

### Dil Tespiti Nasıl Çalışır?

```python
# 1. Dosya uzantılarından dil tespiti
detected_language = LanguageDetector.detect_from_files(files_changed)

# 2. En çok kullanılan dili seçer (Counter ile)
# Örnek: 5 .cs dosyası + 2 .json → Dil: C#

# 3. Config dosyaları (package.json, Dockerfile vb.) 
#    dil tespitine dahil edilmez (false positive önleme)
```

---

## SLAYT 7: Rule Sistemi - MD'den API'ye

### Rules: Markdown Dosyalarından Otomatik API

Rule sistemi, kuralları `.md` dosyaları olarak saklar ve API üzerinden otomatik günceller.

**Mevcut Rule Kategorileri:**

| Kategori | Dosya | Öncelik | İçerik |
|----------|-------|---------|--------|
| Compilation | `compilation.md` | CRITICAL | Syntax, type hataları, eksik keyword'ler |
| Security | `security.md` | CRITICAL | SQL injection, XSS, CSRF, secret exposure |
| Performance | `performance.md` | MEDIUM | N+1 query, gereksiz loop, memory leak |
| Best Practices | `best-practices.md` | LOW | Clean code, SOLID, naming conventions |
| .NET Fundamentals | `dotnet-fundamentals.md` | HIGH | Entity Framework, async/await, LINQ |
| Linter | `linter.md` | LOW | Kod stili, formatting kuralları |

### Dile Özel Rule Oluşturma (AI-Powered)

Sistem, tespit edilen dile göre **otomatik olarak dile özel rule dosyaları** oluşturur:

```
rules/
├── compilation.md           # Genel compilation kuralları
├── security.md              # Genel güvenlik kuralları
├── performance.md           # Genel performans kuralları
├── best-practices.md        # Genel best practices
├── csharp-compilation.md    # C# özel compilation kuralları
├── csharp-security.md       # C# özel güvenlik kuralları
├── csharp-performance.md    # C# özel performans kuralları
├── csharp-best-practices.md # C# özel best practices
├── python-compilation.md    # Python özel compilation kuralları
├── python-security.md       # Python özel güvenlik kuralları
├── python-performance.md    # Python özel performans kuralları
├── python-best-practices.md # Python özel best practices
├── go-compilation.md        # Go özel kuralları
├── go-security.md
├── go-performance.md
└── go-best-practices.md
```

### Rule Oluşturma Akışı:

```
1. PR gelir → 2. Dil tespiti (örn: C#)
      │
      ▼
3. csharp-security.md mevcut mu?
      │
      ├── EVET → Direkt yükle ve AI prompt'a ekle
      │
      └── HAYIR → RuleGenerator ile AI'dan oluştur
                         │
                         ▼
                   4. Genel security.md şablonunu al
                   5. C# diline özel olarak revize et
                   6. csharp-security.md olarak kaydet
                   7. Bir sonraki review'da hazır
```

### API Kendi Rule'larını Güncel Tutuyor

- Rule dosyaları bir kez oluşturulunca cache'lenir
- `force_regenerate=True` ile zorla yenilenebilir
- Her dil/kategori kombinasyonu için ayrı `.md` dosyası
- Git ile versiyonlanır, değişiklik geçmişi takip edilir
- Güncel versiyonlar otomatik indirilir ve uygulanır

---

## SLAYT 8: Review Çıktısı ve Yorum Stratejileri

### 3 Farklı Yorum Stratejisi

```yaml
review:
  comment_strategy: "both"  # summary | inline | both
```

**1. Summary Comment** - PR'a genel bir yorum:
```markdown
## MCP AI Code Review

**Score:** 7/10 ⚠️

### 📊 Detaylı Analiz Özeti (Severity × Type)

| Scope / File Path | 🔴 Critical Security | 🔴 Critical Maintainability | ...
|:------------------|:---:|:---:|...
| **Overall** | 1 | 0 | ...
| `auth.py` | 1 | 0 | ...

### 📊 Issues Found
- Total: **5**
- 🔴 Critical: **1**
- 🟠 High: **2**
- 🟡 Medium: **2**

### ⚠️ Important Issues

#### 🔴 SQL Injection Vulnerability
**Severity:** CRITICAL
**Location:** `auth.py` (Line 42)

Using string concatenation for SQL queries...

**Suggestion:**
> Use parameterized queries...

### 🎯 Recommendation
❌ **Do not merge** - Critical issues must be fixed first.
```

**2. Inline Comments** - Sorunlu satırlara doğrudan yorum:
- Problematic satırın yanına direkt yorum eklenir
- Dosya yolu + satır numarası ile kesin konum

**3. Both** - İkisini birden kullanma (önerilen)

### 3 Farklı Yorum Template'i (Yeni Feature)

Farklı senaryolara göre seçilebilir PR yorum şablonları:

```yaml
# config.yaml
review:
  comment_template: "detailed"  # minimal | detailed | executive
```

---

**Template 1: Minimal** - Hızlı ve öz, küçük PR'lar için ideal

```markdown
## MCP AI Review | Score: 8/10 ✅

**3 issues** found (0 critical, 1 high, 2 medium)

| # | Severity | File | Issue |
|---|----------|------|-------|
| 1 | 🟠 HIGH | `auth.py:42` | Missing input validation |
| 2 | 🟡 MED | `utils.py:18` | Unused import |
| 3 | 🟡 MED | `api.py:65` | Magic number usage |

✅ **Approved** - No blocking issues.
```

> **Kullanım:** Küçük PR'lar, hotfix'ler, typo düzeltmeleri.  
> **Avantaj:** Hızlı okunur, PR thread'i kirletmez.

---

**Template 2: Detailed (Varsayılan)** - Kapsamlı analiz, açıklamalı

```markdown
## MCP AI Code Review

**Score:** 7/10 ⚠️

### 📊 Issues Found
- Total: **5**
- 🔴 Critical: **1** | 🟠 High: **2** | 🟡 Medium: **2**

### 📊 Detaylı Analiz Özeti (Severity × Type)
| Scope | 🔴 Crit. Security | 🔴 Crit. Reliability | 🟠 Major Security | ...
|:------|:--:|:--:|:--:|...
| **Overall** | 1 | 0 | 1 | ...
| `auth.py` | 1 | 0 | 1 | ...

### ⚠️ Important Issues

#### 🔴 SQL Injection Vulnerability
**Severity:** CRITICAL | **File:** `auth.py` (Line 42)
**Category:** Security

Using string concatenation for SQL queries allows attackers to...

**Suggestion:**
> Use parameterized queries: `cursor.execute("SELECT * FROM users WHERE id=?", (user_id,))`

#### 🟠 Missing Error Handling
...

### 🎯 Recommendation
❌ **Do not merge** - Critical issues must be fixed first.

---
*Generated by MCP AI Code Review Server | Review Score: 7/10*
```

> **Kullanım:** Standart PR review'lar, feature branch'ler.  
> **Avantaj:** Tam detay, öneriler, severity tablosu, inline snippet'ler.

---

**Template 3: Executive** - Yönetici/Lead odaklı, risk bazlı özet

```markdown
## MCP AI Review - Executive Summary

### Risk Assessment: ⚠️ MEDIUM RISK

| Metric | Value |
|--------|-------|
| **Quality Score** | 7/10 |
| **Risk Level** | Medium |
| **Estimated Tech Debt** | +2.5 hours |
| **Test Coverage Impact** | -3% (estimated) |

### Risk Breakdown
| Risk Area | Level | Count | Action Required |
|-----------|-------|-------|-----------------|
| Security | 🔴 High | 1 | Immediate fix needed |
| Reliability | 🟠 Medium | 2 | Fix before release |
| Maintainability | 🟡 Low | 2 | Nice to have |

### Key Decisions Needed
1. **SQL Injection in auth.py** - Block merge until fixed? → Recommended: YES
2. **Missing error handling** - Accept tech debt? → Recommended: Fix in this PR

### Summary
Bu PR'da 1 kritik güvenlik açığı tespit edildi. Authentication modülünde 
SQL injection riski mevcut. Merge öncesi düzeltme zorunludur. 
Diğer 4 sorun orta/düşük seviyede olup sprint içinde çözülebilir.

---
*MCP AI Code Review | Executive Report | 2026-02-13*
```

> **Kullanım:** master/main'e merge, release branch'ler, production deploy öncesi.  
> **Avantaj:** Karar vericiler için risk odaklı, tech debt tahmini, aksiyon önerileri.

---

### Template Seçim Mantığı:

| Koşul | Otomatik Template |
|-------|-------------------|
| Diff < 50 satır | `minimal` |
| Standart PR | `detailed` |
| Target branch: master/main/production | `executive` |
| Config'de sabit seçim | Kullanıcı tercihi |

### Detaylı Analiz Tablosu (Branch-Based):

Belirli branch'lere (master, main, preprod, production) yapılan PR'larda otomatik olarak **Severity × Type matris tablosu** eklenir:

```yaml
review:
  detailed_analysis_branches:
    - master
    - main
    - preprod
    - production
```

---

## SLAYT 9: Review Odak Alanları ve Severity Sistemi

### 6 Farklı Focus Area

```yaml
review:
  focus:
    - compilation       # Syntax/compilation hataları
    - security          # Güvenlik açıkları
    - performance       # Performans sorunları
    - bugs              # Logic hataları
    - code_quality      # Kod kalitesi
    - best_practices    # Best practices
```

### 5 Kademeli Severity Sistemi

| Severity | Emoji | Anlam | Aksiyon |
|----------|-------|-------|---------|
| **CRITICAL** | 🔴 | Build fail, güvenlik açığı, veri kaybı | Merge engellenir |
| **HIGH** | 🟠 | Logic hataları, major performans sorunları | Düzeltme önerilir |
| **MEDIUM** | 🟡 | Minor performans, code smell | İyileştirme önerilir |
| **LOW** | 🔵 | Stil sorunları, minor iyileştirmeler | İsteğe bağlı |
| **INFO** | ℹ️ | Bilgilendirme, not | Sadece bilgi |

### Otomatik Merge Bloklama:

```python
# Critical sorun bulunursa → Merge otomatik engellenir
if review_result.block_merge:
    await adapter.update_status(pr_data, "failure", "Critical issues found")
```

### Compilation Kontrolleri (Her Satır İncelenir):

Sistem her satırı şu açılardan kontrol eder:
- **Eksik keyword'ler**: `await`, `async`, `static`, `var`, `const`, `let`, `fn`, `def`...
- **Type mismatch**: `string? = 1`, `int = "test"`
- **Hatalı property/method isimleri**: Typo, yanlış prefix
- **Syntax hataları**: Eksik noktalı virgül, eşleşmeyen parantezler
- **Eksik import'lar**: Kaldırılan using/import ifadeleri

---

## SLAYT 10: MCP Protokolü ve IDE Entegrasyonu

### MCP (Model Context Protocol) Nedir?

MCP, AI modellerinin harici araçlarla iletişim kurmasını sağlayan standart bir protokoldür.

### Sunulan MCP Tools:

| Tool | Açıklama | Kullanım |
|------|----------|----------|
| `review_code` | Kod parçacığı inceleme | Manuel kod review |
| `analyze_diff` | Git diff analizi ve istatistikleri | Diff bilgisi alma |
| `security_scan` | Güvenlik odaklı tarama | Güvenlik denetimi |

### Claude Desktop / MCP Client Kullanımı:

```json
// Tool: review_code
{
  "code": "def login(user, pwd):\n  query = f\"SELECT * FROM users WHERE u='{user}'\"",
  "focus": ["security", "bugs"],
  "language": "python"
}

// Sonuç:
{
  "score": 2,
  "total_issues": 3,
  "issues": [
    {
      "severity": "critical",
      "title": "SQL Injection Vulnerability",
      "description": "Using f-string for SQL query is extremely dangerous...",
      "suggestion": "Use parameterized queries with cursor.execute()"
    }
  ]
}
```

### SSE (Server-Sent Events) Endpoint:

```
GET /mcp/sse  →  Real-time MCP bağlantısı
```

---

## SLAYT 11: Rider IDE Plugin (Geliştirilme Aşamasında)

### JetBrains Rider Plugin Feature

Rider IDE'ye doğrudan entegre edilen bir plugin geliştiriliyor:

**Planlanan Özellikler:**

| Aksiyon | Açıklama | Durum |
|---------|----------|-------|
| **Review Current File** | Açık dosyayı AI ile incele | 🔧 Geliştiriliyor |
| **Review Selection** | Seçili kodu incele | 🔧 Geliştiriliyor |
| **Review Staged Changes** | Git staged değişiklikleri incele | 🔧 Geliştiriliyor |
| **Review Uncommitted Changes** | Tüm uncommitted değişiklikleri incele | 🔧 Geliştiriliyor |

**Teknik Altyapı:**
- **Dil**: Kotlin (JetBrains Plugin SDK)
- **Framework**: IntelliJ Platform Plugin
- **İletişim**: MCP Client → MCP Server (HTTP/SSE)
- **UI**: Tool Window Factory ile özel panel
- **Git**: GitService ile local git entegrasyonu

**Plugin Ayarları:**
- MCP Server URL konfigürasyonu
- API Key yönetimi
- Auto-review toggle
- Custom focus area seçimi

---

## SLAYT 12: Config Dashboard

### Config Yönetim Arayüzü

Config dosyalarını web üzerinden yönetebileceğimiz bir dashboard geliştirildi.

**Dashboard Özellikleri:**

| Özellik | Açıklama |
|---------|----------|
| **AI Provider Seçimi** | OpenAI, Anthropic, Groq arasında geçiş |
| **Model Değiştirme** | Her provider için model seçimi |
| **Platform Yönetimi** | GitHub, GitLab, Bitbucket, Azure enable/disable |
| **Review Stratejisi** | Summary, Inline, Both seçimi |
| **Focus Alanları** | İnceleme alanlarını aç/kapat |
| **Report Level** | Hangi seviyelerin raporlanacağı |
| **Branch Ayarları** | Detaylı analiz yapılacak branch'ler |
| **Rule Yönetimi** | Rule dosyalarını görüntüle/düzenle |

**Örnek Config (config.yaml):**

```yaml
# Server bağlantı ayarları
server:
  host: "0.0.0.0"
  port: 8000
  debug: false

# AI sağlayıcı ve model ayarları
ai:
  provider: "groq"                      # openai | anthropic | groq
  model: "llama-3.3-70b-versatile"      # Provider'a göre model
  temperature: 0.3                      # Yaratıcılık seviyesi
  max_tokens: 4096                      # Maksimum token

# Platform entegrasyonları
platforms:
  github:
    enabled: true
    api_url: "https://api.github.com"
  gitlab:
    enabled: true
    api_url: "https://gitlab.com/api/v4"
  bitbucket:
    enabled: true
    api_url: "https://api.bitbucket.org/2.0"
  azure:
    enabled: true
    api_url: "https://dev.azure.com"

# Review stratejisi
review:
  comment_strategy: "summary"           # inline | summary | both
  detailed_analysis_branches:           # Detaylı tablo branch'leri
    - master
    - main
    - preprod
    - production
  report_levels:                        # Raporlanacak seviyeler
    - critical
    - high
    - medium
  auto_approve: false                   # Otomatik onay
  block_on_critical: true               # Critical'da merge engelle
  focus:                                # İnceleme alanları
    - compilation
    - security
    - performance
    - bugs
    - code_quality
    - best_practices

# Webhook güvenlik
webhook:
  verify_signature: true
  timeout: 300

# Log ayarları
logging:
  level: "INFO"
  format: "json"
```

---

## SLAYT 13: CI/CD Pipeline Entegrasyonları

### Her Platform İçin Hazır Pipeline Config'leri

**GitHub Actions (`examples/github-actions.yml`):**
```yaml
name: AI Code Review
on:
  pull_request:
    types: [opened, synchronize, reopened]
jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Trigger AI Review
        run: |
          curl -X POST ${{ secrets.REVIEW_SERVER_URL }}/webhook \
            -H "Content-Type: application/json" \
            -H "X-GitHub-Event: pull_request" \
            -d @$GITHUB_EVENT_PATH
```

**Bitbucket Pipelines (`examples/bitbucket-pipelines.yml`):**
```yaml
pipelines:
  pull-requests:
    '**':
      - step:
          name: AI Code Review
          script:
            - curl -X POST $REVIEW_SERVER_URL/webhook \
                -H "X-Event-Key: pullrequest:created" \
                -d '{ ... }'
```

**GitLab CI/CD (`examples/gitlab-ci.yml`):**
```yaml
ai-code-review:
  stage: test
  only:
    - merge_requests
  script:
    - curl -X POST $REVIEW_SERVER_URL/webhook \
        -H "X-Gitlab-Event: Merge Request Hook" \
        -d '{ ... }'
```

**Azure Pipelines (`examples/azure-pipelines.yml`):**
```yaml
pr:
  - main
  - master
steps:
- script: |
    curl -X POST $(REVIEW_SERVER_URL)/webhook \
      -H "X-VSS-ActivityId: $(Build.BuildId)" \
      -d '{ ... }'
```

---

## SLAYT 14: Deployment Seçenekleri

### Esnek Deployment

| Yöntem | Script | Açıklama |
|--------|--------|----------|
| **Docker** | `scripts/docker-start.sh` | Standart Docker deployment |
| **Podman** | `scripts/podman-start.sh` | Rootless container çözümü |
| **Docker Compose** | `scripts/podman-compose-start.sh` | Compose ile yönetim |
| **Railway** | `scripts/railway-deploy.sh` | Cloud deployment (PaaS) |
| **Manuel** | `python server.py` | Direkt çalıştırma |

### Dockerfile (Multi-stage Build):

```dockerfile
# Builder stage
FROM python:3.11-slim as builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Production stage
FROM python:3.11-slim
WORKDIR /app
COPY --from=builder /root/.local /root/.local
COPY . .
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=3s \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/')"
CMD ["python", "server.py"]
```

### Redeploy Script (Tek Komut):

```bash
./scripts/redeploy.sh        # Stop → Build → Start → Health Check
./scripts/redeploy.sh --clean # + Eski image'ları temizle
```

---

## SLAYT 15: CodeRabbit vs MCP Code Review Server Karşılaştırması

### Neden CodeRabbit Yerine Kendi Çözümümüz?

| Özellik | CodeRabbit | MCP Code Review Server |
|---------|------------|----------------------|
| **Maliyet** | $12-24/kullanıcı/ay | Self-hosted, sadece AI API maliyeti |
| **Platform Desteği** | GitHub, GitLab | GitHub, GitLab, Bitbucket, Azure DevOps |
| **AI Provider** | Sabit (kendi modeli) | 3 provider seçeneği + değiştirilebilir |
| **Özelleştirme** | Sınırlı config | Tam özelleştirilebilir rule sistemi |
| **Rule Yönetimi** | UI üzerinden sınırlı | Markdown + AI-powered auto-generation |
| **Dile Özel Kurallar** | Genel | Otomatik dile özel rule oluşturma |
| **Veri Gizliliği** | 3. parti sunucular | Self-hosted, tüm veri şirket içinde |
| **IDE Entegrasyonu** | Yok | MCP + Rider Plugin (geliştirilme aşamasında) |
| **Dashboard** | Var | Var (config yönetimi) |
| **API Desteği** | Sınırlı | MCP Tools + REST API |
| **Open Source** | Hayır | Evet (şirket içi) |
| **Merge Bloklama** | Var | Var (critical severity'de otomatik) |
| **Detaylı Tablo** | Yok | Severity × Type matris tablosu |
| **Branch-based Config** | Kısıtlı | Branch'e göre detaylı analiz toggle |

### Maliyet Karşılaştırması (10 Kişilik Ekip):

| | CodeRabbit | MCP Server |
|---|------------|-----------|
| Aylık Sabit | $240/ay | $0 |
| AI API Maliyeti | Dahil | ~$20-50/ay (kullanıma göre) |
| Sunucu Maliyeti | Dahil | ~$5-20/ay (Railway/VPS) |
| **Toplam** | **$240/ay** | **~$25-70/ay** |
| **Yıllık** | **$2,880** | **~$300-840** |
| **Tasarruf** | - | **%70-90** |

---

## SLAYT 16: Güvenlik

### Güvenlik Önlemleri

| Katman | Uygulama |
|--------|----------|
| **Webhook İmza Doğrulama** | `verify_signature: true` - Sahte webhook'ları engeller |
| **API Token Authentication** | Bearer token ile kimlik doğrulama |
| **Environment Variables** | Tüm secret'lar `.env` dosyasında, kod dışında |
| **Hassas Veri Loglama Yok** | Token, password gibi bilgiler loglanmaz |
| **HTTPS Zorunluluğu** | Production'da HTTPS ile çalışma |
| **Rate Limiting** | Aşırı istek koruması (reverse proxy ile) |
| **Self-hosted** | Kod ve veriler tamamen şirket kontrolünde |

### İncelenen Güvenlik Kontrolleri:

AI reviewer, PR'larda şu güvenlik açıklarını tarar:
- SQL Injection
- Cross-Site Scripting (XSS)
- Cross-Site Request Forgery (CSRF)
- Exposed Secrets/Credentials
- Unsafe Deserialization
- Missing Input Validation
- Hardcoded Passwords
- Insecure API Calls

---

## SLAYT 17: Teknik Altyapı ve Teknoloji Stack

### Technology Stack

| Katman | Teknoloji | Versiyon |
|--------|-----------|---------|
| **Framework** | FastAPI | >=0.104.0 |
| **ASGI Server** | Uvicorn | >=0.24.0 |
| **Data Validation** | Pydantic v2 | >=2.5.0 |
| **MCP Protocol** | MCP Python SDK | Latest (GitHub) |
| **AI - OpenAI** | openai | >=1.3.0 |
| **AI - Anthropic** | anthropic | >=0.7.0 |
| **AI - Groq** | groq | >=0.4.0 |
| **GitHub API** | PyGithub | >=2.1.1 |
| **GitLab API** | python-gitlab | >=4.2.0 |
| **Bitbucket API** | atlassian-python-api | >=3.41.0 |
| **Azure API** | azure-devops | >=7.1.0b4 |
| **Diff Parsing** | unidiff | >=0.7.5 |
| **HTTP Client** | httpx | >=0.25.0 |
| **Config** | PyYAML | >=6.0.1 |
| **Logging** | structlog (JSON) | >=23.2.0 |
| **Security** | cryptography, PyJWT | >=41.0.7, >=2.8.0 |
| **Container** | Docker / Podman | - |
| **Python** | 3.11+ | - |

### Proje Yapısı:

```
mcp-server/
├── server.py                    # Ana server (FastAPI + MCP)
├── config.yaml                  # Merkezi konfigürasyon
├── requirements.txt             # Python bağımlılıkları
├── models/
│   └── schemas.py               # Pydantic data modelleri
├── services/
│   ├── ai_reviewer.py           # AI review motoru
│   ├── comment_service.py       # Yorum formatlama
│   ├── diff_analyzer.py         # Diff parse/analiz
│   ├── language_detector.py     # Dil tespiti (25+ dil)
│   └── rule_generator.py        # AI-powered rule oluşturma
├── adapters/
│   ├── base_adapter.py          # Abstract base class
│   ├── github_adapter.py        # GitHub API
│   ├── gitlab_adapter.py        # GitLab API
│   ├── bitbucket_adapter.py     # Bitbucket API
│   └── azure_adapter.py         # Azure DevOps API
├── webhook/
│   ├── handler.py               # Webhook işleme
│   └── parsers/                 # Platform-specific parsers
│       ├── github_parser.py
│       ├── gitlab_parser.py
│       ├── bitbucket_parser.py
│       └── azure_parser.py
├── tools/
│   └── review_tools.py          # MCP Tools (3 tool)
├── rules/                       # Review kuralları (19 dosya)
│   ├── compilation.md
│   ├── security.md
│   ├── performance.md
│   ├── best-practices.md
│   ├── csharp-*.md              # C# özel kuralları
│   ├── python-*.md              # Python özel kuralları
│   └── go-*.md                  # Go özel kuralları
├── examples/                    # CI/CD pipeline örnekleri
│   ├── github-actions.yml
│   ├── gitlab-ci.yml
│   ├── bitbucket-pipelines.yml
│   └── azure-pipelines.yml
├── docker/
│   ├── Dockerfile               # Multi-stage build
│   └── docker-compose.yml
├── scripts/
│   ├── redeploy.sh              # Otomatik redeploy
│   ├── docker-start.sh
│   ├── podman-start.sh
│   └── railway-deploy.sh        # Cloud deploy
├── tests/                       # Test dosyaları
├── docs/                        # Dokümantasyon
└── ide-plugins/
    └── rider-mcp-review/        # Rider IDE Plugin (Kotlin)
```

---

## SLAYT 18: Roadmap - Gelecek Planları

### Kısa Vadeli Roadmap (Q1-Q2 2026)

#### 1. Kategori Bazlı Model Seçimi
Farklı rule kategorileri için farklı AI modelleri kullanabilme:

```yaml
# Planlanan config yapısı:
ai:
  mode: "auto"  # auto | manual
  model_routing:
    compilation:
      model: "gpt-4o"          # Yüksek doğruluk gereken alan
      provider: "openai"
    security:
      model: "claude-3-5-sonnet"  # Güvenlik analizi
      provider: "anthropic"
    performance:
      model: "llama-3.3-70b"   # Hızlı analiz yeterli
      provider: "groq"
    best_practices:
      model: "gpt-4o-mini"     # Düşük maliyet, basit kontrol
      provider: "openai"
    linter:
      model: "llama-3.1-8b"    # Mini model yeterli
      provider: "groq"
```

**Auto Mode Akıllı Yönlendirme:**
- Codebase büyükse → Mini modeller (hız + maliyet optimizasyonu)
- Güvenlik kritik ise → Büyük modeller (doğruluk önceliği)
- Diff küçükse → Hızlı modeller
- Diff büyükse → Parçalayarak farklı modellere dağıtım

#### 2. Public API Oluşturma
Dışarıya açılabilecek bir REST API:

```
POST /api/v1/review          # Kod inceleme
POST /api/v1/security-scan   # Güvenlik taraması
POST /api/v1/diff-analyze    # Diff analizi
GET  /api/v1/rules           # Mevcut kuralları listele
POST /api/v1/rules/generate  # Yeni dil için kural oluştur
GET  /api/v1/languages       # Desteklenen diller
GET  /api/v1/stats           # İnceleme istatistikleri
POST /api/v1/batch-review    # Toplu kod inceleme
```

**API Kullanım Senaryoları:**
- CI/CD pipeline'lardan doğrudan API çağrısı
- 3. parti araçlarla entegrasyon
- Dashboard'dan review tetikleme
- Mobil uygulamalar / bot entegrasyonları
- Webhook kullanmadan direkt review

**API Güvenliği:**
- API Key authentication
- Rate limiting (tier bazlı)
- Request/Response logging
- Swagger/OpenAPI dokümantasyonu

#### 3. PR Yorum Template Sistemi
3 farklı yorum template'i ile farklı senaryolara uyum:

| Template | Hedef Kitle | Kullanım |
|----------|------------|----------|
| `minimal` | Geliştiriciler | Küçük PR, hotfix, hızlı review |
| `detailed` | Tüm ekip | Standart PR review (varsayılan) |
| `executive` | Tech Lead / Manager | Risk analizi, tech debt, karar desteği |

- Config'den sabit seçim veya otomatik seçim (diff boyutu + target branch)
- Dashboard'dan template önizleme ve özelleştirme
- Takım bazlı varsayılan template atama

#### 4. Rider IDE Plugin Tamamlama
- Review Current File → Sonuç paneli
- Selection review
- Staged/Uncommitted changes review
- Tool window ile gerçek zamanlı sonuç gösterimi
- JetBrains Marketplace'e yayınlama

### Orta Vadeli Roadmap (Q3-Q4 2026)

#### 5. Review İstatistikleri Dashboard
```
┌──────────────────────────────────────────────┐
│           Review Analytics Dashboard          │
├──────────────────────────────────────────────┤
│ Toplam Review: 1,234    │  Avg Score: 7.8    │
│ Critical Bug: 23        │  Fixed Rate: 87%   │
│ Top 5 Issue:            │  Trend: ↑ 12%      │
│ 1. Missing await        │                    │
│ 2. SQL Injection        │                    │
│ 3. N+1 Query           │                    │
│ 4. Null Reference      │                    │
│ 5. Unused Variable     │                    │
├──────────────────────────────────────────────┤
│ [Haftalık Grafik]  [Takım Bazlı]  [Dil Bazlı]│
└──────────────────────────────────────────────┘
```

#### 6. Çoklu IDE Plugin Desteği
- VS Code Extension
- IntelliJ IDEA Plugin
- Visual Studio Extension
- Neovim Plugin

#### 7. Team/Organization Bazlı Rule Yönetimi
- Takıma özel rule set'leri
- Role-based access control
- Rule versioning ve rollback
- A/B testing (farklı rule setleri ile karşılaştırma)

#### 8. Akıllı Review Caching
- Aynı pattern'ler için cache mekanizması
- Benzer kodlar için önceki review'ları referans alma
- Incremental review (sadece yeni değişiklikleri incele)

#### 9. PR Review Summary Email/Slack Notifications
- Slack webhook entegrasyonu
- Microsoft Teams entegrasyonu
- Email digest (günlük/haftalık özet)
- Custom notification rules

---

## SLAYT 19: Önerilen Ek Feature'lar

### Modele Göre Tavsiye Edilen Yeni Özellikler

#### 1. Code Complexity Scoring (Karmaşıklık Analizi)
PR'daki değişikliklerin cyclomatic complexity, cognitive complexity gibi metrikleri ölçülüp rapora eklenmesi:

```markdown
### 📐 Complexity Analysis
| Dosya | Cyclomatic | Cognitive | Risk |
|-------|-----------|-----------|------|
| auth.py | 15 | 22 | 🔴 High |
| utils.py | 3 | 4 | 🟢 Low |
```

**Neden?** Karmaşık kodlar bug üretme olasılığı yüksek olduğundan, erken uyarı mekanizması sağlar.

#### 2. Auto-Fix Suggestion (Otomatik Düzeltme Önerisi)
AI'ın sadece sorunu bulması değil, aynı zamanda düzeltilmiş kodu da üretmesi ve PR'a "suggested change" olarak eklemesi:

```diff
- query = f"SELECT * FROM users WHERE id={user_id}"
+ query = "SELECT * FROM users WHERE id=@user_id"
+ cursor.execute(query, {"user_id": user_id})
```

**Neden?** Geliştiricinin düzeltme süresini %50-80 azaltır.

#### 3. Learning from Feedback (Geri Bildirimden Öğrenme)
Geliştiricilerin AI review yorumlarına verdiği tepkiler (thumbs up/down) ile zamanla daha iyi sonuçlar üretmesi:

```
👍 Yararlı bulundu → Bu tür tespitleri artır
👎 Gereksiz bulundu → Bu pattern'i false positive olarak işaretle
```

**Neden?** Zamanla false positive oranı düşer, ekibe özel review kalitesi artar.

---

## SLAYT 20: Demo ve Canlı Gösterim

### Canlı Demo Senaryosu

**Adım 1:** PR açılır (herhangi bir platformda)

**Adım 2:** Webhook tetiklenir

```
🔔 WEBHOOK RECEIVED
════════════════════════════════════════
📦 Platform: GITHUB
🔗 PR #42: Fix user authentication
👤 Author: developer
🌿 feature/auth-fix → main
────────────────────────────────────────
📥 Step 1/5: Fetching diff from platform...
✅ Diff fetched successfully (2,450 bytes)

🔍 Step 2/5: Analyzing diff...
✅ Found 3 changed file(s):
   📄 src/auth/login.py
   📄 src/auth/middleware.py
   📄 tests/test_auth.py

🤖 Step 3/5: Starting AI code review...
   Provider: GROQ
   Model: llama-3.3-70b-versatile
   Focus areas: compilation, security, performance, bugs

✅ AI Review completed!
   Score: 6/10
   Issues: 4 total
   🔴 Critical: 1
   🟠 High: 1
   🟡 Medium: 2

💬 Step 4/5: Posting review comments...
   📝 Summary comment posted
   💭 3 inline comments posted

📊 Step 5/5: Updating PR status...
   ❌ Status: FAILURE (Critical issues found)

🎉 REVIEW COMPLETED
════════════════════════════════════════
```

**Adım 3:** PR'da AI review yorumları görünür

**Adım 4:** Geliştirici düzeltmeleri yapar, yeni commit push eder

**Adım 5:** Webhook tekrar tetiklenir, yeni review yapılır

**Adım 6:** Sorunlar düzeltilmişse → Score artar → Merge açılır

---

## SLAYT 21: Sonuç ve Özet

### Proje Değer Önerisi

| Değer | Açıklama |
|-------|----------|
| **Zaman Tasarrufu** | Manuel review süresi %60-80 azalır |
| **Tutarlılık** | Her PR aynı standartlarla incelenir |
| **Erken Hata Tespiti** | Compilation/güvenlik hataları merge öncesi yakalanır |
| **Maliyet Optimizasyonu** | CodeRabbit'e göre %70-90 tasarruf |
| **Esneklik** | 4 platform, 3 AI provider, 25+ dil |
| **Kontrol** | Self-hosted, tamamen şirket kontrolünde |
| **Ölçeklenebilirlik** | Docker/Podman ile kolay ölçekleme |
| **Öğrenen Sistem** | AI-powered rule generation, dile özel kurallar |

### Anahtar Metrikler:

```
📊 4 Platform Desteği    → GitHub, GitLab, Bitbucket, Azure DevOps
🤖 3 AI Provider         → OpenAI, Anthropic, Groq
🌐 25+ Programlama Dili  → Otomatik tespit
📝 19 Rule Dosyası       → AI-generated, dile özel
🔧 3 MCP Tool            → IDE entegrasyonu
📦 5 Deployment Yöntemi  → Docker, Podman, Railway, Compose, Manuel
🧪 5 Test Dosyası        → Unit + Integration
📋 4 CI/CD Pipeline Örneği → Her platform için hazır config
```

---

## SLAYT 22: Soru-Cevap

### Sık Sorulan Sorular

**S: Hangi AI provider'ı önerirsiniz?**  
C: Yüksek hacim + düşük maliyet için Groq (Llama 3.3), detaylı analiz için OpenAI (GPT-4), güvenlik odaklı inceleme için Anthropic (Claude).

**S: Self-hosted zorunlu mu?**  
C: Evet, veri gizliliği açısından tavsiye edilen. Railway gibi PaaS çözümleri de kullanılabilir.

**S: Review ne kadar sürer?**  
C: Ortalama 10-30 saniye (diff boyutuna ve AI provider'a bağlı).

**S: False positive oranı nedir?**  
C: Rule sistemi ile sürekli iyileştirilmektedir. Dile özel kurallar false positive'i minimize eder.

**S: Mevcut pipeline'a entegre etmek zor mu?**  
C: Hayır. Her platform için hazır YAML config'leri var. Tek satır curl komutu ile entegre edilir.

---

**Hazırlayan:** Mennano Development Team  
**Versiyon:** 1.0.0  
**Son Güncelleme:** Şubat 2026
