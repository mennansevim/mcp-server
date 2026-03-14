# MCP AI Code Review Server — Teknik Sunum

> **Proje:** MCP AI Code Review Server  
> **Versiyon:** 2.0.0  
> **Geliştirici:** Mennano  
> **Tarih:** Mart 2026  
> **Sunum Formatı:** NotebookLM / PowerPoint uyumlu — her bölüm bir slayta karşılık gelir

---

## SLAYT 1: Kapak

### MCP AI Code Review Server

**Yapay Zeka Destekli, Platform-Bağımsız Otomatik Kod İnceleme Sistemi**

- 4 Platform: GitHub · GitLab · Bitbucket · Azure DevOps
- 3 AI Provider: OpenAI (GPT-4) · Anthropic (Claude 3.5) · Groq (Llama 3.3)
- 25+ Programlama Dili Desteği
- MCP Protokolü ile IDE Entegrasyonu
- AI ile Otomatik Rule Üretimi
- Modüler Template Sistemi ile Özelleştirilebilir PR Yorumları
- **OWASP Top 10 Security Deep Scan**
- **AI Slop Detection — Düşük Kalite AI Kodu Tespiti**
- **Live Dashboard & Review Analytics**
- Self-Hosted, Açık Kaynak, Tam Kontrol

---

## SLAYT 2: Neden Bu Projeye İhtiyaç Var?

### Problem Tanımı

Yazılım geliştirme sürecinde Pull Request (PR) inceleme aşaması kritik bir kalite kontrol mekanizmasıdır. Ancak mevcut durumda ciddi sorunlar yaşanmaktadır:

| Problem | Etki | Maliyet |
|---------|------|---------|
| Manuel kod inceleme çok zaman alıyor | Geliştirici 2-4 saat/gün review'a harcıyor | Üretkenlik kaybı |
| İnsan gözü her hatayı yakalayamıyor | Compilation hataları, güvenlik açıkları kaçıyor | Prodüksiyon hataları |
| Farklı platformlarda farklı araçlar | GitHub'da bir araç, Bitbucket'ta başka | Araç maliyeti + eğitim |
| Tutarsız review kalitesi | Reviewer'a göre değişen standartlar | Kod kalitesi düşüşü |
| AI ile yazılan kod kalitesizleşiyor | Copilot/ChatGPT ile üretilen "slop" kod artıyor | Teknik borç birikimi |
| Güvenlik taramaları ayrı araç gerektiriyor | SAST, DAST, secret scanning ayrı kurulumlar | Araç çeşitliliği |
| Mevcut çözümler pahalı | CodeRabbit: $12-24/kullanıcı/ay | Yüksek lisans maliyeti |
| Mevcut çözümler kısıtlı | Platform bağımlı, özelleştirme zor | Vendor lock-in |
| Veri gizliliği endişesi | Kod 3. parti sunuculara gidiyor | Compliance riski |
| Review metrikleri takip edilemiyor | Hangi sorunlar tekrar ediyor, kim ne kadar bloklanıyor? | Görünürlük eksikliği |

### Hedefimiz

Tek bir webhook endpoint'i ile tüm platformlardan gelen PR'ları otomatik, tutarlı ve düşük maliyetle inceleyen — güvenlik taraması, AI slop tespiti ve review analytics dahil — şirket standartlarına göre tamamen özelleştirilebilir, self-hosted bir çözüm üretmek.

---

## SLAYT 3: Neden Python?

### Teknoloji Seçimi Gerekçesi

Python'ın bu proje için tercih edilmesinin somut teknik nedenleri:

**1. AI/ML Ekosisteminin Merkezi**
- OpenAI, Anthropic ve Groq'un resmi SDK'ları Python-first
- `openai>=1.3.0`, `anthropic>=0.7.0`, `groq>=0.4.0` — tüm SDK'lar production-ready
- AI provider'lar arasında geçiş tek satır config değişikliğiyle mümkün

**2. Hızlı Prototipleme ve Yüksek Verimlilik**
- FastAPI ile dakikalar içinde production-ready REST API
- Pydantic v2 ile tip güvenliği + otomatik validation
- `async/await` ile native asynchronous I/O

**3. Platform API Kütüphaneleri**
- `PyGithub` → GitHub, `python-gitlab` → GitLab, `atlassian-python-api` → Bitbucket, `azure-devops` → Azure DevOps

**4. MCP (Model Context Protocol) Desteği**
- MCP'nin resmi Python SDK'sı aktif olarak geliştirilmekte
- SSE (Server-Sent Events) transport desteği built-in

**5. DevOps ve Deployment Kolaylığı**
- Docker image boyutu: ~150MB (python:3.11-slim base)
- Railway, Heroku, AWS Lambda gibi PaaS platformlarına dakikalar içinde deploy

### Alternatif Karşılaştırma

| Kriter | Python | Node.js | C#/.NET | Go |
|--------|--------|---------|---------|-----|
| AI SDK Olgunluğu | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ | ⭐⭐ |
| Platform API Kütüphaneleri | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ |
| Geliştirme Hızı | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ |
| MCP SDK Desteği | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐ | ⭐ |
| Async I/O | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |

**Sonuç:** AI-first bir projenin doğal dili Python'dır.

---

## SLAYT 4: Projenin Temelleri — Mimari Genel Bakış

### Sistem Mimarisi

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       MCP AI Code Review Server v2.0                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌────────────┐    ┌───────────────┐    ┌───────────────────────────────┐   │
│  │  Webhook   │───▶│   Platform    │───▶│       AI Review Engine        │   │
│  │  Handler   │    │  Detection    │    │                               │   │
│  │            │    │  (Auto)       │    │  ┌─────────────────────────┐  │   │
│  └────────────┘    └───────────────┘    │  │   Provider Router       │  │   │
│       ▲                                 │  │  Groq│OpenAI│Anthropic  │  │   │
│       │            ┌───────────────┐    │  └─────────────────────────┘  │   │
│  ┌────┴───────┐    │   Language    │    │                               │   │
│  │  Platform  │    │   Detector   │───▶│  ┌─────────────────────────┐  │   │
│  │  Parsers   │    │   (25+ dil)  │    │  │   Review Modules        │  │   │
│  │            │    └───────────────┘    │  │  • Code Quality         │  │   │
│  │ ┌────────┐ │                         │  │  • Security Deep Scan   │  │   │
│  │ │GitHub  │ │    ┌───────────────┐    │  │  • AI Slop Detection    │  │   │
│  │ ├────────┤ │    │ Rules Helper  │───▶│  │  • Compilation Check    │  │   │
│  │ │GitLab  │ │    │ (MD→Context)  │    │  └─────────────────────────┘  │   │
│  │ ├────────┤ │    └───────────────┘    └───────────────────────────────┘   │
│  │ │Bitbckt │ │                                    │                        │
│  │ ├────────┤ │    ┌───────────────┐               ▼                        │
│  │ │Azure   │ │    │ Rule          │    ┌───────────────────────────────┐   │
│  │ └────────┘ │    │ Generator     │    │      Comment Service          │   │
│  └────────────┘    │ (AI-powered)  │    │  ┌─────────────────────────┐  │   │
│                    └───────────────┘    │  │ Template Engine         │  │   │
│  ┌────────────┐                         │  │ Default│Detailed│Exec.  │  │   │
│  │  MCP Tools │    ┌───────────────┐    │  │ + AI Slop Badge         │  │   │
│  │  (SSE)     │    │ Diff Analyzer │    │  │ + Security Score Badge  │  │   │
│  │            │    │ (unidiff)     │    │  └─────────────────────────┘  │   │
│  │ review_code│    └───────────────┘    └───────────────────────────────┘   │
│  │ analyze_dif│                                    │                        │
│  │ sec_scan   │                                    ▼                        │
│  └────────────┘    ┌───────────────┐    ┌───────────────────────────────┐   │
│                    │  Analytics    │◀───│   Platform Adapters           │   │
│  ┌────────────┐    │  Store        │    │   (Yorum + Status Post)      │   │
│  │ React UI   │    │  (In-memory)  │    └───────────────────────────────┘   │
│  │ Dashboard  │    └───────────────┘                                        │
│  │ Analytics  │                                                             │
│  │ Config     │    ┌───────────────┐                                        │
│  └────────────┘    │ Live Log      │                                        │
│                    │ Store         │                                        │
│                    │ (Streaming)   │                                        │
│                    └───────────────┘                                        │
├─────────────────────────────────────────────────────────────────────────────┤
│  FastAPI │ React+Vite │ MCP/SSE │ Docker │ Structured Logging (JSON)       │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Temel Tasarım İlkeleri

| İlke | Uygulama |
|------|----------|
| **Platform Agnostik** | Tek webhook endpoint, otomatik platform tespiti |
| **Provider Agnostik** | Abstract AI interface, factory pattern ile provider seçimi |
| **Modüler Mimari** | Her bileşen bağımsız, değiştirilebilir, test edilebilir |
| **Config-Driven** | Tüm davranışlar `config.yaml` + UI Settings ile yönetilir |
| **Self-Hosted** | Tüm veriler şirket kontrolünde, 3. parti bağımlılığı yok |
| **Observable** | Live dashboard, analytics, structured logging |

---

## SLAYT 5: Review Akışı — Uçtan Uca

### PR Review Lifecycle (5 Adım)

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  1. WEBHOOK  │────▶│  2. DIFF     │────▶│  3. AI       │
│  ALINDI      │     │  ÇEKİLDİ     │     │  İNCELEME    │
│              │     │              │     │              │
│ Platform     │     │ Adapter ile  │     │ • Code Review│
│ Tespiti      │     │ API'den diff │     │ • Security   │
│ (Header)     │     │ çekilir      │     │   Deep Scan  │
│              │     │              │     │ • AI Slop    │
│ Live Log     │     │ Dil Tespiti  │     │   Detection  │
│ Başlar       │     │ Rule Yükleme │     │ • Short-Circ.│
└──────────────┘     └──────────────┘     └──────────────┘
                                                │
┌──────────────┐     ┌──────────────┐           │
│  5. STATUS   │◀────│  4. YORUM    │◀──────────┘
│  GÜNCELLEME  │     │  GÖNDERİMİ   │
│              │     │              │
│ success /    │     │ Summary +    │
│ failure      │     │ Inline +     │
│ (auto block) │     │ Badges       │
│              │     │ (Template)   │
│ Analytics    │     │              │
│ Kaydı        │     │ AI Slop +    │
│              │     │ Security     │
│              │     │ Badges       │
└──────────────┘     └──────────────┘
```

### Yeni Modüller (v2.0)

| Modül | Açıklama | Tetiklenme |
|-------|----------|------------|
| **Security Deep Scan** | OWASP Top 10 + Secret Leak tespiti | Her review'da otomatik |
| **AI Slop Detection** | Düşük kalite AI-generated kod tespiti | Her review'da otomatik |
| **Live Log Store** | Review adımlarını real-time streaming | Webhook geldiğinde |
| **Analytics Store** | Review metriklerini kaydet ve aggrege et | Review tamamlandığında |

---

## SLAYT 6: Security Deep Scan — OWASP Top 10

### Kapsamlı Güvenlik Taraması

Her PR review'ında AI, OWASP Top 10 framework'ü kullanarak derinlemesine güvenlik analizi yapar.

### OWASP Top 10 Kapsam

| ID | Kategori | Severity | Taranan Pattern'ler |
|----|----------|----------|---------------------|
| **A1** | Injection | 🔴 CRITICAL | SQL/NoSQL/OS command injection, SSTI |
| **A2** | Broken Authentication | 🔴 CRITICAL | Hardcoded credentials, weak password |
| **A3** | Sensitive Data Exposure | 🔴 CRITICAL | PII logging, missing encryption |
| **A4** | XXE | 🟠 HIGH | XML parsing without disabled entities |
| **A5** | Broken Access Control | 🟠 HIGH | Missing auth checks, IDOR, path traversal |
| **A6** | Security Misconfiguration | 🟠 HIGH | Debug mode, default credentials, CORS * |
| **A7** | XSS | 🟠 HIGH | innerHTML, reflected/stored XSS |
| **A8** | Insecure Deserialization | 🔴 CRITICAL | BinaryFormatter, pickle, eval() |
| **A9** | Known Vulnerable Components | 🟡 MEDIUM | Deprecated libs, MD5 hashing |
| **A10** | Insufficient Logging | 🔵 LOW | Missing audit trail |

### Secret Leak Detection

Kod içinde expose edilen secret'ları otomatik tespit eder:

| Pattern | Örnek | Severity |
|---------|-------|----------|
| API Keys | `api_key = "sk-..."` | 🔴 CRITICAL |
| Passwords | `password = "admin123"` | 🔴 CRITICAL |
| Connection Strings | `mongodb://user:pass@host` | 🔴 CRITICAL |
| Private Keys | `-----BEGIN RSA PRIVATE KEY-----` | 🔴 CRITICAL |
| Cloud Credentials | `AKIA...` (AWS), `AIza...` (GCP) | 🔴 CRITICAL |

### Security Score

Her review sonrası 0-10 arası security score hesaplanır:

```python
# Penalty sistemi
Critical issue  → -4 puan
High issue      → -2 puan
Medium issue    → -1 puan

# Başlangıç: 10, minimum: 0
security_score = max(0, 10 - total_penalty)
```

### Veri Modeli

```python
class ReviewIssue(BaseModel):
    # ... mevcut alanlar ...
    owasp_id: Optional[str]     # "A1", "A2", ... "A10"
    cwe_id: Optional[str]       # "CWE-89", "CWE-79", ...
    threat_type: Optional[str]  # "injection", "broken_auth", "secret_leak", ...

class ReviewResult(BaseModel):
    # ... mevcut alanlar ...
    security_score: int              # 0-10
    security_issues_count: int
    secret_leak_detected: bool
    owasp_categories_hit: List[str]  # ["A1", "A3", "A7"]
```

### PR Comment'te Görünüm

```markdown
![Security](https://img.shields.io/badge/Security-6%2F10-orange)
![Secret Leak](https://img.shields.io/badge/🔑_Secret_Leak-DETECTED-red)

### 🔒 Security Deep Scan
| # | Severity | Issue | OWASP | CWE |
|---|----------|-------|-------|-----|
| 1 | 🔴 CRITICAL | SQL Injection in auth.py:42 | A1 | CWE-89 |
| 2 | 🟠 HIGH | Missing CSRF token | A5 | CWE-352 |
```

---

## SLAYT 7: AI Slop Detection

### Problem: AI-Generated Düşük Kalite Kod

Copilot, ChatGPT ve diğer AI araçlarıyla üretilen kodun kalitesi kontrolsüz bırakıldığında "AI Slop" oluşur. Bu kod teknik olarak çalışır ama bakım maliyetini artırır.

### Tespit Edilen Pattern'ler

| Pattern | Örnek | Neden Sorunlu |
|---------|-------|---------------|
| **Gereksiz Yorumlar** | `// Initialize the variable` | Kodu tekrar eden, bilgi vermeyen yorumlar |
| **Generic İsimler** | `data`, `result`, `temp`, `item`, `obj` | Anlamsız, bağlam vermeyen değişken isimleri |
| **Boilerplate Bloat** | Framework'ün zaten yaptığı null check'ler | Gereksiz kod şişkinliği |
| **Copy-Paste** | Minimal farklı tekrar eden bloklar | Refactor edilmemiş, DRY ihlali |
| **Catch-All Exception** | `except Exception` | Spesifik hata yönetimi yok |
| **Hallucinated API** | Var olmayan method/class kullanımı | AI'ın uydurduğu API çağrıları |
| **TODO/FIXME Scaffold** | `// TODO: implement this` | Tamamlanmamış AI iskelet kodu |
| **Tutarsız Pattern** | Aynı dosyada callback + async/await | Stil karışıklığı |

### Severity Kısıtlaması

```
AI Slop issues → Maximum severity: MEDIUM
```

**AI Slop sorunları asla merge'ü engellemez.** Bunlar bilgilendirme amaçlı kalite uyarılarıdır, critical/high olarak sınıflandırılmaz.

### Güvenlik Mekanizması

AI, bir ai_slop issue'suna yanlışlıkla yüksek severity atarsa, post-processing'de otomatik cap uygulanır:

```python
if issue.get("category") == "ai_slop":
    if issue["severity"] in ("critical", "high"):
        issue["severity"] = "medium"  # Otomatik düşür
```

### PR Comment'te Görünüm

```markdown
![AI Slop](https://img.shields.io/badge/🤖_AI_Slop-3_found-orange)

### 🤖 AI Slop Detected
| # | Issue | File | Line |
|---|-------|------|------|
| 1 | Obvious redundant comment | auth.py | 15 |
| 2 | Generic variable name `data` | utils.py | 42 |
| 3 | Catch-all exception handler | api.py | 78 |
```

### Veri Modeli

```python
class ReviewResult(BaseModel):
    # ... mevcut alanlar ...
    ai_slop_detected: bool   # True/False
    ai_slop_count: int        # Bulunan AI slop sayısı
```

---

## SLAYT 8: Live Dashboard — React UI

### Real-Time Review Monitoring

Sunucu, her review sürecini adım adım live streaming ile takip edebilen bir React dashboard sunar.

### Teknoloji Stack

| Katman | Teknoloji | Amaç |
|--------|-----------|------|
| Frontend | React + TypeScript | Component-based UI |
| Bundler | Vite | Hızlı HMR, dev server |
| Routing | React Router | SPA navigasyon |
| Styling | Pure CSS (custom design system) | Lightweight, framework-free |
| API | REST + Polling | Backend ile iletişim |

### Sayfa Yapısı

| Sayfa | URL | İçerik |
|-------|-----|--------|
| **PR Runs** | `/ui/logs` | Aktif ve tamamlanan run'ların kartları, stat özet |
| **Run Detail** | `/ui/logs/:runId` | Timeline görünümünde adım adım review süreci |
| **Analytics** | `/ui/analytics` | Aggrege review metrikleri, grafikler, tablolar |
| **Settings** | `/ui/config` | Template seçici, AI provider, focus areas, polling |

### Dashboard Özellikleri

**PR Runs Sayfası:**
- Stat kartları: Active, Completed, Errors, Total
- Card-based grid layout — her run'ın PR numarası, başlığı, score'u, issue sayısı
- Status badge: Running (yeşil), Done (mavi), Error (kırmızı)
- Configurable polling interval

**Run Detail Sayfası:**
- Timeline view: Her review adımı (webhook → diff → AI → comment → status)
- Renk kodlu durum: running (mavi border), success (yeşil), error (kırmızı)
- Live event streaming

### Mimari

```
Browser (React)                    Backend (FastAPI)
──────────────                    ──────────────────
                                  ┌──────────────┐
GET /api/logs/runs  ──────────▶  │ LiveLogStore │
  (polling 3s)      ◀──────────  │ (in-memory)  │
                                  │ deque-based  │
GET /api/logs/runs/:id/events    │ thread-safe  │
  (cursor-based)    ──────────▶  └──────────────┘
                     ◀──────────

GET /api/config     ──────────▶  config.yaml +
PUT /api/config     ──────────▶  config.overrides.yaml
```

### Ortak Layout — AppShell

Tüm sayfalar `AppShell` component'i ile sarmalanır:
- Sticky top navigation bar
- "MCP Code Review" branding (gradient)
- Active sayfa vurgusu
- Responsive tasarım

---

## SLAYT 9: Review Analytics & Metrics

### Veri Odaklı Review İzleme

Her review tamamlandığında sonuçlar `AnalyticsStore`'a kaydedilir. Dashboard üzerinden aggrege metrikler görüntülenir.

### Overview Metrikleri

| Metrik | Açıklama |
|--------|----------|
| **Total Reviews** | Toplam yapılan review sayısı |
| **Avg Score** | Ortalama kod kalite puanı (0-10) |
| **Avg Security Score** | Ortalama güvenlik puanı (0-10) |
| **Total Issues** | Toplam tespit edilen sorun sayısı |
| **Critical Count** | Critical seviyede sorun sayısı |
| **Security Issues** | Güvenlik sorunları toplamı |
| **AI Slop Count** | Tespit edilen AI slop sayısı |
| **Blocked Merges** | Merge engellenen PR sayısı |
| **Secret Leaks** | Tespit edilen secret leak sayısı |

### Analiz Modülleri

**1. Score Trend**
- PR bazında quality ve security score grafiği
- Zaman içindeki iyileşme/kötüleşme trendi

**2. Security Breakdown**
- OWASP kategori dağılımı (bar chart)
- Threat type dağılımı
- Ortalama security score
- Toplam secret leak sayısı

**3. Top Issue Categories**
- En sık karşılaşılan sorun kategorileri
- Horizontal bar chart ile görselleştirme

**4. Author Stats**
- Geliştirici bazında review sayısı, ortalama score, issue sayısı, bloklanma
- Tablo formatında

### API Endpoints

| Endpoint | Dönen Veri |
|----------|-----------|
| `GET /api/analytics/overview` | Aggrege özet metrikler |
| `GET /api/analytics/trend?limit=50` | Son N review'ın score trendi |
| `GET /api/analytics/top-issues?limit=10` | En sık sorun kategorileri |
| `GET /api/analytics/security` | OWASP dağılımı, threat types, secret leaks |
| `GET /api/analytics/authors?limit=20` | Geliştirici bazlı istatistikler |
| `GET /api/analytics/recent?limit=20` | Son review'ların listesi |

### Veri Akışı

```
Webhook → AI Review → ReviewResult
                          │
                          ├──▶ Platform'a yorum gönder
                          │
                          └──▶ analytics.record_review(result, pr_id, repo, author, platform)
                                    │
                                    ▼
                              AnalyticsStore (in-memory, thread-safe)
                                    │
                                    ▼
                              React Dashboard (polling)
```

---

## SLAYT 10: Settings & Template Picker (UI)

### Runtime Konfigürasyon Yönetimi

Settings sayfası üzerinden tüm review parametreleri runtime'da değiştirilebilir. Sunucu yeniden başlatmaya gerek yoktur.

### Template Seçici

UI üzerinde 3 template arasında radio button ile seçim yapılır:

| Template | Hedef Kitle | Açıklama |
|----------|------------|----------|
| **Default (Compact)** | Geliştiriciler | Clean summary, badge'ler, issue table, collapsible details |
| **Detailed** | QA / Tüm ekip | Code-level feedback, inline annotations, full context |
| **Executive (Visual)** | Tech Lead / Manager | Badge-heavy, visual overview, risk analizi |

**Seçim akışı:**
```
UI Radio Select → PUT /api/config { review: { template: "executive" } }
    → server.py: update_runtime_config()
        → CommentService yeniden oluşturulur (hot-swap)
        → config.overrides.yaml'a persist edilir
    → Sonraki webhook'ta yeni template kullanılır
```

### Diğer Ayarlar

**AI Provider:**
- Provider seçimi: OpenAI / Anthropic / Groq
- Model seçimi: Provider'a göre filtrelenen dropdown

**Review Behavior:**
- Comment Strategy: Summary / Inline / Both
- Focus Areas: Virgülle ayrılmış odak alanları

**UI Preferences:**
- Poll Interval: Dashboard'un backend'i ne sıklıkla sorguladığı
- Max Events Per Poll: Her sorguda alınacak maksimum event sayısı

### Backend Mekanizması

```yaml
# config.yaml (base)
review:
  template:
    name: "executive"

# config.overrides.yaml (UI'dan kaydedilen)
review:
  template:
    name: "default"
  comment_strategy: "both"
ai:
  provider: "groq"
  model: "llama-3.3-70b-versatile"
```

**Deep merge:** `config.yaml` + `config.overrides.yaml` = final config.  
Override dosyası UI'dan her kayıtta güncellenir.

---

## SLAYT 11: Desteklenen Platformlar

### 4 Büyük Platform, Tek Webhook Endpoint

| Platform | Adapter | Auth Yöntemi | Durum |
|----------|---------|-------------|-------|
| **GitHub** | `GitHubAdapter` | Bearer Token | ✅ Aktif |
| **GitLab** | `GitLabAdapter` | Private Token | ✅ Aktif |
| **Bitbucket** | `BitbucketAdapter` | App Password (Basic Auth) | ✅ Aktif |
| **Azure DevOps** | `AzureAdapter` | PAT (Personal Access Token) | ✅ Aktif |

### Platform Tespiti — Otomatik Header Algılama

```python
PLATFORM_HEADERS = {
    'x-github-event':    Platform.GITHUB,
    'x-gitlab-event':    Platform.GITLAB,
    'x-event-key':       Platform.BITBUCKET,
    'x-vss-activityid':  Platform.AZURE,
}
```

### Her Platform İçin Tam Özellik Seti

| Özellik | GitHub | GitLab | Bitbucket | Azure |
|---------|--------|--------|-----------|-------|
| Diff çekme | ✅ | ✅ | ✅ | ✅ |
| Summary yorum | ✅ | ✅ | ✅ | ✅ |
| Inline yorum | ✅ | ✅ | ✅ | ✅ |
| Status güncelleme | ✅ | ✅ | ✅ | ✅ |
| Merge bloklama | ✅ | ✅ | ✅ | ✅ |

### Adapter Mimarisi

```python
class BasePlatformAdapter(ABC):
    async def fetch_diff(self, pr_data: UnifiedPRData) -> str: ...
    async def post_summary_comment(self, pr_data: UnifiedPRData, comment: str): ...
    async def post_inline_comments(self, pr_data: UnifiedPRData, comments: list): ...
    async def update_status(self, pr_data: UnifiedPRData, state: str, description: str): ...
```

Yeni platform eklemek = Sadece yeni bir adapter yazmak. Mevcut iş mantığı hiç değişmez.

---

## SLAYT 12: AI Provider Sistemi

### 3 AI Provider — Modüler ve Değiştirilebilir

| Provider | Model(ler) | Hız | Maliyet | Öne Çıkan |
|----------|-----------|-----|---------|-----------|
| **Groq** | Llama 3.3 70B, Mixtral 8x7B | ⚡ Çok Hızlı | 💰 Ücretsiz/Düşük | Günlük review |
| **OpenAI** | GPT-4o, GPT-4o-mini, GPT-4 Turbo | 🔄 Orta | 💰💰 Orta | Karmaşık analiz |
| **Anthropic** | Claude 3.5 Sonnet | 🔄 Orta | 💰💰💰 Orta-Yüksek | Güvenlik analizi |

### Provider değiştirmek

**Config ile:**
```yaml
ai:
  provider: "groq"
  model: "llama-3.3-70b-versatile"
```

**UI Settings ile:**
- Dropdown'dan provider ve model seçilip "Save Settings" tıklanır
- Backend anında güncellenir, restart gerekmez

**MCP Tool ile:**
```json
{
  "code": "def login(user, pwd): ...",
  "provider": "openai",
  "model": "gpt-4o"
}
```

---

## SLAYT 13: Dil Tespiti ve Rule Sistemi

### 25+ Programlama Dili Otomatik Tespiti

| Dil Ailesi | Desteklenen Diller |
|------------|-------------------|
| **.NET** | C# |
| **JVM** | Java, Kotlin, Scala |
| **Web** | JavaScript, TypeScript |
| **Scripting** | Python, Ruby, PHP |
| **Sistem** | Go, Rust, C, C++ |
| **Mobil** | Swift, Dart |
| **Data** | SQL, YAML, JSON, XML |

### Rule Yapısı (19 dosya)

```
rules/
├── compilation.md           # Genel compilation kuralları
├── security.md              # Genel güvenlik
├── performance.md           # Genel performans
├── best-practices.md        # Genel best practices
├── csharp-compilation.md    # C# özel
├── csharp-security.md
├── python-compilation.md    # Python özel
├── python-security.md
├── go-compilation.md        # Go özel
└── ... (19+ dosya)
```

### AI ile Otomatik Rule Üretimi

Yeni bir dil için rule bulunmadığında, `RuleGenerator` AI ile otomatik oluşturur:

```
PR gelir → Dil tespiti: "Rust" → rust-security.md mevcut mu?
  └── HAYIR → RuleGenerator:
        1. Genel security.md şablonunu al
        2. Rust diline özel AI ile revize et
        3. rust-security.md kaydet
        4. Sonraki review'da hazır
```

---

## SLAYT 14: Short-Circuit Review

### Compilation Hatası = Diğer Kontroller Durur

Sistem compilation/syntax hatası bulduğunda diğer kategorileri kontrol etmeyi durdurur. **Derlenmeyen kod için güvenlik analizi anlamsızdır.**

**İki katmanlı uygulama:**

1. **AI Prompt Seviyesi** — AI'a "compilation hatası bulursan dur" talimatı
2. **Post-Processing** — Programatik filtre ile garanti

```python
compilation_issues = [i for i in issues if i.severity == "critical" and i.category in ("compilation", "syntax")]
if compilation_issues:
    normalized_issues = compilation_issues  # Diğer her şeyi at
```

| Senaryo | Davranış |
|---------|----------|
| Compilation hatası var | Sadece compilation raporlanır, merge engellenir |
| Compilation temiz | Security + AI Slop + diğer tüm kontroller çalışır |

---

## SLAYT 15: Template Sistemi

### 4 Farklı Template

| Template | Hedef | Özellik |
|----------|-------|---------|
| **Default** | Geliştiriciler | Kompakt, badge'li, collapsible details |
| **Detailed** | QA / Tüm ekip | Dosya bazlı, kod snippet'li, severity matrix |
| **Executive** | Tech Lead / Manager | Badge'ler, risk tablosu, tech debt tahmini |
| **Custom** | İsteğe bağlı | `custom_templates/*.md` ile tam özelleştirme |

### v2.0 Eklentileri (Tüm Template'lerde)

Her template artık şu ek bölümleri içerir:

**AI Slop Badge:**
```markdown
![AI Slop](https://img.shields.io/badge/🤖_AI_Slop-3_found-orange)
```

**Security Score Badge:**
```markdown
![Security](https://img.shields.io/badge/Security-8%2F10-green)
```

**Secret Leak Badge (varsa):**
```markdown
![Secret Leak](https://img.shields.io/badge/🔑_Secret_Leak-DETECTED-red)
```

**AI Slop Detay Bölümü:**
```markdown
### 🤖 AI Slop Detected
| # | Issue | File | Line |
|---|-------|------|------|
| 1 | Obvious redundant comment | auth.py | 15 |
```

**Security Deep Scan Bölümü:**
```markdown
### 🔒 Security Deep Scan
| # | Severity | Issue | OWASP | CWE | Threat |
|---|----------|-------|-------|-----|--------|
| 1 | 🔴 CRITICAL | SQL Injection | A1 | CWE-89 | injection |
```

### Template Seçim Yöntemleri

1. **config.yaml** — `review.template.name: "executive"`
2. **UI Settings** — Radio button ile seçip "Save"
3. **API** — `POST /templates/switch { "name": "detailed" }`
4. **PUT /api/config** — `{ "review": { "template": "executive" } }`

---

## SLAYT 16: MCP Protokolü ve IDE Entegrasyonu

### MCP Tools

| Tool | Açıklama | Kullanım |
|------|----------|----------|
| `review_code` | Kod parçacığını AI ile incele | IDE içinden tetikleme |
| `analyze_diff` | Git diff istatistikleri | Diff analizi |
| `security_scan` | Güvenlik odaklı tarama | Sadece güvenlik |

### SSE Endpoint

```
GET /mcp/sse → Real-time MCP bağlantısı
```

### Desteklenen Client'lar

| Client | Durum |
|--------|-------|
| Claude Desktop | ✅ |
| Cursor IDE | ✅ |
| VS Code (Copilot) | ✅ |
| Windsurf | ✅ |

---

## SLAYT 17: API Endpoint Referansı — Tam Liste

### Core

| Method | Endpoint | Açıklama |
|--------|----------|----------|
| `GET` | `/` | Health check |
| `POST` | `/webhook` | Universal webhook |
| `GET` | `/mcp/sse` | MCP SSE endpoint |

### Config & Templates

| Method | Endpoint | Açıklama |
|--------|----------|----------|
| `GET` | `/api/config` | Editable config (template dahil) |
| `PUT` | `/api/config` | Update config (persist edilir) |
| `GET` | `/templates` | Template listesi + aktif |
| `POST` | `/templates/switch` | Runtime template değiştirme |

### Rules

| Method | Endpoint | Açıklama |
|--------|----------|----------|
| `GET` | `/rules` | Rule dosyalarını listele |
| `GET` | `/rules/resolve?focus=...&language=...` | Rule çözümle |
| `GET` | `/rules/{filename}` | Rule içeriği |

### Live Logs

| Method | Endpoint | Açıklama |
|--------|----------|----------|
| `GET` | `/api/logs/config` | Logs config |
| `GET` | `/api/logs/active` | Aktif run'lar |
| `GET` | `/api/logs/runs` | Tüm run'lar |
| `GET` | `/api/logs/runs/{run_id}/events` | Run event'leri (cursor-based) |

### Analytics

| Method | Endpoint | Açıklama |
|--------|----------|----------|
| `GET` | `/api/analytics/overview` | Aggrege özet |
| `GET` | `/api/analytics/trend` | Score trendi |
| `GET` | `/api/analytics/top-issues` | Top sorun kategorileri |
| `GET` | `/api/analytics/security` | OWASP dağılımı |
| `GET` | `/api/analytics/authors` | Author istatistikleri |
| `GET` | `/api/analytics/recent` | Son review'lar |

### UI (SPA)

| Method | Endpoint | Açıklama |
|--------|----------|----------|
| `GET` | `/ui` | React SPA index |
| `GET` | `/ui/{path}` | SPA routing |

**Toplam: 20+ API endpoint**

---

## SLAYT 18: Data Modeli

### Temel Modeller (Pydantic v2)

```python
class UnifiedPRData(BaseModel):
    platform: Platform           # GITHUB | GITLAB | BITBUCKET | AZURE
    pr_id: str
    repo_full_name: str
    source_branch: str
    target_branch: str
    title: str
    author: str
    diff: str
    files_changed: list[str]

class ReviewIssue(BaseModel):
    severity: IssueSeverity      # CRITICAL | HIGH | MEDIUM | LOW | INFO
    title: str
    description: str
    file_path: str | None
    line_number: int | None
    code_snippet: str | None
    suggestion: str | None
    category: str                # security, compilation, ai_slop, ...
    owasp_id: str | None         # NEW: "A1" ... "A10"
    cwe_id: str | None           # NEW: "CWE-89"
    threat_type: str | None      # NEW: "injection", "secret_leak", ...

class ReviewResult(BaseModel):
    summary: str
    score: int                   # 0-10
    issues: list[ReviewIssue]
    block_merge: bool
    # Auto-calculated fields
    total_issues: int
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int
    info_count: int
    # NEW: AI Slop
    ai_slop_detected: bool
    ai_slop_count: int
    # NEW: Security Deep Scan
    security_score: int          # 0-10
    security_issues_count: int
    secret_leak_detected: bool
    owasp_categories_hit: list[str]
```

---

## SLAYT 19: Proje Dizin Yapısı

```
mcp-server/
├── server.py                      # Ana FastAPI server (20+ endpoint)
├── config.yaml                    # Merkezi konfigürasyon
├── config.overrides.yaml          # UI'dan kaydedilen override'lar
├── requirements.txt               # Python bağımlılıkları
├── .env                           # Secret'lar (Git dışı)
│
├── models/
│   └── schemas.py                 # Pydantic modeller (SecurityThreat, ReviewIssue, ...)
│
├── services/
│   ├── ai_reviewer.py             # AI review motoru + OWASP + AI Slop prompt
│   ├── ai_providers/              # Provider soyutlama katmanı
│   │   ├── base.py                #   Abstract AIProvider
│   │   ├── factory.py             #   Provider factory
│   │   ├── router.py              #   Multi-provider router
│   │   ├── openai_provider.py     #   OpenAI
│   │   ├── anthropic_provider.py  #   Anthropic
│   │   ├── groq_provider.py       #   Groq
│   │   └── mock_provider.py       #   Test mock
│   ├── comment_service.py         # Yorum formatlama
│   ├── diff_analyzer.py           # Diff parse (unidiff)
│   ├── language_detector.py       # 25+ dil tespiti
│   ├── rule_generator.py          # AI rule üretimi
│   ├── rules_service.py           # Rule dosya yönetimi
│   ├── live_log_store.py          # NEW: Real-time log streaming
│   ├── analytics_store.py         # NEW: Review metrics aggregation
│   └── ui_logs_config.py          # NEW: UI polling config parser
│
├── adapters/                      # Platform API clients
│   ├── base_adapter.py
│   ├── github_adapter.py
│   ├── gitlab_adapter.py
│   ├── bitbucket_adapter.py
│   └── azure_adapter.py
│
├── webhook/                       # Webhook handling
│   ├── handler.py
│   └── parsers/
│       ├── github_parser.py
│       ├── gitlab_parser.py
│       ├── bitbucket_parser.py
│       └── azure_parser.py
│
├── review_templates/              # PR yorum template'leri
│   ├── base.py                    #   + AI Slop & Security badge support
│   ├── default.py
│   ├── detailed.py
│   ├── executive.py
│   └── custom.py
│
├── ui/                            # NEW: React dashboard
│   ├── src/
│   │   ├── App.tsx                #   Route definitions
│   │   ├── components/
│   │   │   ├── AppShell.tsx       #   Global nav layout
│   │   │   └── ActiveRunRow.tsx
│   │   ├── routes/
│   │   │   ├── LogsDashboardPage.tsx   # PR runs grid
│   │   │   ├── LogDetailPage.tsx       # Timeline view
│   │   │   ├── AnalyticsPage.tsx       # Review analytics
│   │   │   └── ConfigPage.tsx          # Settings + template picker
│   │   ├── lib/
│   │   │   ├── api.ts             #   API client functions
│   │   │   └── usePolling.ts      #   Polling hook
│   │   ├── types/logs.ts          #   TypeScript interfaces
│   │   └── styles.css             #   Design system (~400 lines)
│   ├── vite.config.ts
│   └── package.json
│
├── tools/
│   └── review_tools.py            # MCP Tools (3 tool)
│
├── rules/                         # 19 review kural dosyası (.md)
├── custom_templates/              # Kullanıcı şablonları
├── docs/                          # Dokümantasyon (9 dosya)
└── tests/                         # Test dosyaları
```

---

## SLAYT 20: CodeRabbit vs MCP Server — Karşılaştırma

| Özellik | CodeRabbit | MCP Server v2.0 |
|---------|------------|-----------------|
| **Maliyet** | $12-24/kullanıcı/ay | Self-hosted, sadece AI API |
| **Platform** | GitHub, GitLab | GitHub, GitLab, Bitbucket, Azure |
| **AI Provider** | Sabit | 3 provider, runtime değiştirilebilir |
| **OWASP Security Scan** | Yok | ✅ OWASP Top 10 + Secret Leak |
| **AI Slop Detection** | Yok | ✅ 8 pattern tespiti |
| **Review Analytics** | Temel | ✅ Full dashboard + metriks |
| **Live Dashboard** | Yok | ✅ Real-time streaming UI |
| **Template Sistemi** | Tek format | 4 template + custom |
| **Rule Yönetimi** | Sınırlı | Markdown + AI auto-generation |
| **IDE Entegrasyonu** | Yok | MCP (Claude, Cursor, VS Code) |
| **Veri Gizliliği** | 3. parti sunucu | Self-hosted |
| **Runtime Config** | Yok | UI + API ile hot-swap |
| **Short-Circuit** | Yok | ✅ Compilation → dur |
| **Open Source** | Hayır | Evet |

### Maliyet (10 kişilik ekip, yıllık)

| | CodeRabbit | MCP Server |
|---|------------|-----------|
| **Yıllık** | **$2,880** | **~$300-840** |
| **Tasarruf** | — | **%70-90** |

---

## SLAYT 21: Canlı Demo Senaryosu

### Server Konsol Çıktısı

```
🔔 WEBHOOK RECEIVED
════════════════════════════════════════════════════
📦 Platform: GITHUB
🔗 PR #42: Add user authentication module
👤 Author: developer
🌿 feature/auth → main
────────────────────────────────────────────────────

📥 Step 1/5: Fetching diff from platform...
✅ Diff fetched successfully (4,120 bytes)

🔍 Step 2/5: Analyzing diff...
✅ Found 4 changed file(s):
   📄 src/auth/login.py
   📄 src/auth/middleware.py
   📄 src/config.py
   📄 tests/test_auth.py

🤖 Step 3/5: Starting AI code review...
   Provider: GROQ
   Model: llama-3.3-70b-versatile
   Focus: compilation, security, performance, bugs, code_quality, best_practices

✅ AI Review completed!
   Score: 5/10
   Issues: 6 total
   🔴 Critical: 1 (SQL Injection — A1)
   🟠 High: 1 (Missing CSRF — A5)
   🟡 Medium: 2 (AI Slop: redundant comments)
   🔵 Low: 2

💬 Step 4/5: Posting review comments...
   Strategy: summary
   📝 Posting summary comment...
   ✅ Summary comment posted

📊 Step 5/5: Updating PR status...
   ❌ Status: FAILURE (Critical issues → merge blocked)

🎉 REVIEW COMPLETED
   Score: 5/10 | Security: 4/10 | AI Slop: 2 found
════════════════════════════════════════════════════
```

### PR'da Görünen Yorum (Executive Template)

```markdown
## 📊 MCP AI Code Review

![Quality](https://img.shields.io/badge/Quality-5%2F10-red)
![Security](https://img.shields.io/badge/Security-4%2F10-red)
![AI Slop](https://img.shields.io/badge/🤖_AI_Slop-2_found-orange)
![Secret Leak](https://img.shields.io/badge/🔑_Secret_Leak-NONE-green)
![Merge](https://img.shields.io/badge/Merge-BLOCKED-red)

### 🔒 Security Deep Scan
| # | Severity | Issue | OWASP | CWE |
|---|----------|-------|-------|-----|
| 1 | 🔴 CRITICAL | SQL Injection in login.py:42 | A1 | CWE-89 |
| 2 | 🟠 HIGH | Missing CSRF protection | A5 | CWE-352 |

### 🤖 AI Slop Detected
| # | Issue | File | Line |
|---|-------|------|------|
| 1 | Redundant comment: "// Initialize variable" | config.py | 12 |
| 2 | Generic variable name: `data` | middleware.py | 35 |

> ❌ **MERGE BLOCKED** — 1 critical issue(s) found.
```

---

## SLAYT 22: Projenin Sayısal Büyüklüğü

```
📊 4   Platform Desteği       → GitHub, GitLab, Bitbucket, Azure DevOps
🤖 3   AI Provider            → OpenAI, Anthropic, Groq
🌐 25+ Programlama Dili       → Otomatik tespit + dile özel kurallar
📝 19  Rule Dosyası           → AI-generated, Markdown tabanlı
📋 4   PR Template            → Default, Detailed, Executive, Custom
🔧 3   MCP Tool               → review_code, analyze_diff, security_scan
🔍 7   Focus Area             → compilation, security, performance, bugs, ...
⚡ 5   Severity Level         → CRITICAL → INFO
🔒 10  OWASP Kategori         → A1-A10 tam kapsam
🤖 8   AI Slop Pattern        → Redundant comment, generic name, boilerplate, ...
📈 6   Analytics Endpoint     → overview, trend, top-issues, security, authors, recent
🖥️ 4   UI Sayfası             → PR Runs, Run Detail, Analytics, Settings
🌐 20+ API Endpoint           → REST API tam coverage
📦 5   Deployment Yöntemi     → Docker, Podman, Compose, Railway, Manuel
📄 4   CI/CD Pipeline Örneği  → GitHub Actions, GitLab CI, Bitbucket Pipes, Azure
🔐 7   Güvenlik Katmanı       → İmza doğrulama → HTTPS → Self-hosted
📁 40+ Kaynak Dosyası         → Python + TypeScript modüler mimari
```

---

## SLAYT 23: Değer Önerisi Özeti

| Boyut | Etki |
|-------|------|
| **Maliyet** | CodeRabbit'e göre %70-90 tasarruf |
| **Zaman** | Manuel review süresi %60-80 azalır |
| **Güvenlik** | OWASP Top 10 + Secret Leak → proaktif güvenlik |
| **AI Kalitesi** | AI Slop Detection → düşük kalite AI kodu tespit |
| **Görünürlük** | Live Dashboard + Analytics → veri odaklı kararlar |
| **Esneklik** | 4 platform, 3 AI, 25+ dil, 4 template, UI config |
| **Gizlilik** | Self-hosted, kod asla 3. parti sunuculara gitmez |
| **Ölçeklenebilirlik** | Container-based, yatay ölçekleme |
| **Sürdürülebilirlik** | AI ile otomatik kural üretimi, config-driven |

---

## SLAYT 24: Roadmap — Gelecek Planları

### Kısa Vade (Q2 2026)

| # | Feature | Açıklama |
|---|---------|----------|
| 1 | **Kategori Bazlı Model Seçimi** | Security → Claude, compilation → GPT-4 |
| 2 | **Persistent Analytics** | SQLite/PostgreSQL ile kalıcı metrik storage |
| 3 | **Notification Hub** | Slack, Teams, Email entegrasyonu |
| 4 | **Public REST API** | Webhook kullanmadan direkt review API |

### Orta Vade (Q3-Q4 2026)

| # | Feature | Açıklama |
|---|---------|----------|
| 5 | **Çoklu IDE Plugin** | VS Code, IntelliJ, Visual Studio extensions |
| 6 | **Team-based Rules** | Takım bazlı rule set'leri, RBAC |
| 7 | **Akıllı Caching** | Benzer pattern cache, incremental review |
| 8 | **Complexity Scoring** | Cyclomatic + cognitive complexity |

### Uzun Vade (2027)

| # | Feature | Açıklama |
|---|---------|----------|
| 9 | **Learning from Feedback** | 👍/👎 ile false positive azaltma |
| 10 | **Multi-tenant SaaS** | Çoklu org desteği, self-service |

---

## SLAYT 25: Soru-Cevap

### Sık Sorulan Sorular

**S: AI Slop nedir ve neden önemli?**
C: AI araçlarıyla (Copilot, ChatGPT) üretilen düşük kaliteli kod pattern'leridir. Gereksiz yorumlar, generic isimler, boilerplate gibi. Merge engellemez ama teknik borç birikimini önler.

**S: Security Deep Scan mevcut SAST araçlarının yerini alır mı?**
C: Tam olarak değil. AI-based tarama, geleneksel SAST'tan farklı olarak bağlamı anlayabilir. İkisi birlikte kullanılabilir. MCP Server, OWASP Top 10 odaklı pattern tespiti yapar.

**S: Analytics verileri nerede saklanır?**
C: Şu an in-memory (sunucu restart'ta sıfırlanır). Roadmap'te persistent storage (SQLite/PostgreSQL) planlanmaktadır.

**S: Dashboard'a kimler erişebilir?**
C: Şu an auth yok, network seviyesinde kontrol edilir (VPN/firewall). İleride RBAC planlanmaktadır.

**S: Review ne kadar sürer?**
C: Ortalama 10-30 saniye. Groq ile genellikle 5-15 saniye.

**S: Template nasıl değiştirilir?**
C: 3 yol: config.yaml, UI Settings sayfası, veya API endpoint. Hepsi runtime'da çalışır.

**S: Yeni programlama dili desteği nasıl eklenir?**
C: Otomatik. İlk kez o dilde PR geldiğinde RuleGenerator AI ile kuralları oluşturur.

**S: Birden fazla repo için tek server yeterli mi?**
C: Evet. Webhook URL'i ayarlanan tüm repo'lar aynı server'ı kullanabilir. Platform farkı yok.

---

**Hazırlayan:** Mennano Development Team  
**Versiyon:** 2.0.0  
**Son Güncelleme:** Mart 2026  
**İletişim:** [Mennano]
