# MCP AI Code Review Server — Teknik Sunum

> **Versiyon:** 2.0.0 | **Tarih:** Mart 2026 | **Format:** Canva Docs → Sunum

---

## Slayt 1 — Kapak

**MCP AI Code Review Server**

Yapay Zeka Destekli, Platform-Bağımsız Kod İnceleme Sistemi

- 4 Platform — GitHub · GitLab · Bitbucket · Azure DevOps
- 3 AI Provider — GPT-4 · Claude 3.5 · Llama 3.3
- OWASP Top 10 Security Deep Scan
- AI Slop Detection
- Live Dashboard & Analytics
- MCP IDE Entegrasyonu

**Notlar:**

Herkese merhaba. Bugün sizlere geliştirdiğimiz MCP AI Code Review Server projesini anlatacağım. Bu proje kısaca şunu yapıyor: bir geliştirici herhangi bir platformda — ister GitHub olsun, ister GitLab, Bitbucket ya da Azure DevOps — bir Pull Request açtığında, sistem otomatik olarak o PR'ı yapay zeka ile inceler, güvenlik taraması yapar, AI ile yazılmış düşük kaliteli kodu tespit eder ve sonucu doğrudan PR'a yorum olarak yazar. Tüm bunlar saniyeler içinde, hiçbir manuel müdahale olmadan gerçekleşir. Üstelik tamamen self-hosted, yani kodunuz asla şirket dışına çıkmıyor.

---

## Slayt 2 — Neden Bu Projeye İhtiyaç Var?

| Problem | Etki |
|---------|------|
| Manuel review çok zaman alıyor | 2-4 saat/gün üretkenlik kaybı |
| İnsan gözü her hatayı yakalayamıyor | Güvenlik açıkları kaçıyor |
| Platform başına farklı araçlar | Araç maliyeti + eğitim |
| Tutarsız review kalitesi | Reviewer'a göre değişen standart |
| AI-generated kod kalitesizleşiyor | Teknik borç birikimi |
| Güvenlik taraması ayrı araç | SAST/DAST/secret scan ayrı kurulum |
| Mevcut çözümler pahalı ve kısıtlı | CodeRabbit: $12-24/kişi/ay, vendor lock-in |
| Veri gizliliği endişesi | Kod 3. parti sunuculara gidiyor |

**Notlar:**

Şimdi bu projeyi neden yaptığımızı konuşalım. Hepimiz biliyoruz ki kod inceleme süreci yazılım geliştirmenin en kritik aşamalarından biri. Ama mevcut durumda ciddi sorunlar var.

Birincisi, zaman. Bir geliştirici günde ortalama 2 ila 4 saat sadece başkalarının kodunu incelemeye harcıyor. Bu ciddi bir üretkenlik kaybı. İkincisi, insan gözü her şeyi yakalayamıyor — özellikle güvenlik açıkları, ince compilation hataları ve performans sorunları gözden kaçabiliyor.

Bir de artık herkes AI kullanıyor: Copilot, ChatGPT ile kod üretiyor. Ama bu kodun kalitesi kontrol edilmiyor. "AI Slop" dediğimiz gereksiz yorumlar, generic değişken isimleri, copy-paste bloklar birikiyor.

Piyasadaki çözümlere bakarsanız, CodeRabbit gibi araçlar var ama kişi başı 12-24 dolar aylık maliyet, sadece 2 platformu destekliyor, özelleştirme sınırlı ve en önemlisi kodunuz 3. parti sunuculara gidiyor. Biz bütün bu sorunları tek bir self-hosted çözümle ortadan kaldırmak istedik.

---

## Slayt 3 — Neden Python?

| Kriter | Python | Node.js | C#/.NET | Go |
|--------|:------:|:-------:|:-------:|:--:|
| AI SDK Olgunluğu | ★★★★★ | ★★★ | ★★ | ★★ |
| Platform API Kütüphaneleri | ★★★★★ | ★★★ | ★★★ | ★★ |
| MCP SDK Desteği | ★★★★★ | ★★★★ | ★★ | ★ |
| Geliştirme Hızı | ★★★★★ | ★★★★ | ★★★ | ★★★ |

**Notlar:**

"Neden Python?" diye sorulabilir — özellikle ekip olarak .NET ağırlıklı çalışıyorsak. Cevap aslında çok net: bu bir AI-first proje ve AI dünyasının lingua franca'sı Python.

OpenAI, Anthropic, Groq — üçünün de resmi SDK'ları Python-first. Üstelik GitHub, GitLab, Bitbucket, Azure DevOps için olgun Python kütüphaneleri var: PyGithub, python-gitlab, atlassian-python-api, azure-devops. MCP protokolünün resmi SDK'sı da Python'da.

FastAPI ile dakikalar içinde production-ready API kurabiliyorsunuz. Pydantic v2 ile tip güvenliği ve otomatik validation geliyor. Async/await native destek var. Docker image'ı 150 megabyte.

Aynı işi C# ile yapmaya kalksanız, AI SDK'ları ya community-driven ya da çok yeni. Platform API kütüphaneleri ya eksik ya da sınırlı. Go'da da durum benzer. Tabloda gördüğünüz gibi Python her kriterde açık ara önde. Bu proje için en pragmatik tercih buydu.

---

## Slayt 4 — Mimari Genel Bakış

**Bileşenler:**

- Webhook Handler → Platform Detection (Auto)
- Language Detector (25+ dil) → Rules Helper (Markdown)
- AI Review Engine: Provider Router (Groq/OpenAI/Anthropic)
- Review Modules: Code Quality, Security Deep Scan, AI Slop, Compilation
- Comment Service → Template Engine (Default/Detailed/Executive)
- Platform Adapters → Yorum + Status gönderimi
- Live Log Store + Analytics Store
- React UI Dashboard

**Tasarım İlkeleri:** Platform Agnostik · Provider Agnostik · Config-Driven · Self-Hosted · Observable

**Notlar:**

Bu slaytla sistemin büyük resmini görelim. Mimari altı ana katmandan oluşuyor.

En solda Webhook Handler var. Herhangi bir platformdan gelen webhook isteğini alıyor ve HTTP header'larına bakarak platformu otomatik tespit ediyor. GitHub mu, GitLab mu, Bitbucket mu — bunu sizin belirtmenize gerek yok, sistem kendisi anlıyor.

Ortada AI Review Engine var — bu sistemin kalbi. Üç farklı AI provider'ı destekliyor: Groq, OpenAI ve Anthropic. Hangisini kullanacağınız config'den veya UI'dan seçilebilir. Review engine tek seferde dört modülü çalıştırıyor: standart kod kalitesi kontrolü, OWASP tabanlı security deep scan, AI slop detection ve compilation kontrolü.

Sağda Comment Service var. AI'dan gelen sonuçları seçili template ile formatlayıp platforma yorum olarak gönderiyor. Altta da yeni eklediğimiz bileşenler var: Live Log Store ile review sürecini real-time izleyebiliyorsunuz, Analytics Store ile de aggrege metrikler topluyorsunuz.

Temel tasarım ilkelerimiz şunlar: platform agnostik, provider agnostik, config-driven yani her şey YAML'dan yönetiliyor, self-hosted ve observable yani canlı izlenebilir.

---

## Slayt 5 — Review Akışı (5 Adım)

1. **Webhook Alındı** — Platform tespiti, live log başlar
2. **Diff Çekildi** — Adapter ile API'den diff, dil tespiti, rule yükleme
3. **AI İnceleme** — Code review + Security scan + AI Slop + Short-circuit
4. **Yorum Gönderimi** — Template ile formatlama, badge'ler, PR'a yorum
5. **Status Güncelleme** — success/failure, merge bloklama, analytics kaydı

**Notlar:**

Şimdi bir PR açıldığında uçtan uca ne oluyor, onu adım adım görelim.

Birinci adım: Platform webhook gönderiyor, sistem bunu alıyor, header'dan platformu tespit ediyor ve live log kaydını başlatıyor. Artık bu review'ı dashboard'dan canlı izleyebilirsiniz.

İkinci adım: Platform adapter'ı devreye giriyor. İlgili API'yi çağırıp PR'ın diff'ini çekiyor. Diff'teki dosya uzantılarına bakarak programlama dilini tespit ediyor — mesela .cs dosyaları varsa C#, .py varsa Python. Sonra o dile özel rule dosyalarını yüklüyor.

Üçüncü adım: Burası en kritik kısım. AI'a diff ve kurallar gönderiliyor, AI tek seferde dört farklı analiz yapıyor: standart kod kalitesi, OWASP tabanlı güvenlik taraması, AI slop detection ve compilation kontrolü. Önemli bir mekanizma var burada: eğer compilation hatası bulunursa, diğer kontroller yapılmaz. Biz buna short-circuit diyoruz. Derlenmeyen kodda güvenlik analizi yapmanın anlamı yok.

Dördüncü adım: Sonuçlar seçili template ile formatlanıyor — badge'ler, tablolar, detay bölümleri — ve PR'a yorum olarak gönderiliyor.

Beşinci adım: PR'ın status'u güncelleniyor. Critical sorun varsa failure olarak işaretleniyor ve merge otomatik engelleniyor. Son olarak review sonuçları analytics store'a kaydediliyor.

---

## Slayt 6 — Security Deep Scan

**OWASP Top 10 tam kapsam:**

| OWASP | Kategori | Severity |
|-------|----------|----------|
| A1 | Injection (SQL, NoSQL, OS) | CRITICAL |
| A2 | Broken Authentication | CRITICAL |
| A3 | Sensitive Data Exposure | CRITICAL |
| A5 | Broken Access Control | HIGH |
| A7 | XSS | HIGH |
| A8 | Insecure Deserialization | CRITICAL |

**Secret Leak Detection:** API keys, passwords, connection strings, private keys, cloud credentials

**Security Score:** 0-10 arası otomatik hesaplanan puan (penalty sistemi)

**Notlar:**

v2.0 ile eklediğimiz en önemli özelliklerden biri Security Deep Scan. Her PR review'ında AI, OWASP Top 10 framework'ünü kullanarak kapsamlı bir güvenlik analizi yapıyor.

A1'den A10'a kadar tüm kategoriler kapsanıyor. SQL injection, broken authentication, sensitive data exposure, XSS, insecure deserialization ve daha fazlası. AI sadece pattern matching yapmıyor, bağlamı da anlıyor. Mesela bir string interpolation gördüğünde, bunun bir SQL sorgusu içinde mi yoksa bir log mesajında mı olduğunu ayırt edebiliyor.

Bunun yanında Secret Leak Detection var. Kodda hardcoded API key, password, connection string, private key gibi sensitive bilgileri tarayıp CRITICAL olarak raporluyor. AWS key formatı, GCP key formatı gibi bilinen pattern'leri de tanıyor.

Her review sonrası otomatik bir security score hesaplanıyor: 10 üzerinden başlıyor, critical issue başına 4, high başına 2, medium başına 1 puan düşüyor. Bu score PR comment'te badge olarak görünüyor. Eğer secret leak tespit edildiyse ayrı bir kırmızı badge da ekleniyor.

Her issue'nun OWASP ID'si ve mümkünse CWE ID'si de var — A1, CWE-89 gibi. Bu da kurumsal raporlama ve compliance açısından çok değerli.

---

## Slayt 7 — AI Slop Detection

**Tespit edilen 8 pattern:**

| Pattern | Örnek |
|---------|-------|
| Gereksiz yorum | `// Initialize the variable` |
| Generic isim | `data`, `result`, `temp`, `item` |
| Boilerplate bloat | Framework'ün yaptığı tekrar |
| Copy-paste bloklar | Refactor edilmemiş tekrar |
| Catch-all exception | `except Exception` |
| Hallucinated API | Var olmayan method kullanımı |
| TODO/FIXME scaffold | `// TODO: implement this` |
| Tutarsız pattern | Aynı dosyada callback + async |

**Kural:** AI Slop = max MEDIUM severity. Merge'ü asla engellemez.

**Notlar:**

İkinci büyük yenilik AI Slop Detection. Şimdi hepimiz Copilot kullanıyoruz, ChatGPT'ye kod yazdırıyoruz. Bu araçlar harika ama kontrolsüz bırakıldığında "slop" kod üretiyorlar. Teknik olarak çalışıyor ama bakım maliyetini feci artırıyor.

Ne demek slop kod? Mesela kodu aynen tekrar eden yorumlar: "Initialize the variable" — bunu zaten kodu okuyan herkes görüyor, bilgi değeri sıfır. Ya da her yere "data", "result", "temp" gibi generic değişken isimleri. Copy-paste ile yapılmış tekrar eden bloklar — bir loop veya helper function ile çözülebilecek şeyler. AI'ın uydurduğu, aslında o framework'te var olmayan API çağrıları, yani hallucinated API'lar. Ve tabii TODO: implement this gibi tamamlanmamış iskelet kodlar.

Sistemimiz bu 8 pattern'i otomatik tespit ediyor. Ama çok önemli bir tasarım kararı aldık: AI Slop sorunları asla merge'ü engellemez. Maximum severity MEDIUM. Bunlar bilgilendirme amaçlı kalite uyarıları. Çünkü bir generic değişken ismi yüzünden PR'ı bloklamak doğru değil. AI yanlışlıkla bir slop issue'ya critical derse bile, biz post-processing'de bunu otomatik olarak medium'a düşürüyoruz. Bu şekilde geliştiricilere faydalı geri bildirim veriyoruz ama iş akışını engellemiyoruz.

---

## Slayt 8 — Live Dashboard

**4 Sayfa:**

| Sayfa | İçerik |
|-------|--------|
| PR Runs | Aktif/tamamlanan review kartları, stat özeti |
| Run Detail | Timeline view, adım adım review süreci |
| Analytics | Metrikler, grafikler, trendler |
| Settings | Template seçici, AI provider, config |

**Tech:** React + TypeScript + Vite | Polling-based | Pure CSS design system

**Notlar:**

Projenin önceki versiyonunda review sürecini takip etmek zordu. Sadece konsol loglarına bakabiliyordunuz. v2.0 ile tam donanımlı bir React dashboard ekledik.

Dashboard dört sayfadan oluşuyor. Ana sayfa PR Runs — burada aktif ve tamamlanan tüm review'ları kart formatında görüyorsunuz. Her kartın üzerinde PR numarası, başlığı, author, platform, branch bilgisi, score ve issue sayısı var. Status badge'leri renk kodlu: yeşil running, mavi done, kırmızı error.

Bir karta tıkladığınızda Run Detail sayfasına gidiyorsunuz. Burada review sürecini timeline view olarak adım adım izleyebiliyorsunuz: webhook alındı, diff çekildi, AI inceleme başladı, yorum gönderildi, status güncellendi. Her adım renk kodlu — mavi devam ediyor, yeşil başarılı, kırmızı hata.

Üstte sticky bir navigation bar var: PR Runs, Analytics, Settings. Tüm sayfalarda tutarlı. Responsive tasarım, mobilde de düzgün çalışıyor.

Teknik olarak React + TypeScript + Vite kullanıyoruz. Backend ile iletişim REST API üzerinden polling ile sağlanıyor. CSS tamamen custom, herhangi bir UI framework'e bağımlılık yok.

---

## Slayt 9 — Review Analytics

**9 Temel Metrik:**

Total Reviews · Avg Score · Avg Security Score · Total Issues · Critical Count · Security Issues · AI Slop Count · Blocked Merges · Secret Leaks

**4 Analiz Modülü:**

- Score Trend — PR bazında kalite ve güvenlik puanı grafiği
- Security Breakdown — OWASP dağılımı, threat types
- Top Issue Categories — En sık sorunlar bar chart
- Author Stats — Geliştirici bazlı istatistikler

**Notlar:**

Analytics sayfası, tüm review verilerini bir araya getirip anlamlı metrikler sunuyor. Buradaki temel sorumuz şu: "Ekibimiz nasıl gidiyor? Kod kalitemiz iyileşiyor mu kötüleşiyor mu?"

Üstte 9 stat kartı var: toplam review sayısı, ortalama kalite ve güvenlik puanları, toplam issue sayısı, critical sayısı, güvenlik sorunları, AI slop sayısı, merge engellenen PR sayısı ve secret leak sayısı. Bunlar tek bakışta genel durumu gösteriyor.

Altında dört analiz modülü var. Score Trend PR bazında kalite ve güvenlik puanlarını grafik olarak gösteriyor — zaman içinde iyileşme veya kötüleşmeyi hemen fark ediyorsunuz. Security Breakdown OWASP kategorilerini ve threat type'larını bar chart olarak görselleştiriyor — mesela en çok A1 Injection mı yoksa A5 Broken Access Control mı çıkıyor, bunu görüyorsunuz. Top Issue Categories en sık karşılaşılan sorun tiplerini gösteriyor. Author Stats tablosu da geliştirici bazında review sayısını, ortalama puanını, toplam issue sayısını ve kaç kez merge'ünün engellendiğini listeliyor.

Bu veriler şu an in-memory tutuluyor, sunucu restart'ta sıfırlanıyor. Ama roadmap'te persistent storage ile kalıcı hale getirmeyi planlıyoruz.

---

## Slayt 10 — Settings & Template Seçici

**3 Template:**

| Template | Hedef Kitle |
|----------|------------|
| Default (Compact) | Geliştiriciler — özet, badge, collapsible |
| Detailed | QA / Tüm ekip — satır bazlı, full context |
| Executive (Visual) | Tech Lead — badge-heavy, risk analizi |

**Diğer Ayarlar:** AI Provider + Model · Comment Strategy · Focus Areas · Poll Interval

**Hot-swap:** Seçim anında uygulanır, restart gerekmez.

**Notlar:**

Settings sayfası üzerinden tüm review parametrelerini runtime'da değiştirebiliyorsunuz. En önemli özellik template seçici. Üç hazır template arasında radio button ile geçiş yapıyorsunuz.

Default template kompakt bir format — geliştiriciler için ideal. Badge'ler, kısa bir issue tablosu ve açılır-kapanır detaylar içeriyor. Detailed template tam code-level feedback veriyor — her sorunun dosya yolu, satır numarası, kod snippet'i ve önerisi detaylı açılıyor. Executive template ise tech lead'ler ve yöneticiler için tasarlandı — daha çok badge, risk tablosu ve genel durum özeti ağırlıklı.

Template değiştirdiğinizde Save diyorsunuz, backend anında CommentService'i yeniden oluşturuyor. Sunucu restart'a gerek yok. Bir sonraki webhook'ta seçili template ile yorum oluşturuluyor. Ayar config.overrides.yaml dosyasına persist ediliyor, yani sunucu kapanıp açılsa bile seçiminiz korunuyor.

Bunun dışında AI provider ve modelini de buradan değiştirebiliyorsunuz. Comment strategy'yi summary, inline veya both olarak seçebiliyorsunuz. Focus areas'ı özelleştirebiliyorsunuz. Dashboard'un polling interval'ini ayarlayabiliyorsunuz.

---

## Slayt 11 — Platform Desteği

**4 Platform, Tek Endpoint:**

| Platform | Auth | Durum |
|----------|------|-------|
| GitHub | Bearer Token | ✅ |
| GitLab | Private Token | ✅ |
| Bitbucket | App Password | ✅ |
| Azure DevOps | PAT | ✅ |

**Otomatik tespit:** HTTP header'lardan platform algılama

**Tam özellik seti:** Diff çekme · Summary yorum · Inline yorum · Status güncelleme · Merge bloklama

**Notlar:**

Sistemin en güçlü yanlarından biri platform bağımsızlığı. Dört büyük platformu destekliyoruz: GitHub, GitLab, Bitbucket ve Azure DevOps. Ama hepsi tek bir webhook endpoint'i kullanıyor: /webhook.

Nasıl çalışıyor? Her platform kendine özgü HTTP header'ları gönderiyor. GitHub X-GitHub-Event gönderiyor, GitLab X-Gitlab-Event, Bitbucket X-Event-Key, Azure X-VSS-ActivityId. Sistem gelen isteğin header'ına bakıyor ve platformu otomatik tespit ediyor. Eğer hiçbir header bulamazsa payload yapısından da çıkarım yapabiliyor.

Her platform için tam özellik seti var: diff çekme, summary yorum yazma, satır bazlı inline yorum, PR status güncelleme ve merge bloklama. Dördü de aynı seviyede destekleniyor.

Mimari açıdan baktığınızda, her platform için bir adapter sınıfı var ve hepsi BasePlatformAdapter abstract class'ından türüyor. Yeni bir platform eklemek istediğinizde sadece yeni bir adapter yazıyorsunuz. Mevcut iş mantığı hiç değişmiyor. Bu da open-closed principle'ın güzel bir uygulaması.

---

## Slayt 12 — AI Provider Sistemi

| Provider | Model | Hız | Maliyet |
|----------|-------|:---:|:-------:|
| Groq | Llama 3.3 70B | Çok hızlı | Ücretsiz/düşük |
| OpenAI | GPT-4o, GPT-4o-mini | Orta | Orta |
| Anthropic | Claude 3.5 Sonnet | Orta | Orta-yüksek |

**3 yolla değiştirilebilir:** config.yaml · UI Settings · MCP Tool override

**Notlar:**

Üç farklı AI provider'ı destekliyoruz ve hepsi aynı abstract interface'den türüyor. Factory pattern ile isimden instance oluşturuluyor, strategy pattern ile runtime'da geçiş yapılabiliyor.

Groq önerimiz günlük yüksek hacimli kullanım için. Llama 3.3 70B modeli inanılmaz hızlı — 5-15 saniye içinde review tamamlanıyor. Ve maliyeti neredeyse sıfır. OpenAI'ı karmaşık kod analizi için öneriyoruz, GPT-4o modeli daha derinlemesine anlıyor. Anthropic'in Claude 3.5 Sonnet modeli özellikle güvenlik analizi konusunda çok başarılı.

Provider değiştirmek üç şekilde mümkün: config.yaml'da provider ve model alanını değiştirerek, UI Settings sayfasından dropdown ile seçerek ya da MCP tool çağrısında runtime override yaparak. Üçü de sunucu yeniden başlatmaya gerek kalmadan çalışıyor. Vendor lock-in diye bir şey yok — yarın yeni bir AI provider çıksa, interface'i implemente edip config'e eklemeniz yeterli.

---

## Slayt 13 — Dil Tespiti & Rule Sistemi

**25+ dil:** C# · Java · Python · TypeScript · Go · Rust · Swift · Kotlin · ve dahası

**19 rule dosyası:** Markdown tabanlı, Git ile versiyonlanan

**AI ile otomatik rule üretimi:** Yeni dil geldiğinde RuleGenerator devreye girer

**Notlar:**

Sistem 25'ten fazla programlama dilini otomatik tespit edebiliyor. PR'daki dosya uzantılarına bakarak en baskın dili çıkarıyor. Mesela 5 tane .cs dosyası ve 2 tane .json dosyası varsa, sonuç C#.

Dil tespiti neden önemli? Çünkü dile özel kurallarımız var. Rules klasöründe 19 markdown dosyası var. Genel kurallar: compilation.md, security.md, performance.md, best-practices.md. Ve dile özel versiyonları: csharp-compilation.md, python-security.md, go-performance.md gibi. Bu kurallar AI prompt'una bağlam olarak ekleniyor. C# kodu incelenirken Python kuralları uygulanmıyor, bu false positive'leri ciddi ölçüde azaltıyor.

En güzel özelliklerden biri de otomatik rule üretimi. Diyelim ilk kez Rust dilinde bir PR geldi. Sistem rust-security.md dosyasını arıyor, bulamıyor. Bu durumda RuleGenerator devreye giriyor: genel security.md şablonunu alıyor, AI'a veriyor ve "bunu Rust diline özel olarak yeniden yaz" diyor. Üretilen dosya kaydediliyor ve bir sonraki Rust review'ında hazır. Yani sistem kendini genişletiyor.

---

## Slayt 14 — Short-Circuit & Severity

**Short-Circuit:** Compilation hatası bulunursa diğer tüm kontroller durur.

**5 Severity:** CRITICAL → HIGH → MEDIUM → LOW → INFO

**Merge bloklama:** Critical issue = failure status = merge engellenir

**Notlar:**

Short-circuit mekanizması akıllı bir önceliklendirme stratejisi. Mantık basit: eğer kodda syntax hatası veya compilation hatası varsa, o kod zaten çalışmayacak. Dolayısıyla güvenlik analizi, performans kontrolü, AI slop tespiti yapmanın bir anlamı yok. Sistem compilation hatası bulduğu anda diğer kontrolleri atlıyor ve sadece compilation sorunlarını raporluyor.

Bunu iki katmanda garanti ediyoruz. Birincisi AI prompt'una açık talimat veriyoruz: "compilation hatası bulursan dur, başka bir şey kontrol etme." İkincisi, AI'dan gelen yanıtı programatik olarak filtreliyoruz. Yani AI talimata uymasa bile, post-processing'de sadece compilation issue'ları bırakıyoruz.

Severity sistemi beş kademeli: critical, high, medium, low, info. Critical issue bulunduğunda PR status'u failure olarak işaretleniyor. Eğer repoda branch protection aktifse, merge otomatik engelleniyor. Geliştirici düzeltmeyi yapıp push ettiğinde yeni bir review tetikleniyor ve cycle tekrar başlıyor.

---

## Slayt 15 — Template Sistemi

**4 Template:**

| Template | Hedef |
|----------|-------|
| Default | Kompakt — badge, issue table, collapsible |
| Detailed | Dosya bazlı — kod snippet, severity matrix |
| Executive | Görsel — badge-heavy, risk tablosu |
| Custom | Kullanıcı tanımlı markdown şablon |

**v2.0 eklentileri:** AI Slop Badge · Security Score Badge · Secret Leak Badge · OWASP tablo · AI Slop detay bölümü

**Notlar:**

PR'a yazılan review yorumunun formatı template sistemi ile yönetiliyor. Dört seçenek var.

Default template geliştiriciler için tasarlandı. Kompakt ve okunması hızlı. Üstte badge'ler — score, security, issue sayısı — altta bir issue tablosu ve her sorunun detayı collapsible olarak. Detailed template QA ekibi ve kapsamlı review isteyenler için. Dosya bazlı dağılım, her sorunun tam kodu, severity matrix dahil. Executive template tech lead'ler ve yöneticiler için — shield badge'leri ağırlıklı, risk analizi, tech debt tahmini, genel durum özeti.

v2.0 ile tüm template'lere yeni bölümler ekledik: AI Slop badge'i ve detay tablosu, Security Score badge'i, secret leak badge'i ve OWASP tabanlı güvenlik bölümü. Hangi template'i seçerseniz seçin, bu bilgiler otomatik olarak yoruma dahil ediliyor.

Bir de Custom template var. custom_templates klasörüne kendi markdown dosyanızı koyabiliyorsunuz. Placeholder'larla çalışıyor: {score}, {total_issues}, {issues_list} gibi. Kendi takımınıza özel format tanımlayabilirsiniz.

---

## Slayt 16 — MCP & IDE Entegrasyonu

**3 MCP Tool:**

| Tool | Açıklama |
|------|----------|
| review_code | Kod parçacığını AI ile incele |
| analyze_diff | Diff istatistikleri çıkar |
| security_scan | Güvenlik odaklı tarama |

**Endpoint:** `GET /mcp/sse` (Server-Sent Events)

**Desteklenen IDE:** Claude Desktop · Cursor · VS Code · Windsurf

**Notlar:**

Webhook tabanlı otomatik review dışında, bir de IDE entegrasyonu var. MCP yani Model Context Protocol — Anthropic tarafından geliştirilen açık bir standart. AI modellerinin harici araçlarla iletişim kurmasını sağlıyor.

Sunucumuz SSE endpoint'i üzerinden MCP client'lara bağlanıyor. Üç tool sunuyoruz: review_code ile seçili bir kod parçacığını AI'a review ettirebiliyorsunuz, analyze_diff ile bir diff'in istatistiklerini çıkarabiliyorsunuz, security_scan ile sadece güvenlik odaklı tarama yapabiliyorsunuz.

Bu ne işe yarıyor? PR açmadan önce bile kodunuzu kontrol edebiliyorsunuz. Cursor'da veya VS Code'da kod yazarken MCP tool'u çağırıyorsunuz, saniyeler içinde AI geri bildirim veriyor. Bir nevi pre-review imkanı. Ve burada provider override da yapabiliyorsunuz — mesela normalde Groq kullanıyorsunuz ama güvenlik taraması için Claude'u tercih etmek istiyorsunuz, tool çağrısında belirtmeniz yeterli.

---

## Slayt 17 — API Endpoint Referansı

**20+ endpoint:**

| Kategori | Endpoints |
|----------|-----------|
| Core | Health check · Webhook · MCP SSE |
| Config | GET/PUT config · Template list/switch |
| Rules | List · Resolve · Get content |
| Live Logs | Config · Active · All runs · Run events |
| Analytics | Overview · Trend · Top issues · Security · Authors · Recent |
| UI | SPA index · SPA routing |

**Notlar:**

Sistemde toplam 20'den fazla REST API endpoint'i var. Bunları kategorilere ayırabiliriz.

Core endpoint'ler: health check, webhook alımı ve MCP SSE bağlantısı. Config endpoint'leri: GET ile mevcut config'i okuyorsunuz, PUT ile güncelliyorsunuz. Template listesi ve runtime template switch de burada. Rules endpoint'leri: kural dosyalarını listeleme, focus area ve dile göre çözümleme ve belirli bir kuralın içeriğini getirme.

Live Logs endpoint'leri dashboard için: logs config, aktif run'lar, tüm run'lar ve belirli bir run'ın event'leri — bu cursor-based pagination ile çalışıyor. Analytics endpoint'leri: overview, score trend, top issues, security breakdown, author stats ve recent reviews. Son olarak UI endpoint'leri: React SPA'yı serve ediyor.

Tüm bu endpoint'ler FastAPI üzerinde çalışıyor, otomatik OpenAPI/Swagger dokümantasyonu var. localhost:8000/docs adresinden interactive olarak test edebilirsiniz.

---

## Slayt 18 — CodeRabbit Karşılaştırma

| Özellik | CodeRabbit | MCP Server |
|---------|:----------:|:----------:|
| Platform | 2 | **4** |
| AI Provider | Sabit | **3, değiştirilebilir** |
| OWASP Scan | ✗ | **✓** |
| AI Slop | ✗ | **✓** |
| Live Dashboard | ✗ | **✓** |
| Analytics | Temel | **Full** |
| Template | 1 | **4 + custom** |
| IDE (MCP) | ✗ | **✓** |
| Self-hosted | ✗ | **✓** |
| Open Source | ✗ | **✓** |

**Maliyet (10 kişi/yıl):** CodeRabbit $2,880 → MCP Server ~$300-840 **(% 70-90 tasarruf)**

**Notlar:**

Piyasanın en bilinen rakibi CodeRabbit ile karşılaştıralım. Tablodaki farklar ortada ama birkaç kritik noktayı vurgulayalım.

Platform desteği: CodeRabbit sadece GitHub ve GitLab destekliyor. Biz dört platform. Yani Bitbucket veya Azure DevOps kullanan bir ekipseniz CodeRabbit'i kullanamazsınız bile.

AI provider: CodeRabbit kendi sabit modelini kullanıyor, değiştirme imkanı yok. Biz üç farklı provider sunuyoruz ve runtime'da değiştirilebilir. OWASP tabanlı security scan, AI slop detection, live dashboard, analytics, template sistemi — bunların hiçbiri CodeRabbit'te yok.

Ve en önemlisi: maliyet. 10 kişilik bir ekip için CodeRabbit yılda 2,880 dolar. Bizim çözümde ise sadece AI API maliyeti ve küçük bir sunucu maliyeti var — yıllık 300-840 dolar arası. Bu %70 ile %90 arasında tasarruf demek. 50 kişilik bir ekipte bu fark 13,000 doların üzerine çıkıyor.

Ve veri gizliliği meselesi var. CodeRabbit'te kodunuz 3. parti sunuculara gidiyor. Self-hosted çözümde her şey kendi kontrolünüzde.

---

## Slayt 19 — Canlı Demo

**Senaryo:** GitHub'da açılan bir PR → AI Review → PR'a yorum

**Konsol çıktısı (özetlenmiş):**

```
🔔 WEBHOOK → 📦 GITHUB → PR #42: Add auth module
📥 Diff: 4,120 bytes → 4 dosya
🤖 AI Review: Score 5/10
   🔴 1 Critical (SQL Injection — A1)
   🟠 1 High (Missing CSRF — A5)
   🟡 2 Medium (AI Slop)
💬 Summary comment posted
❌ MERGE BLOCKED
```

**PR'da görünen yorum:** Quality 5/10 · Security 4/10 · AI Slop 2 · Merge BLOCKED

**Notlar:**

Şimdi canlı bir senaryo üzerinden gidelim. Bir geliştirici GitHub'da PR açıyor: "Add user authentication module". feature/auth branch'inden main'e.

Konsol çıktısında görebiliyorsunuz: webhook alındı, platform GitHub olarak tespit edildi. Diff çekildi — 4,120 byte, 4 dosya değişmiş. AI review başladı, Groq provider ile Llama 3.3 modeli kullanılıyor.

Sonuç: 5/10 score. 6 issue bulundu. Bunlardan 1 tanesi critical — SQL injection, OWASP A1. 1 tanesi high — missing CSRF protection, OWASP A5. 2 tanesi medium — AI slop, gereksiz yorumlar. 2 tanesi de low seviyede.

PR'a giden yorum executive template formatında: üstte badge'ler — Quality 5/10 kırmızı, Security 4/10 kırmızı, AI Slop 2 found turuncu, Merge BLOCKED kırmızı. Altta OWASP tablosu ve AI slop tablosu. Geliştirici SQL injection'ı düzeltip push ettiğinde yeni review tetiklenir, score artar ve merge açılır.

---

## Slayt 20 — Sayılarla Proje

| Metrik | Değer |
|--------|-------|
| Platform | 4 |
| AI Provider | 3 |
| Programlama Dili | 25+ |
| Rule Dosyası | 19 |
| PR Template | 4 + custom |
| MCP Tool | 3 |
| OWASP Kategori | 10 |
| AI Slop Pattern | 8 |
| API Endpoint | 20+ |
| UI Sayfası | 4 |
| Kaynak Dosya | 40+ |

**Notlar:**

Projenin sayısal büyüklüğüne bakalım. 4 platform desteği, 3 AI provider, 25'ten fazla programlama dili desteği, 19 review kuralı dosyası, 4 hazır template artı custom template imkanı, 3 MCP tool, OWASP Top 10'un 10 kategorisinin tamamı, 8 AI slop pattern, 20'den fazla API endpoint, 4 UI sayfası ve 40'tan fazla kaynak dosya. Python ve TypeScript ile modüler mimari.

Bütün bunlar tek bir Docker container'da çalışıyor. Image boyutu yaklaşık 150 megabyte. Bir VPS'e deploy edip webhook URL'ini ayarlamak dakikalar alıyor.

---

## Slayt 21 — Değer Önerisi

| Boyut | Etki |
|-------|------|
| Maliyet | %70-90 tasarruf |
| Zaman | Manuel review %60-80 azalır |
| Güvenlik | OWASP + Secret Leak proaktif tarama |
| AI Kalitesi | Düşük kalite AI kodu otomatik tespit |
| Görünürlük | Dashboard + Analytics ile veri odaklı kararlar |
| Esneklik | 4 platform, 3 AI, 25+ dil, 4 template |
| Gizlilik | Self-hosted, kod şirket dışına çıkmaz |

**Notlar:**

Sonuç olarak bu projenin değer önerisini özetleyelim. Maliyet tarafında rakiplere göre %70-90 arası tasarruf. Zaman tarafında manuel review süresi %60-80 oranında azalıyor — geliştirici review'a değil, üretime odaklanıyor.

Güvenlik tarafında OWASP Top 10 ve secret leak detection ile proaktif güvenlik taraması — sorunlar merge'den önce yakalanıyor. AI kalitesi tarafında slop detection ile ekiplerin AI araçlarını bilinçli kullanması sağlanıyor. Görünürlük tarafında live dashboard ve analytics ile veri odaklı kararlar alınıyor — hangi sorunlar tekrar ediyor, kod kalitesi iyileşiyor mu, kim en çok bloklanıyor gibi soruların cevabı var.

Esneklik tarafında tek çözüm dört platformu, üç AI provider'ı, 25'ten fazla dili ve dört farklı template'i destekliyor. Ve en kritik konu: veri gizliliği. Self-hosted yapı sayesinde kodunuz asla şirket dışına çıkmıyor. GDPR, KVKK uyumlu.

---

## Slayt 22 — Roadmap

**Kısa vade (Q2 2026):**
- Kategori bazlı model seçimi (Security → Claude, Compilation → GPT-4)
- Persistent analytics (SQLite/PostgreSQL)
- Notification hub (Slack, Teams)

**Orta vade (Q3-Q4 2026):**
- IDE eklentileri (VS Code, IntelliJ)
- Team-based rules (RBAC)
- Akıllı caching & incremental review

**Uzun vade (2027):**
- Learning from feedback (👍/👎)
- Multi-tenant SaaS

**Notlar:**

İleriye dönük planlarımız var. Kısa vadede — bu çeyrek içinde — kategori bazlı model seçimi üzerinde çalışıyoruz. Fikir şu: güvenlik taraması için Claude'u kullan çünkü güvenlik konusunda çok iyi, compilation kontrolü için GPT-4'ü kullan çünkü syntax anlama konusunda güçlü, genel review için Groq'u kullan çünkü hızlı ve ucuz. Ayrıca analytics verilerini şu an in-memory tutuyoruz, bunu SQLite veya PostgreSQL ile kalıcı hale getireceğiz. Slack ve Teams notification entegrasyonu da bu dönemde gelecek.

Orta vadede IDE eklentileri planlıyoruz — VS Code ve IntelliJ için native extension'lar. Team-based rules ile farklı takımların farklı kural setleri olabilecek. Akıllı caching ile benzer pattern'leri tekrar AI'a göndermeden cache'den çözeceğiz.

Uzun vadede feedback loop mekanizması — geliştiriciler AI yorumlarına 👍 veya 👎 veriyor, sistem bunlardan öğreniyor, false positive oranı düşüyor. Ve en son multi-tenant SaaS modeli ile birden fazla organizasyonu tek platform üzerinden destekleme.

---

## Slayt 23 — Soru-Cevap

**Sık Sorulan Sorular**

- Review süresi ne kadar? → 10-30 saniye (Groq ile 5-15 sn)
- AI Slop merge'ü engelliyor mu? → Hayır, max severity MEDIUM
- Security scan SAST yerine geçer mi? → Tamamlayıcı, ikisi birlikte kullanılabilir
- Analytics verileri kalıcı mı? → Şu an in-memory, persistent storage planlanan
- Birden fazla repo tek server? → Evet, webhook URL ayarlayın yeterli
- Yeni dil desteği? → Otomatik, RuleGenerator AI ile oluşturur

**Notlar:**

Şimdi sorularınızı alalım. Ama öncesinde en sık sorulan soruları paylaşayım.

Review ne kadar sürer? Groq ile genellikle 5 ila 15 saniye, OpenAI veya Anthropic ile 15 ila 30 saniye arası. Diff büyüklüğüne bağlı tabii ama ortalama bu.

AI Slop merge'ü engelliyor mu? Kesinlikle hayır. Bunu tasarım kararı olarak aldık. AI slop uyarıları bilgilendirme amaçlı, maximum medium severity. Merge'ü sadece critical seviye sorunlar engelliyor.

Security Deep Scan mevcut SAST araçlarının yerini alır mı? Tam olarak değil. AI tabanlı tarama geleneksel SAST'tan farklı — bağlamı anlıyor, daha az false positive üretiyor ama rule-based kesinlik açısından geleneksel araçlar hala değerli. İkisi birlikte kullanılabilir.

Birden fazla repo için tek server yeterli mi? Evet. Her repoda sadece webhook URL'ini ayarlamanız yeterli. Platform farkı da önemli değil — bir repo GitHub'da, diğeri Bitbucket'ta olabilir, ikisi de aynı server'a webhook atabilir.

Başka soruları olan varsa buyursun.

---

**Hazırlayan:** Mennano Development Team
**Versiyon:** 2.0.0 | **Mart 2026**
