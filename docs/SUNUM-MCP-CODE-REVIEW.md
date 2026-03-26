# MCP AI Code Review Server — Technical Presentation

> **Version:** 2.0.0 | **Date:** March 2026 | **Format:** Canva Docs → Presentation

---

## Slide 1 — Cover

**MCP AI Code Review Server**

AI-Powered, Platform-Agnostic Code Review System

A self-hosted, AI-powered code review server that automatically analyzes every Pull Request across GitHub, GitLab, Bitbucket and Azure DevOps. It combines multi-provider AI intelligence with OWASP-based security scanning, AI-generated code quality detection, and a live analytics dashboard — replacing expensive SaaS tools while keeping your source code entirely within your infrastructure.

- 4 Platforms — GitHub · GitLab · Bitbucket · Azure DevOps — Single webhook, auto-detected
- 3 AI Providers — GPT-4 · Claude 3.5 · Llama 3.3 — Hot-swappable at runtime
- OWASP Top 10 Security Deep Scan — Injection, auth, XSS, secret leaks scored 0-10
- AI Slop Detection — Catches low-quality AI-generated code patterns
- Live Dashboard & Analytics — Real-time review tracking with metrics & trends
- MCP IDE Integration — Review code directly from Cursor, VS Code & more

**Notlar:**

Herkese merhaba, ben Sevim. Bugün sizlerle hem bir sorunu hem de o soruna karşı geliştirdiğimiz çözümü paylaşacağım.

Şöyle bir düşünün: sabah masanıza oturuyorsunuz, kahvenizi alıyorsunuz ve bir de bakıyorsunuz ki 5 tane PR review bekliyor. Biri C#, biri Python, biri de daha önce hiç bakmadığınız bir mikroservis. Saatlerinizi harcıyorsunuz — ama ne kadar dikkatli olursanız olun, insan gözü bir yerde kaçırıyor. Bir SQL injection gözden kayıyor, Copilot'un ürettiği ama kimsenin kontrol etmediği "slop" kod sessizce birikiyor, güvenlik açıkları ancak production'da patlayınca fark ediliyor.

Bir gün ekip olarak şunu sorduk kendimize: "Biz neden bu işi yapay zekaya yaptırmıyoruz?" Piyasaya baktık — CodeRabbit var, Codacy var, SonarCloud var. Ama ya çok pahalılar, ya sadece iki platformu destekliyorlar, ya da en kritik nokta: kodunuz 3. parti sunuculara gidiyor. Finans, savunma, sağlık gibi sektörlerde bu kabul edilebilir değil.

İşte tam bu noktada dedik ki: "Biz bunu kendimiz yapalım. Hem esnek olsun, hem açık kaynak olsun, hem de kodumuz kendi altyapımızdan çıkmasın." MCP AI Code Review Server böyle doğdu.

Peki ne yapıyor bu sistem? Bir geliştirici herhangi bir platformda — ister GitHub olsun, ister GitLab, Bitbucket ya da Azure DevOps — bir Pull Request açtığında, sistem otomatik olarak o PR'ı yapay zeka ile inceler, OWASP Top 10 tabanlı güvenlik taraması yapar, AI ile yazılmış düşük kaliteli kodu tespit eder ve sonucu doğrudan PR'a yorum olarak yazar. Tüm bunlar saniyeler içinde, hiçbir manuel müdahale olmadan gerçekleşir. Üstelik tamamen self-hosted — kodunuz asla şirket dışına çıkmıyor.

Bugünkü sunumda bu sistemi sıfırdan nasıl tasarladığımızı, hangi mimari kararları neden aldığımızı ve pratikte ne fark yarattığını birlikte göreceğiz. Haydi başlayalım.

---

## Slide 2 — Why This Project?

Code review is one of the most critical stages of software development, yet the current landscape is plagued with inefficiencies. Developers spend hours on manual reviews, security issues slip through human oversight, and existing SaaS solutions are expensive, limited in platform support, and raise data privacy concerns. This project was built to solve all of these problems in a single self-hosted solution.

| Problem | Impact |
|---------|--------|
| Manual review is time-consuming | 2-4 hours/day productivity loss |
| Human eyes miss bugs | Security vulnerabilities slip through |
| Different tools per platform | Tool cost + training overhead |
| Inconsistent review quality | Standards vary by reviewer |
| AI-generated code quality dropping | Technical debt accumulation |
| Security scanning requires separate tools | SAST/DAST/secret scan separate setup |
| Existing solutions are expensive & limited | CodeRabbit: $12-24/person/month, vendor lock-in |
| Data privacy concerns | Code sent to 3rd party servers |

**Notlar:**

Şimdi bu projeyi neden yaptığımızı konuşalım. Hepimiz biliyoruz ki kod inceleme süreci yazılım geliştirmenin en kritik aşamalarından biri. Ama mevcut durumda ciddi sorunlar var.

Birincisi, zaman. Bir geliştirici günde ortalama 2 ila 4 saat sadece başkalarının kodunu incelemeye harcıyor. Bu ciddi bir üretkenlik kaybı. İkincisi, insan gözü her şeyi yakalayamıyor — özellikle güvenlik açıkları, ince compilation hataları ve performans sorunları gözden kaçabiliyor.

Bir de artık herkes AI kullanıyor: Copilot, ChatGPT ile kod üretiyor. Ama bu kodun kalitesi kontrol edilmiyor. "AI Slop" dediğimiz gereksiz yorumlar, generic değişken isimleri, copy-paste bloklar birikiyor.

Piyasadaki çözümlere bakarsanız, CodeRabbit gibi araçlar var ama kişi başı 12-24 dolar aylık maliyet, sadece 2 platformu destekliyor, özelleştirme sınırlı ve en önemlisi kodunuz 3. parti sunuculara gidiyor. Biz bütün bu sorunları tek bir self-hosted çözümle ortadan kaldırmak istedik.

---

## Slide 3 — Why Python?

Python is the lingua franca of the AI ecosystem. All three major AI providers (OpenAI, Anthropic, Groq) offer Python-first SDKs, and mature libraries exist for every supported platform. Combined with FastAPI's rapid development cycle and Pydantic v2's type safety, Python was the most pragmatic choice for an AI-first project.

| Criteria | Python | Node.js | C#/.NET | Go |
|----------|:------:|:-------:|:-------:|:--:|
| AI SDK Maturity | ★★★★★ | ★★★ | ★★ | ★★ |
| Platform API Libraries | ★★★★★ | ★★★ | ★★★ | ★★ |
| MCP SDK Support | ★★★★★ | ★★★★ | ★★ | ★ |
| Development Speed | ★★★★★ | ★★★★ | ★★★ | ★★★ |

**Notlar:**

"Neden Python?" diye sorulabilir — özellikle ekip olarak .NET ağırlıklı çalışıyorsak. Cevap aslında çok net: bu bir AI-first proje ve AI dünyasının lingua franca'sı Python.

OpenAI, Anthropic, Groq — üçünün de resmi SDK'ları Python-first. Üstelik GitHub, GitLab, Bitbucket, Azure DevOps için olgun Python kütüphaneleri var: PyGithub, python-gitlab, atlassian-python-api, azure-devops. MCP protokolünün resmi SDK'sı da Python'da.

FastAPI ile dakikalar içinde production-ready API kurabiliyorsunuz. Pydantic v2 ile tip güvenliği ve otomatik validation geliyor. Async/await native destek var. Docker image'ı 150 megabyte.

Aynı işi C# ile yapmaya kalksanız, AI SDK'ları ya community-driven ya da çok yeni. Platform API kütüphaneleri ya eksik ya da sınırlı. Go'da da durum benzer. Tabloda gördüğünüz gibi Python her kriterde açık ara önde. Bu proje için en pragmatik tercih buydu.

---

## Slide 4 — Architecture Overview

The system is built around a modular, layered architecture. A single webhook endpoint receives events from any platform, routes them through an AI-powered review engine, and posts formatted results back as PR comments — all while streaming live events to an analytics dashboard.

**Components:**

- Webhook Handler → Platform Detection (Auto) — Receives incoming webhooks and auto-identifies the source platform from HTTP headers.
- Language Detector (25+ languages) → Rules Helper (Markdown) — Detects the dominant language in the diff and loads language-specific review rules.
- AI Review Engine: Provider Router (Groq/OpenAI/Anthropic) — Core engine that routes review requests to the configured AI provider.
- Review Modules: Code Quality, Security Deep Scan, AI Slop, Compilation — Four parallel analysis modules run in a single AI pass.
- Comment Service → Template Engine (Default/Detailed/Executive) — Formats AI results into rich PR comments using the selected template.
- Platform Adapters → Comment + Status posting — Sends comments and updates PR status via platform-specific APIs.
- Live Log Store + Analytics Store — In-memory stores for real-time event streaming and aggregated review metrics.
- React UI Dashboard — A 4-page frontend for monitoring reviews, analytics, and configuration.

**Design Principles:** Platform Agnostic · Provider Agnostic · Config-Driven · Self-Hosted · Observable

**Notlar:**

Bu slaytla sistemin büyük resmini görelim. Mimari altı ana katmandan oluşuyor.

En solda Webhook Handler var. Herhangi bir platformdan gelen webhook isteğini alıyor ve HTTP header'larına bakarak platformu otomatik tespit ediyor. GitHub mu, GitLab mu, Bitbucket mu — bunu sizin belirtmenize gerek yok, sistem kendisi anlıyor.

Ortada AI Review Engine var — bu sistemin kalbi. Üç farklı AI provider'ı destekliyor: Groq, OpenAI ve Anthropic. Hangisini kullanacağınız config'den veya UI'dan seçilebilir. Review engine tek seferde dört modülü çalıştırıyor: standart kod kalitesi kontrolü, OWASP tabanlı security deep scan, AI slop detection ve compilation kontrolü.

Sağda Comment Service var. AI'dan gelen sonuçları seçili template ile formatlayıp platforma yorum olarak gönderiyor. Altta da yeni eklediğimiz bileşenler var: Live Log Store ile review sürecini real-time izleyebiliyorsunuz, Analytics Store ile de aggrege metrikler topluyorsunuz.

Temel tasarım ilkelerimiz şunlar: platform agnostik, provider agnostik, config-driven yani her şey YAML'dan yönetiliyor, self-hosted ve observable yani canlı izlenebilir.

---

## Slide 5 — Review Flow (5 Steps)

When a Pull Request is opened, the entire review pipeline executes end-to-end in seconds with zero manual intervention. From webhook reception to merge decision, every step is automated, logged in real-time, and recorded for analytics.

1. **Webhook Received** — The platform sends a webhook; the system auto-detects the source and starts a live log session for real-time monitoring.
2. **Diff Fetched** — The platform adapter pulls the PR diff via API, detects the programming language from file extensions, and loads language-specific rules.
3. **AI Review** — The AI performs four analyses in a single pass: code quality, OWASP security scan, AI slop detection, and compilation check. If a compilation error is found, all other checks are short-circuited.
4. **Comment Posted** — Results are formatted using the selected template with badges, tables, and collapsible details, then posted as a PR comment.
5. **Status Update** — The PR status is set to success or failure. Critical issues block the merge. Review data is recorded to the analytics store.

**Notlar:**

Şimdi bir PR açıldığında uçtan uca ne oluyor, onu adım adım görelim.

Birinci adım: Platform webhook gönderiyor, sistem bunu alıyor, header'dan platformu tespit ediyor ve live log kaydını başlatıyor. Artık bu review'ı dashboard'dan canlı izleyebilirsiniz.

İkinci adım: Platform adapter'ı devreye giriyor. İlgili API'yi çağırıp PR'ın diff'ini çekiyor. Diff'teki dosya uzantılarına bakarak programlama dilini tespit ediyor — mesela .cs dosyaları varsa C#, .py varsa Python. Sonra o dile özel rule dosyalarını yüklüyor.

Üçüncü adım: Burası en kritik kısım. AI'a diff ve kurallar gönderiliyor, AI tek seferde dört farklı analiz yapıyor: standart kod kalitesi, OWASP tabanlı güvenlik taraması, AI slop detection ve compilation kontrolü. Önemli bir mekanizma var burada: eğer compilation hatası bulunursa, diğer kontroller yapılmaz. Biz buna short-circuit diyoruz. Derlenmeyen kodda güvenlik analizi yapmanın anlamı yok.

Dördüncü adım: Sonuçlar seçili template ile formatlanıyor — badge'ler, tablolar, detay bölümleri — ve PR'a yorum olarak gönderiliyor.

Beşinci adım: PR'ın status'u güncelleniyor. Critical sorun varsa failure olarak işaretleniyor ve merge otomatik engelleniyor. Son olarak review sonuçları analytics store'a kaydediliyor.

---

## Slide 6 — Security Deep Scan

Every PR is scanned against the full OWASP Top 10 framework. Unlike traditional pattern-matching tools, the AI understands context — distinguishing a string interpolation inside a SQL query from one in a log message. Each issue is tagged with an OWASP ID and CWE ID for compliance reporting.

**Full OWASP Top 10 Coverage:**

| OWASP | Category | Severity |
|-------|----------|----------|
| A1 | Broken Access Control | CRITICAL |
| A2 | Cryptographic Failures | CRITICAL |
| A3 | Injection (SQL, NoSQL, OS, LDAP) | CRITICAL |
| A4 | Insecure Design | HIGH |
| A5 | Security Misconfiguration | HIGH |
| A6 | Vulnerable & Outdated Components | MEDIUM |
| A7 | Identification & Authentication Failures | CRITICAL |
| A8 | Software & Data Integrity Failures | HIGH |
| A9 | Security Logging & Monitoring Failures | MEDIUM |
| A10 | Server-Side Request Forgery (SSRF) | HIGH |

**Secret Leak Detection:** Scans for hardcoded API keys, passwords, connection strings, private keys, and cloud credentials. Recognized patterns include AWS, GCP, and Azure key formats. Any match is flagged as CRITICAL.

**Security Score:** A 0-10 score is automatically calculated using a penalty system: -4 per critical, -2 per high, -1 per medium. Displayed as a badge on the PR comment.

**Notlar:**

v2.0 ile eklediğimiz en önemli özelliklerden biri Security Deep Scan. Her PR review'ında AI, OWASP Top 10 framework'ünü kullanarak kapsamlı bir güvenlik analizi yapıyor. AI sadece pattern matching yapmıyor, bağlamı da anlıyor. Mesela bir string interpolation gördüğünde, bunun bir SQL sorgusu içinde mi yoksa bir log mesajında mı olduğunu ayırt edebiliyor.

Şimdi tablodaki 10 kategoriyi tek tek açıklayayım:

A1 — Broken Access Control. OWASP'ın 2021'de bir numaraya koyduğu kategori. Bir kullanıcının yetkisi olmayan kaynaklara erişebilmesi. Mesela normal bir kullanıcı /admin/users endpoint'ine istek atıp tüm kullanıcı listesini görebiliyorsa, bu A1 ihlali. Sistemimiz yetki kontrolü eksik olan endpoint'leri tespit ediyor.

A2 — Cryptographic Failures. Eski adıyla Sensitive Data Exposure. Hassas verilerin düzgün şifrelenmemesi. Mesela şifrelerin MD5 veya SHA1 gibi zayıf algoritmalarla hash'lenmesi, HTTPS yerine HTTP kullanılması, ya da encryption key'in kodda hardcoded olması. Bunların hepsi bu kategoriye giriyor.

A3 — Injection. SQL injection, NoSQL injection, OS command injection, LDAP injection gibi saldırılar. Kullanıcıdan gelen verinin doğrudan sorguya ya da komuta eklenmesi. Mesela string concatenation ile SQL sorgusu oluşturmak klasik bir örnek. Parameterized query kullanılmamışsa sistem bunu yakalar.

A4 — Insecure Design. Bu mimari seviyede bir sorun. Kod düzgün yazılmış olabilir ama tasarım zayıf. Mesela rate limiting olmaması, brute force koruması eksikliği, ya da iş mantığında güvenlik kontrolünün atlanabilmesi. AI bunu bağlamdan çıkarıyor.

A5 — Security Misconfiguration. Yanlış veya eksik yapılandırma. Debug modunun production'da açık kalması, default şifrelerin değiştirilmemesi, gereksiz servislerin aktif olması, error mesajlarında stack trace gösterilmesi gibi durumlar.

A6 — Vulnerable and Outdated Components. Bilinen güvenlik açığı olan eski kütüphanelerin kullanılması. Import veya dependency tanımlarında eski versiyonlar tespit edilirse uyarı verilir. Bu severity olarak medium çünkü her eski versiyon mutlaka açık demek değil, ama dikkat edilmesi lazım.

A7 — Identification and Authentication Failures. Kimlik doğrulama zayıflıkları. Zayıf şifre politikası, session yönetimi hataları, token süresinin sonsuz olması, multi-factor authentication eksikliği. Mesela JWT token'ın expire süresi ayarlanmamışsa bu kategoriye giriyor.

A8 — Software and Data Integrity Failures. Yazılım güncelleme sürecinde veya CI/CD pipeline'ında bütünlük kontrolü yapılmaması. Ayrıca insecure deserialization da bu kategoride. Güvenilmeyen kaynaktan gelen veriyi deserialize etmek ciddi bir risk.

A9 — Security Logging and Monitoring Failures. Güvenlik olaylarının loglanmaması veya izlenmemesi. Login başarısızlıkları loglanmıyor mu? Kritik işlemler audit trail bırakıyor mu? Bu eksiklikler saldırının fark edilmesini geciktirir. Severity medium çünkü doğrudan saldırı değil ama tespit süresini uzatıyor.

A10 — Server-Side Request Forgery, kısaca SSRF. Sunucunun kullanıcı girdisiyle iç ağdaki kaynaklara istek yapması. Mesela bir URL fetch özelliği varsa ve kullanıcı http://localhost:6379 gibi bir adres verip Redis'e erişebiliyorsa, bu A10. Cloud ortamlarında metadata endpoint'lerine erişim de bu kategoride.

Bunun yanında Secret Leak Detection var. Kodda hardcoded API key, password, connection string, private key gibi sensitive bilgileri tarayıp CRITICAL olarak raporluyor. AWS key formatı, GCP key formatı gibi bilinen pattern'leri de tanıyor.

Her review sonrası otomatik bir security score hesaplanıyor: 10 üzerinden başlıyor, critical issue başına 4, high başına 2, medium başına 1 puan düşüyor. Bu score PR comment'te badge olarak görünüyor. Eğer secret leak tespit edildiyse ayrı bir kırmızı badge da ekleniyor.

Her issue'nun OWASP ID'si ve mümkünse CWE ID'si de var — A1, CWE-89 gibi. Bu da kurumsal raporlama ve compliance açısından çok değerli.

---

## Slide 7 — AI Slop Detection

As AI coding assistants become mainstream, a new category of technical debt is emerging: "AI Slop" — code that compiles and runs but is poorly structured, repetitive, and hard to maintain. The system detects 8 common patterns and reports them as advisory warnings that never block the merge.

**8 Detected Patterns:**

| Pattern | Example |
|---------|---------|
| Redundant comments | `// Initialize the variable` — Comments that repeat what the code already says, adding zero informational value. |
| Generic naming | `data`, `result`, `temp`, `item` — Vague variable names that hurt readability and make debugging harder. |
| Boilerplate bloat | Repetition of framework defaults — Code that duplicates what the framework already handles out of the box. |
| Copy-paste blocks | Unrefactored duplications — Repeated logic that should be extracted into a helper function or loop. |
| Catch-all exception | `except Exception` — Overly broad error handling that swallows specific exceptions and hides bugs. |
| Hallucinated API | Non-existent method calls — AI-invented methods or classes that don't exist in the framework. |
| TODO/FIXME scaffold | `// TODO: implement this` — Incomplete skeleton code left behind by AI generation. |
| Inconsistent pattern | callback + async in same file — Mixing paradigms that indicate unreviewed AI output. |

**Rule:** AI Slop = max MEDIUM severity. Never blocks merge. Even if the AI labels a slop issue as critical, post-processing automatically caps it to medium.

**Notlar:**

İkinci büyük yenilik AI Slop Detection. Şimdi hepimiz Copilot kullanıyoruz, ChatGPT'ye kod yazdırıyoruz. Bu araçlar harika ama kontrolsüz bırakıldığında "slop" kod üretiyorlar. Teknik olarak çalışıyor ama bakım maliyetini feci artırıyor.

Ne demek slop kod? Mesela kodu aynen tekrar eden yorumlar: "Initialize the variable" — bunu zaten kodu okuyan herkes görüyor, bilgi değeri sıfır. Ya da her yere "data", "result", "temp" gibi generic değişken isimleri. Copy-paste ile yapılmış tekrar eden bloklar — bir loop veya helper function ile çözülebilecek şeyler. AI'ın uydurduğu, aslında o framework'te var olmayan API çağrıları, yani hallucinated API'lar. Ve tabii TODO: implement this gibi tamamlanmamış iskelet kodlar.

Sistemimiz bu 8 pattern'i otomatik tespit ediyor. Ama çok önemli bir tasarım kararı aldık: AI Slop sorunları asla merge'ü engellemez. Maximum severity MEDIUM. Bunlar bilgilendirme amaçlı kalite uyarıları. Çünkü bir generic değişken ismi yüzünden PR'ı bloklamak doğru değil. AI yanlışlıkla bir slop issue'ya critical derse bile, biz post-processing'de bunu otomatik olarak medium'a düşürüyoruz. Bu şekilde geliştiricilere faydalı geri bildirim veriyoruz ama iş akışını engellemiyoruz.

---

## Slide 8 — Live Dashboard

A fully-featured React dashboard provides real-time visibility into every review. Track active runs, drill into step-by-step timelines, analyze aggregated metrics, and manage configuration — all from a modern, responsive UI with no external CSS framework dependencies.

**4 Pages:**

| Page | Content |
|------|---------|
| PR Runs | Lists all active and completed reviews as cards with status badges, scores, and issue counts. Summary stats displayed at the top. |
| Run Detail | Timeline view showing each step of the review process (webhook → diff → AI → comment → status) with color-coded progress. |
| Analytics | Nine key metrics, score trends, OWASP breakdown, top issue categories, and per-author statistics. |
| Settings | Template picker with live preview, AI provider/model selection, comment strategy, and polling interval configuration. |

**Tech:** React + TypeScript + Vite | Polling-based | Pure CSS design system

**Notlar:**

Ekranda dashboard'un üç sayfasından kesitler görüyorsunuz.

Sağda PR Runs — ana ekran. Üstte özet kartlar: 1 aktif, 6 tamamlanmış, 1 hatalı, 8 toplam. Altında her review ayrı bir kart. PR-148 kırmızı ERROR — review sırasında sorun olmuş. PR-91 mavi DONE, score 8/10. Dikkat edin, biri GitHub'dan diğeri GitLab'dan — tek endpoint dört platformu destekliyor.

Solda Analytics — Score Trend'de her PR'ın kalite puanı çubuk grafik olarak görünüyor. PR-142 kırmızı 3/10, PR-56 yeşil 9/10. Altında OWASP dağılımı: A1 Broken Access Control 3 kez, en sık sorun. Bu grafik ekibin hangi güvenlik konularında zayıf olduğunu doğrudan gösteriyor.

Ortada Settings — template seçici, AI provider ve model dropdown'ları. Değiştirip Save dediğinizde backend anında güncelleniyor, restart gerekmez.

Teknik olarak React + TypeScript + Vite, polling tabanlı, sıfır CSS framework bağımlılığı.

---

## Slide 9 — Review Analytics

The analytics dashboard answers the key question: "Is our code quality improving or declining?" It aggregates data from every completed review and presents it through 9 stat cards and 4 analysis modules, enabling data-driven decisions about team performance and recurring issues.

**9 Key Metrics:**

Total Reviews · Avg Score · Avg Security Score · Total Issues · Critical Count · Security Issues · AI Slop Count · Blocked Merges · Secret Leaks

**4 Analysis Modules:**

- Score Trend — Tracks quality and security scores per PR over time, making improvements or regressions immediately visible.
- Security Breakdown — Visualizes OWASP category distribution and threat types as bar charts to identify the most common vulnerability patterns.
- Top Issue Categories — Ranks the most frequently reported issue types across all reviews.
- Author Stats — Per-developer table showing review count, average score, total issues, and merge block frequency.

**Notlar:**

Analytics sayfası, tüm review verilerini bir araya getirip anlamlı metrikler sunuyor. Buradaki temel sorumuz şu: "Ekibimiz nasıl gidiyor? Kod kalitemiz iyileşiyor mu kötüleşiyor mu?"

Üstte 9 stat kartı var: toplam review sayısı, ortalama kalite ve güvenlik puanları, toplam issue sayısı, critical sayısı, güvenlik sorunları, AI slop sayısı, merge engellenen PR sayısı ve secret leak sayısı. Bunlar tek bakışta genel durumu gösteriyor.

Altında dört analiz modülü var. Score Trend PR bazında kalite ve güvenlik puanlarını grafik olarak gösteriyor — zaman içinde iyileşme veya kötüleşmeyi hemen fark ediyorsunuz. Security Breakdown OWASP kategorilerini ve threat type'larını bar chart olarak görselleştiriyor — mesela en çok A1 Injection mı yoksa A5 Broken Access Control mı çıkıyor, bunu görüyorsunuz. Top Issue Categories en sık karşılaşılan sorun tiplerini gösteriyor. Author Stats tablosu da geliştirici bazında review sayısını, ortalama puanını, toplam issue sayısını ve kaç kez merge'ünün engellendiğini listeliyor.

Bu veriler şu an in-memory tutuluyor, sunucu restart'ta sıfırlanıyor. Ama roadmap'te persistent storage ile kalıcı hale getirmeyi planlıyoruz.

---

## Slide 10 — Settings & Template Picker

All review parameters can be modified at runtime through the Settings page. The most powerful feature is the template picker — switch between three built-in comment formats with a single click. Changes are persisted to `config.overrides.yaml` and applied instantly without restarting the server.

**3 Templates:**

| Template | Target Audience |
|----------|----------------|
| Default (Compact) | Developers — concise summary with badges, issue table, and collapsible details for quick scanning. |
| Detailed | QA / Full team — line-by-line feedback with file paths, code snippets, and a full severity matrix. |
| Executive (Visual) | Tech Lead — badge-heavy layout with risk analysis, tech debt estimates, and high-level status overview. |

**Other Settings:** AI Provider + Model · Comment Strategy (summary/inline/both) · Focus Areas · Poll Interval

**Hot-swap:** The backend re-initializes CommentService on save. The next webhook uses the new template immediately, no restart required.

**Notlar:**

Settings sayfası üzerinden tüm review parametrelerini runtime'da değiştirebiliyorsunuz. En önemli özellik template seçici. Üç hazır template arasında radio button ile geçiş yapıyorsunuz.

Default template kompakt bir format — geliştiriciler için ideal. Badge'ler, kısa bir issue tablosu ve açılır-kapanır detaylar içeriyor. Detailed template tam code-level feedback veriyor — her sorunun dosya yolu, satır numarası, kod snippet'i ve önerisi detaylı açılıyor. Executive template ise tech lead'ler ve yöneticiler için tasarlandı — daha çok badge, risk tablosu ve genel durum özeti ağırlıklı.

Template değiştirdiğinizde Save diyorsunuz, backend anında CommentService'i yeniden oluşturuyor. Sunucu restart'a gerek yok. Bir sonraki webhook'ta seçili template ile yorum oluşturuluyor. Ayar config.overrides.yaml dosyasına persist ediliyor, yani sunucu kapanıp açılsa bile seçiminiz korunuyor.

Bunun dışında AI provider ve modelini de buradan değiştirebiliyorsunuz. Comment strategy'yi summary, inline veya both olarak seçebiliyorsunuz. Focus areas'ı özelleştirebiliyorsunuz. Dashboard'un polling interval'ini ayarlayabiliyorsunuz.

---

## Slide 11 — Platform Support

All four major Git platforms are supported through a single `/webhook` endpoint. The system identifies the source platform automatically by inspecting HTTP headers (e.g., `X-GitHub-Event`, `X-Gitlab-Event`). Each platform has a dedicated adapter class extending `BasePlatformAdapter`, making it trivial to add new platforms following the open-closed principle.

**4 Platforms, Single Endpoint:**

| Platform | Auth | Status |
|----------|------|--------|
| GitHub | Bearer Token | ✅ |
| GitLab | Private Token | ✅ |
| Bitbucket | App Password | ✅ |
| Azure DevOps | PAT | ✅ |

**Auto-detection:** Platform identification via HTTP headers — falls back to payload structure analysis if no known header is found.

**Full feature set:** Diff fetching · Summary comment · Inline comment · Status update · Merge blocking — all at feature parity across every platform.

**Notlar:**

Sistemin en güçlü yanlarından biri platform bağımsızlığı. Dört büyük platformu destekliyoruz: GitHub, GitLab, Bitbucket ve Azure DevOps. Ama hepsi tek bir webhook endpoint'i kullanıyor: /webhook.

Nasıl çalışıyor? Her platform kendine özgü HTTP header'ları gönderiyor. GitHub X-GitHub-Event gönderiyor, GitLab X-Gitlab-Event, Bitbucket X-Event-Key, Azure X-VSS-ActivityId. Sistem gelen isteğin header'ına bakıyor ve platformu otomatik tespit ediyor. Eğer hiçbir header bulamazsa payload yapısından da çıkarım yapabiliyor.

Her platform için tam özellik seti var: diff çekme, summary yorum yazma, satır bazlı inline yorum, PR status güncelleme ve merge bloklama. Dördü de aynı seviyede destekleniyor.

Mimari açıdan baktığınızda, her platform için bir adapter sınıfı var ve hepsi BasePlatformAdapter abstract class'ından türüyor. Yeni bir platform eklemek istediğinizde sadece yeni bir adapter yazıyorsunuz. Mevcut iş mantığı hiç değişmiyor. Bu da open-closed principle'ın güzel bir uygulaması.

---

## Slide 12 — AI Provider System

Three AI providers are supported through a unified abstract interface. A factory pattern creates instances by name, and a strategy pattern enables runtime switching. There is zero vendor lock-in — adding a new provider requires only implementing the interface and registering it in the config.

| Provider | Model | Speed | Cost |
|----------|-------|:-----:|:----:|
| Groq | Llama 3.3 70B | Very fast | Free/low — Recommended for high-volume daily use. Reviews complete in 5-15 seconds. |
| OpenAI | GPT-4o, GPT-4o-mini | Medium | Medium — Best for deep code analysis and complex logic review. |
| Anthropic | Claude 3.5 Sonnet | Medium | Medium-high — Excels at security analysis and nuanced vulnerability detection. |

**Changeable in 3 ways:** config.yaml file · UI Settings dropdown · MCP Tool call override — all without server restart.

**Notlar:**

Üç farklı AI provider'ı destekliyoruz ve hepsi aynı abstract interface'den türüyor. Factory pattern ile isimden instance oluşturuluyor, strategy pattern ile runtime'da geçiş yapılabiliyor.

Groq önerimiz günlük yüksek hacimli kullanım için. Llama 3.3 70B modeli inanılmaz hızlı — 5-15 saniye içinde review tamamlanıyor. Ve maliyeti neredeyse sıfır. OpenAI'ı karmaşık kod analizi için öneriyoruz, GPT-4o modeli daha derinlemesine anlıyor. Anthropic'in Claude 3.5 Sonnet modeli özellikle güvenlik analizi konusunda çok başarılı.

Provider değiştirmek üç şekilde mümkün: config.yaml'da provider ve model alanını değiştirerek, UI Settings sayfasından dropdown ile seçerek ya da MCP tool çağrısında runtime override yaparak. Üçü de sunucu yeniden başlatmaya gerek kalmadan çalışıyor. Vendor lock-in diye bir şey yok — yarın yeni bir AI provider çıksa, interface'i implemente edip config'e eklemeniz yeterli.

---

## Slide 13 — Language Detection & Rule System

The system auto-detects the dominant programming language from file extensions in the PR diff and loads language-specific review rules. This ensures C# code is reviewed with C# rules, not Python rules — dramatically reducing false positives. When a new language appears for the first time, the RuleGenerator uses AI to create tailored rules automatically.

**25+ languages:** C# · Java · Python · TypeScript · Go · Rust · Swift · Kotlin · and more — detected from file extensions in the diff.

**19 rule files:** Markdown-based and Git-versioned. Includes both general rules (compilation.md, security.md, performance.md) and language-specific variants (csharp-compilation.md, python-security.md, go-performance.md).

**AI-powered auto rule generation:** When a PR arrives in an unsupported language, RuleGenerator takes the general template, sends it to the AI with the target language, and saves the generated rules for future use. The system grows its own knowledge base.

**Notlar:**

Sistem 25'ten fazla programlama dilini otomatik tespit edebiliyor. PR'daki dosya uzantılarına bakarak en baskın dili çıkarıyor. Mesela 5 tane .cs dosyası ve 2 tane .json dosyası varsa, sonuç C#.

Dil tespiti neden önemli? Çünkü dile özel kurallarımız var. Rules klasöründe 19 markdown dosyası var. Genel kurallar: compilation.md, security.md, performance.md, best-practices.md. Ve dile özel versiyonları: csharp-compilation.md, python-security.md, go-performance.md gibi. Bu kurallar AI prompt'una bağlam olarak ekleniyor. C# kodu incelenirken Python kuralları uygulanmıyor, bu false positive'leri ciddi ölçüde azaltıyor.

En güzel özelliklerden biri de otomatik rule üretimi. Diyelim ilk kez Rust dilinde bir PR geldi. Sistem rust-security.md dosyasını arıyor, bulamıyor. Bu durumda RuleGenerator devreye giriyor: genel security.md şablonunu alıyor, AI'a veriyor ve "bunu Rust diline özel olarak yeniden yaz" diyor. Üretilen dosya kaydediliyor ve bir sonraki Rust review'ında hazır. Yani sistem kendini genişletiyor.

---

## Slide 14 — Short-Circuit & Severity

The short-circuit mechanism is an intelligent prioritization strategy. If a compilation error is detected, all other checks (security, performance, AI slop) are skipped — because analyzing code that doesn't compile is meaningless. This is enforced at two layers: the AI prompt explicitly instructs a halt, and post-processing programmatically filters the response.

**Short-Circuit:** If a compilation error is found, all other checks are skipped. Only compilation issues are reported, saving AI tokens and keeping feedback focused.

**5 Severity Levels:** CRITICAL → HIGH → MEDIUM → LOW → INFO — each level determines the impact on PR status and merge eligibility.

**Merge blocking:** Any critical issue sets the PR status to failure. With branch protection enabled, merge is automatically blocked until the developer fixes and pushes again, triggering a new review cycle.

**Notlar:**

Short-circuit mekanizması akıllı bir önceliklendirme stratejisi. Mantık basit: eğer kodda syntax hatası veya compilation hatası varsa, o kod zaten çalışmayacak. Dolayısıyla güvenlik analizi, performans kontrolü, AI slop tespiti yapmanın bir anlamı yok. Sistem compilation hatası bulduğu anda diğer kontrolleri atlıyor ve sadece compilation sorunlarını raporluyor.

Bunu iki katmanda garanti ediyoruz. Birincisi AI prompt'una açık talimat veriyoruz: "compilation hatası bulursan dur, başka bir şey kontrol etme." İkincisi, AI'dan gelen yanıtı programatik olarak filtreliyoruz. Yani AI talimata uymasa bile, post-processing'de sadece compilation issue'ları bırakıyoruz.

Severity sistemi beş kademeli: critical, high, medium, low, info. Critical issue bulunduğunda PR status'u failure olarak işaretleniyor. Eğer repoda branch protection aktifse, merge otomatik engelleniyor. Geliştirici düzeltmeyi yapıp push ettiğinde yeni bir review tetikleniyor ve cycle tekrar başlıyor.

---

## Slide 15 — Template System

The review comment posted to each PR is generated by a template engine. Four options are available to suit different audiences, from developers who want a quick scan to executives who need a high-level risk overview. All templates were enhanced in v2.0 with security and AI slop sections.

**4 Templates:**

| Template | Purpose |
|----------|---------|
| Default | Compact format for developers — badges at the top, a concise issue table, and collapsible detail sections for each finding. |
| Detailed | Full code-level feedback for QA teams — file-by-file breakdown with code snippets, line numbers, and a severity matrix. |
| Executive | Visual format for tech leads — heavy use of shield badges, risk analysis table, and overall status summary. |
| Custom | Drop your own markdown template into the `custom_templates/` folder. Uses placeholders like `{score}`, `{total_issues}`, `{issues_list}`. |

**v2.0 additions:** AI Slop Badge · Security Score Badge · Secret Leak Badge · OWASP table · AI Slop detail section — automatically included in all templates.

**Notlar:**

PR'a yazılan review yorumunun formatı template sistemi ile yönetiliyor. Dört seçenek var.

Default template geliştiriciler için tasarlandı. Kompakt ve okunması hızlı. Üstte badge'ler — score, security, issue sayısı — altta bir issue tablosu ve her sorunun detayı collapsible olarak. Detailed template QA ekibi ve kapsamlı review isteyenler için. Dosya bazlı dağılım, her sorunun tam kodu, severity matrix dahil. Executive template tech lead'ler ve yöneticiler için — shield badge'leri ağırlıklı, risk analizi, tech debt tahmini, genel durum özeti.

v2.0 ile tüm template'lere yeni bölümler ekledik: AI Slop badge'i ve detay tablosu, Security Score badge'i, secret leak badge'i ve OWASP tabanlı güvenlik bölümü. Hangi template'i seçerseniz seçin, bu bilgiler otomatik olarak yoruma dahil ediliyor.

Bir de Custom template var. custom_templates klasörüne kendi markdown dosyanızı koyabiliyorsunuz. Placeholder'larla çalışıyor: {score}, {total_issues}, {issues_list} gibi. Kendi takımınıza özel format tanımlayabilirsiniz.

---

## Slide 16 — MCP & IDE Integration

Beyond automated webhook reviews, the server also acts as an MCP (Model Context Protocol) tool provider. Developers can review code, analyze diffs, or run security scans directly from their IDE — enabling a pre-review workflow before even opening a PR. Provider override is supported per tool call.

**3 MCP Tools:**

| Tool | Description |
|------|-------------|
| review_code | Send a code snippet to the AI for instant review feedback directly in your editor. |
| analyze_diff | Extract statistical insights from a diff — file count, change distribution, and complexity indicators. |
| security_scan | Run a security-focused OWASP scan on selected code without triggering a full review. |

**Endpoint:** `GET /mcp/sse` (Server-Sent Events) — Standard MCP protocol for real-time tool communication.

**Supported IDEs:** Claude Desktop · Cursor · VS Code · Windsurf — Any MCP-compatible client can connect.

**Notlar:**

Webhook tabanlı otomatik review dışında, bir de IDE entegrasyonu var. MCP yani Model Context Protocol — Anthropic tarafından geliştirilen açık bir standart. AI modellerinin harici araçlarla iletişim kurmasını sağlıyor.

Sunucumuz SSE endpoint'i üzerinden MCP client'lara bağlanıyor. Üç tool sunuyoruz: review_code ile seçili bir kod parçacığını AI'a review ettirebiliyorsunuz, analyze_diff ile bir diff'in istatistiklerini çıkarabiliyorsunuz, security_scan ile sadece güvenlik odaklı tarama yapabiliyorsunuz.

Bu ne işe yarıyor? PR açmadan önce bile kodunuzu kontrol edebiliyorsunuz. Cursor'da veya VS Code'da kod yazarken MCP tool'u çağırıyorsunuz, saniyeler içinde AI geri bildirim veriyor. Bir nevi pre-review imkanı. Ve burada provider override da yapabiliyorsunuz — mesela normalde Groq kullanıyorsunuz ama güvenlik taraması için Claude'u tercih etmek istiyorsunuz, tool çağrısında belirtmeniz yeterli.

---

## Slide 17 — API Endpoint Reference

The server exposes over 20 REST API endpoints powered by FastAPI with automatic OpenAPI/Swagger documentation at `/docs`. Every aspect of the system — configuration, rules, live logs, analytics, and the UI — is accessible through well-structured API categories.

**20+ endpoints:**

| Category | Endpoints |
|----------|-----------|
| Core | Health check · Webhook · MCP SSE — Essential server operations and webhook entry point. |
| Config | GET/PUT config · Template list/switch — Read and update runtime configuration including template selection. |
| Rules | List · Resolve · Get content — Browse, resolve by language/focus area, and read individual rule files. |
| Live Logs | Config · Active · All runs · Run events — Dashboard data with cursor-based pagination for event streaming. |
| Analytics | Overview · Trend · Top issues · Security · Authors · Recent — Full analytics suite for aggregated review data. |
| UI | SPA index · SPA routing — Serves the React single-page application and handles client-side routing. |

**Notlar:**

Sistemde toplam 20'den fazla REST API endpoint'i var. Bunları kategorilere ayırabiliriz.

Core endpoint'ler: health check, webhook alımı ve MCP SSE bağlantısı. Config endpoint'leri: GET ile mevcut config'i okuyorsunuz, PUT ile güncelliyorsunuz. Template listesi ve runtime template switch de burada. Rules endpoint'leri: kural dosyalarını listeleme, focus area ve dile göre çözümleme ve belirli bir kuralın içeriğini getirme.

Live Logs endpoint'leri dashboard için: logs config, aktif run'lar, tüm run'lar ve belirli bir run'ın event'leri — bu cursor-based pagination ile çalışıyor. Analytics endpoint'leri: overview, score trend, top issues, security breakdown, author stats ve recent reviews. Son olarak UI endpoint'leri: React SPA'yı serve ediyor.

Tüm bu endpoint'ler FastAPI üzerinde çalışıyor, otomatik OpenAPI/Swagger dokümantasyonu var. localhost:8000/docs adresinden interactive olarak test edebilirsiniz.

---

## Slide 18 — CodeRabbit Comparison

A head-to-head comparison with CodeRabbit, the market's most recognized AI code review tool. The MCP Server outperforms on every dimension: platform coverage, AI flexibility, security depth, observability, and cost — while offering full data sovereignty through self-hosting.

| Feature | CodeRabbit | MCP Server |
|---------|:----------:|:----------:|
| Platforms | 2 | **4** |
| AI Provider | Fixed | **3, switchable** |
| OWASP Scan | ✗ | **✓** |
| AI Slop | ✗ | **✓** |
| Live Dashboard | ✗ | **✓** |
| Analytics | Basic | **Full** |
| Templates | 1 | **4 + custom** |
| IDE (MCP) | ✗ | **✓** |
| Self-hosted | ✗ | **✓** |
| Open Source | ✗ | **✓** |

**Cost (10 people/year):** CodeRabbit $2,880 → MCP Server ~$300-840 **(70-90% savings)**. For a 50-person team, annual savings exceed $13,000. Self-hosted means your code never leaves your infrastructure.

**Notlar:**

Piyasanın en bilinen rakibi CodeRabbit ile karşılaştıralım. Tablodaki farklar ortada ama birkaç kritik noktayı vurgulayalım.

Platform desteği: CodeRabbit sadece GitHub ve GitLab destekliyor. Biz dört platform. Yani Bitbucket veya Azure DevOps kullanan bir ekipseniz CodeRabbit'i kullanamazsınız bile.

AI provider: CodeRabbit kendi sabit modelini kullanıyor, değiştirme imkanı yok. Biz üç farklı provider sunuyoruz ve runtime'da değiştirilebilir. OWASP tabanlı security scan, AI slop detection, live dashboard, analytics, template sistemi — bunların hiçbiri CodeRabbit'te yok.

Ve en önemlisi: maliyet. 10 kişilik bir ekip için CodeRabbit yılda 2,880 dolar. Bizim çözümde ise sadece AI API maliyeti ve küçük bir sunucu maliyeti var — yıllık 300-840 dolar arası. Bu %70 ile %90 arasında tasarruf demek. 50 kişilik bir ekipte bu fark 13,000 doların üzerine çıkıyor.

Ve veri gizliliği meselesi var. CodeRabbit'te kodunuz 3. parti sunuculara gidiyor. Self-hosted çözümde her şey kendi kontrolünüzde.

---

## Slide 19 — Live Demo

A walkthrough of a real-world scenario: a developer opens a PR to add an authentication module. The system detects the webhook, reviews the code, finds critical security issues and AI slop patterns, posts a formatted comment with badges, and blocks the merge — all within seconds.

**Scenario:** A PR opened on GitHub → AI Review → Comment on PR

**Console output (summarized):**

```
🔔 WEBHOOK → 📦 GITHUB → PR #42: Add auth module
📥 Diff: 4,120 bytes → 4 files
🤖 AI Review: Score 5/10
   🔴 1 Critical (SQL Injection — A1)
   🟠 1 High (Missing CSRF — A5)
   🟡 2 Medium (AI Slop)
💬 Summary comment posted
❌ MERGE BLOCKED
```

**Comment on PR:** Quality 5/10 · Security 4/10 · AI Slop 2 · Merge BLOCKED

**Notlar:**

Şimdi canlı bir senaryo üzerinden gidelim. Bir geliştirici GitHub'da PR açıyor: "Add user authentication module". feature/auth branch'inden main'e.

Konsol çıktısında görebiliyorsunuz: webhook alındı, platform GitHub olarak tespit edildi. Diff çekildi — 4,120 byte, 4 dosya değişmiş. AI review başladı, Groq provider ile Llama 3.3 modeli kullanılıyor.

Sonuç: 5/10 score. 6 issue bulundu. Bunlardan 1 tanesi critical — SQL injection, OWASP A1. 1 tanesi high — missing CSRF protection, OWASP A5. 2 tanesi medium — AI slop, gereksiz yorumlar. 2 tanesi de low seviyede.

PR'a giden yorum executive template formatında: üstte badge'ler — Quality 5/10 kırmızı, Security 4/10 kırmızı, AI Slop 2 found turuncu, Merge BLOCKED kırmızı. Altta OWASP tablosu ve AI slop tablosu. Geliştirici SQL injection'ı düzeltip push ettiğinde yeni review tetiklenir, score artar ve merge açılır.

---

## Slide 20 — Project in Numbers

A quantitative overview of the project's scope and capabilities. The entire system runs in a single Docker container (~150MB image) and can be deployed to any VPS in minutes.

| Metric | Value |
|--------|-------|
| Platforms | 4 |
| AI Providers | 3 |
| Programming Languages | 25+ |
| Rule Files | 19 |
| PR Templates | 4 + custom |
| MCP Tools | 3 |
| OWASP Categories | 10 |
| AI Slop Patterns | 8 |
| API Endpoints | 20+ |
| UI Pages | 4 |
| Source Files | 40+ |

**Notlar:**

Projenin sayısal büyüklüğüne bakalım. 4 platform desteği, 3 AI provider, 25'ten fazla programlama dili desteği, 19 review kuralı dosyası, 4 hazır template artı custom template imkanı, 3 MCP tool, OWASP Top 10'un 10 kategorisinin tamamı, 8 AI slop pattern, 20'den fazla API endpoint, 4 UI sayfası ve 40'tan fazla kaynak dosya. Python ve TypeScript ile modüler mimari.

Bütün bunlar tek bir Docker container'da çalışıyor. Image boyutu yaklaşık 150 megabyte. Bir VPS'e deploy edip webhook URL'ini ayarlamak dakikalar alıyor.

---

## Slide 21 — Value Proposition

The combined value of the system spans cost, time, security, quality, visibility, flexibility, and privacy. It replaces multiple fragmented tools with a single unified solution that keeps your code within your own infrastructure.

| Dimension | Impact |
|-----------|--------|
| Cost | 70-90% savings |
| Time | Manual review reduced by 60-80% |
| Security | OWASP + Secret Leak proactive scanning |
| AI Quality | Low-quality AI code auto-detected |
| Visibility | Data-driven decisions via Dashboard + Analytics |
| Flexibility | 4 platforms, 3 AI, 25+ languages, 4 templates |
| Privacy | Self-hosted, code never leaves the company |

**Notlar:**

Sonuç olarak bu projenin değer önerisini özetleyelim. Maliyet tarafında rakiplere göre %70-90 arası tasarruf. Zaman tarafında manuel review süresi %60-80 oranında azalıyor — geliştirici review'a değil, üretime odaklanıyor.

Güvenlik tarafında OWASP Top 10 ve secret leak detection ile proaktif güvenlik taraması — sorunlar merge'den önce yakalanıyor. AI kalitesi tarafında slop detection ile ekiplerin AI araçlarını bilinçli kullanması sağlanıyor. Görünürlük tarafında live dashboard ve analytics ile veri odaklı kararlar alınıyor — hangi sorunlar tekrar ediyor, kod kalitesi iyileşiyor mu, kim en çok bloklanıyor gibi soruların cevabı var.

Esneklik tarafında tek çözüm dört platformu, üç AI provider'ı, 25'ten fazla dili ve dört farklı template'i destekliyor. Ve en kritik konu: veri gizliliği. Self-hosted yapı sayesinde kodunuz asla şirket dışına çıkmıyor. GDPR, KVKK uyumlu.

---

## Slide 22 — Roadmap

The project has a clear evolution path from a single-team tool to a multi-tenant SaaS platform. Each phase builds on the previous, adding intelligence, persistence, and collaboration capabilities.

**Short-term (Q2 2026):**
- Category-based model selection (Security → Claude, Compilation → GPT-4) — Use the best AI model for each specific analysis type.
- Persistent analytics (SQLite/PostgreSQL) — Move from in-memory to durable storage so metrics survive restarts.
- Notification hub (Slack, Teams) — Push review results to team communication channels in real-time.

**Mid-term (Q3-Q4 2026):**
- IDE plugins (VS Code, IntelliJ) — Native extensions beyond MCP for broader IDE support.
- Team-based rules (RBAC) — Different teams can have different rule sets and severity thresholds.
- Smart caching & incremental review — Cache similar patterns to skip redundant AI calls and review only changed files.

**Long-term (2027):**
- Learning from feedback (👍/👎) — Developers rate AI comments; the system learns and reduces false positives over time.
- Multi-tenant SaaS — Serve multiple organizations from a single platform with isolated configurations.

**Notlar:**

İleriye dönük planlarımız var. Kısa vadede — bu çeyrek içinde — kategori bazlı model seçimi üzerinde çalışıyoruz. Fikir şu: güvenlik taraması için Claude'u kullan çünkü güvenlik konusunda çok iyi, compilation kontrolü için GPT-4'ü kullan çünkü syntax anlama konusunda güçlü, genel review için Groq'u kullan çünkü hızlı ve ucuz. Ayrıca analytics verilerini şu an in-memory tutuyoruz, bunu SQLite veya PostgreSQL ile kalıcı hale getireceğiz. Slack ve Teams notification entegrasyonu da bu dönemde gelecek.

Orta vadede IDE eklentileri planlıyoruz — VS Code ve IntelliJ için native extension'lar. Team-based rules ile farklı takımların farklı kural setleri olabilecek. Akıllı caching ile benzer pattern'leri tekrar AI'a göndermeden cache'den çözeceğiz.

Uzun vadede feedback loop mekanizması — geliştiriciler AI yorumlarına 👍 veya 👎 veriyor, sistem bunlardan öğreniyor, false positive oranı düşüyor. Ve en son multi-tenant SaaS modeli ile birden fazla organizasyonu tek platform üzerinden destekleme.

---

## Slide 23 — Q&A

Here are the most commonly asked questions about the system. Each addresses a key concern around performance, workflow impact, security tooling, data durability, scalability, and extensibility.

**Frequently Asked Questions**

- How long does a review take? → 10-30 seconds (5-15s with Groq)
- Does AI Slop block merge? → No, max severity is MEDIUM
- Does Security scan replace SAST? → Complementary, best used together
- Is analytics data persistent? → Currently in-memory, persistent storage planned
- Multiple repos on one server? → Yes, just configure the webhook URL
- New language support? → Automatic, RuleGenerator creates rules via AI

**Notlar:**

Şimdi sorularınızı alalım. Ama öncesinde en sık sorulan soruları paylaşayım.

Review ne kadar sürer? Groq ile genellikle 5 ila 15 saniye, OpenAI veya Anthropic ile 15 ila 30 saniye arası. Diff büyüklüğüne bağlı tabii ama ortalama bu.

AI Slop merge'ü engelliyor mu? Kesinlikle hayır. Bunu tasarım kararı olarak aldık. AI slop uyarıları bilgilendirme amaçlı, maximum medium severity. Merge'ü sadece critical seviye sorunlar engelliyor.

Security Deep Scan mevcut SAST araçlarının yerini alır mı? Tam olarak değil. AI tabanlı tarama geleneksel SAST'tan farklı — bağlamı anlıyor, daha az false positive üretiyor ama rule-based kesinlik açısından geleneksel araçlar hala değerli. İkisi birlikte kullanılabilir.

Birden fazla repo için tek server yeterli mi? Evet. Her repoda sadece webhook URL'ini ayarlamanız yeterli. Platform farkı da önemli değil — bir repo GitHub'da, diğeri Bitbucket'ta olabilir, ikisi de aynı server'a webhook atabilir.

Başka soruları olan varsa buyursun.

---

**Prepared by:** Mennano Development Team
**Version:** 2.0.0 | **March 2026**
