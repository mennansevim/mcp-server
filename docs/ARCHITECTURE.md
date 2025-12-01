# 🏗️ MCP Code Review Server - Architecture

## 📊 Sistem Mimarisi

### Genel Akış Diyagramı

```mermaid
flowchart TB
    subgraph CICD[CI/CD Platforms]
        direction LR
        GH[GitHub Actions]
        GL[GitLab CI/CD]
        BB[Bitbucket Pipelines]
        AZ[Azure Pipelines]
    end
    
    subgraph PUBLIC[Public Access]
        NG[Ngrok Tunnel<br/>Public HTTPS URL]
    end
    
    subgraph SERVER[MCP Server - Port 8000]
        WH[Webhook Handler<br/>/webhook endpoint]
        
        subgraph DETECT[Platform Detection]
            direction TB
            PD[Platform Detector]
            GHP[GitHub Parser]
            GLP[GitLab Parser]
            BBP[Bitbucket Parser]
            AZP[Azure Parser]
        end
        
        subgraph CORE[Core Services]
            direction TB
            LD[Language Detector<br/>25+ languages]
            DA[Diff Analyzer]
            RG[Rule Generator<br/>AI-powered]
            AI[AI Reviewer<br/>Groq/Claude/GPT-4]
            CS[Comment Service]
        end
        
        subgraph ADAPT[Platform Adapters]
            direction TB
            GHA[GitHub Adapter]
            GLA[GitLab Adapter]
            BBA[Bitbucket Adapter]
            AZA[Azure Adapter]
        end
        
        subgraph RULES[Rules Engine]
            direction LR
            BR[Base Rules<br/>security.md<br/>performance.md]
            LR[Language Rules<br/>python-*.md<br/>csharp-*.md]
        end
    end
    
    subgraph APIS[External APIs]
        direction TB
        subgraph AI_APIS[AI Providers]
            GROQ[Groq API<br/>Llama 3.3]
            CLAUDE[Anthropic API<br/>Claude 3.5]
            GPT[OpenAI API<br/>GPT-4]
        end
        subgraph PLATFORM_APIS[Platform APIs]
            GHAPI[GitHub API]
            GLAPI[GitLab API]
            BBAPI[Bitbucket API]
            AZAPI[Azure DevOps API]
        end
    end
    
    GH -.->|1. webhook POST| NG
    GL -.->|1. webhook POST| NG
    BB -.->|1. webhook POST| NG
    AZ -.->|1. webhook POST| NG
    
    NG ==>|2. forward| WH
    
    WH ==>|3. parse payload| PD
    PD -->|GitHub| GHP
    PD -->|GitLab| GLP
    PD -->|Bitbucket| BBP
    PD -->|Azure| AZP
    
    GHP ==>|4. PR data| GHA
    GLP ==>|4. MR data| GLA
    BBP ==>|4. PR data| BBA
    AZP ==>|4. PR data| AZA
    
    GHA -.->|5. fetch diff| GHAPI
    GLA -.->|5. fetch diff| GLAPI
    BBA -.->|5. fetch diff| BBAPI
    AZA -.->|5. fetch diff| AZAPI
    
    GHAPI -.->|6. diff data| GHA
    GLAPI -.->|6. diff data| GLA
    BBAPI -.->|6. diff data| BBA
    AZAPI -.->|6. diff data| AZA
    
    GHA ==>|7. diff + files| LD
    GLA ==>|7. diff + files| LD
    BBA ==>|7. diff + files| LD
    AZA ==>|7. diff + files| LD
    
    LD ==>|8. detected language| RG
    LD -->|files list| DA
    DA ==>|9. parsed diff| AI
    
    BR -->|base rules| RG
    RG -->|check/generate| LR
    LR ==>|10. language rules| AI
    
    AI -.->|11. review request| GROQ
    AI -.->|11. review request| CLAUDE
    AI -.->|11. review request| GPT
    
    GROQ -.->|12. review result| AI
    CLAUDE -.->|12. review result| AI
    GPT -.->|12. review result| AI
    
    AI ==>|13. review result| CS
    CS ==>|14. format comments| GHA
    CS ==>|14. format comments| GLA
    CS ==>|14. format comments| BBA
    CS ==>|14. format comments| AZA
    
    GHA -.->|15. post comments| GHAPI
    GLA -.->|15. post comments| GLAPI
    BBA -.->|15. post comments| BBAPI
    AZA -.->|15. post comments| AZAPI
    
    GHAPI -.->|16. notify| GH
    GLAPI -.->|16. notify| GL
    BBAPI -.->|16. notify| BB
    AZAPI -.->|16. notify| AZ
    
    style WH fill:#4CAF50,stroke:#2E7D32,stroke-width:3px
    style AI fill:#2196F3,stroke:#1565C0,stroke-width:3px
    style LD fill:#FF9800,stroke:#E65100,stroke-width:3px
    style RG fill:#9C27B0,stroke:#6A1B9A,stroke-width:3px
    style NG fill:#F44336,stroke:#C62828,stroke-width:3px
    style CS fill:#00BCD4,stroke:#00838F,stroke-width:3px
```

---

## 🔄 Review Akış Detayı

```mermaid
sequenceDiagram
    autonumber
    participant Dev as Developer
    participant GH as GitHub
    participant NG as Ngrok
    participant WH as Webhook Handler
    participant AD as Platform Adapter
    participant LD as Language Detector
    participant RG as Rule Generator
    participant AI as AI Reviewer
    participant CS as Comment Service
    
    rect rgb(200, 230, 255)
        Note over Dev,GH: Developer Workflow
        Dev->>+GH: PR Acar
        GH->>+NG: Webhook POST
    end
    
    rect rgb(255, 230, 200)
        Note over NG,WH: Webhook Processing
        NG->>+WH: Forward /webhook
        Note right of WH: Platform Detection<br/>x-github-event header
        WH->>+AD: Parse & Route
    end
    
    rect rgb(200, 255, 230)
        Note over AD,LD: Data Collection
        AD->>+GH: API: Fetch Diff
        GH-->>-AD: Diff Content
        AD->>+LD: Changed Files List
        Note right of LD: Extension Analysis<br/>.cs → csharp
        LD-->>-AD: Detected: csharp
    end
    
    rect rgb(255, 240, 200)
        Note over LD,RG: Rules Preparation
        LD->>+RG: Language: csharp
        
        alt Rules Not Cached
            RG->>AI: Generate Rules
            Note right of AI: AI creates rules
            AI-->>RG: Generated Rules
            Note right of RG: Save to rules/
        else Rules Cached
            Note right of RG: Load from cache
        end
        RG-->>-LD: Rules Ready
    end
    
    rect rgb(230, 200, 255)
        Note over AI: AI Review Process
        RG->>+AI: Diff + Rules + Focus
        Note right of AI: Analyzing:<br/>Compilation<br/>Security<br/>Performance
        AI-->>-CS: Review Result
    end
    
    rect rgb(255, 200, 200)
        Note over CS,GH: Comment & Status Update
        CS->>CS: Format Comments
        
        alt Critical Issues
            CS->>AD: Summary + Inline + FAILURE
            AD->>GH: POST Comments + Block
            GH-->>Dev: PR BLOCKED
        else No Critical Issues
            CS->>AD: Summary Comment + SUCCESS
            AD->>GH: POST Comment + Approve
            GH-->>Dev: PR APPROVED
        end
    end
    
    rect rgb(200, 255, 255)
        Note over Dev: Developer Reviews Results
        Dev->>Dev: Read AI Comments
        Dev->>Dev: Fix Issues
    end
```

---

## 🧩 Component Detayları

### 1. Webhook Handler

```mermaid
flowchart LR
    A[HTTP Request<br/>POST /webhook] --> B{Headers Check}
    
    B -->|x-github-event| C[GitHub]
    B -->|x-gitlab-event| D[GitLab]
    B -->|x-event-key| E[Bitbucket]
    B -->|x-vss-activityid| F[Azure]
    B -->|Unknown| X[Error<br/>Unsupported]
    
    C --> G[GitHub Parser]
    D --> H[GitLab Parser]
    E --> I[Bitbucket Parser]
    F --> J[Azure Parser]
    
    G --> K[Unified PR Data]
    H --> K
    I --> K
    J --> K
    
    K --> L[Route to<br/>Platform Adapter]
    
    style A fill:#2196F3,stroke:#1565C0,stroke-width:3px
    style B fill:#2196F3,stroke:#1565C0,stroke-width:3px
    style C fill:#4CAF50,stroke:#2E7D32,stroke-width:2px
    style D fill:#4CAF50,stroke:#2E7D32,stroke-width:2px
    style E fill:#4CAF50,stroke:#2E7D32,stroke-width:2px
    style F fill:#4CAF50,stroke:#2E7D32,stroke-width:2px
    style G fill:#FF9800,stroke:#E65100,stroke-width:2px
    style H fill:#FF9800,stroke:#E65100,stroke-width:2px
    style I fill:#FF9800,stroke:#E65100,stroke-width:2px
    style J fill:#FF9800,stroke:#E65100,stroke-width:2px
    style K fill:#9C27B0,stroke:#6A1B9A,stroke-width:3px
    style L fill:#4CAF50,stroke:#2E7D32,stroke-width:3px
    style X fill:#F44336,stroke:#C62828,stroke-width:2px
```

### 2. Language Detection

```mermaid
flowchart TD
    A[Changed Files List] --> B[Filter Config Files]
    
    B --> C{Parse Extensions}
    
    C -->|.py| PY[Python]
    C -->|.cs, .csx| CS[C#]
    C -->|.js, .jsx, .ts, .tsx| JS[JavaScript/TypeScript]
    C -->|.java, .kt, .scala| JV[Java/Kotlin/Scala]
    C -->|.go| GO[Go]
    C -->|.rs| RS[Rust]
    C -->|.php| PHP[PHP]
    C -->|.rb| RB[Ruby]
    C -->|25+ more...| MORE[Others]
    
    PY --> COUNT[Count by Language]
    CS --> COUNT
    JS --> COUNT
    JV --> COUNT
    GO --> COUNT
    RS --> COUNT
    PHP --> COUNT
    RB --> COUNT
    MORE --> COUNT
    
    COUNT --> MOST{Most Common?}
    
    MOST -->|max count| RESULT[Detected Language]
    
    RESULT --> LOG[Log Detection]
    
    LOG --> RETURN[Return to<br/>Rule Generator]
    
    style A fill:#2196F3,stroke:#1565C0,stroke-width:3px
    style B fill:#2196F3,stroke:#1565C0,stroke-width:3px
    style PY fill:#FF9800,stroke:#E65100,stroke-width:2px
    style CS fill:#FF9800,stroke:#E65100,stroke-width:2px
    style JS fill:#FF9800,stroke:#E65100,stroke-width:2px
    style JV fill:#FF9800,stroke:#E65100,stroke-width:2px
    style GO fill:#FF9800,stroke:#E65100,stroke-width:2px
    style RS fill:#FF9800,stroke:#E65100,stroke-width:2px
    style PHP fill:#FF9800,stroke:#E65100,stroke-width:2px
    style RB fill:#FF9800,stroke:#E65100,stroke-width:2px
    style MORE fill:#FF9800,stroke:#E65100,stroke-width:2px
    style COUNT fill:#4CAF50,stroke:#2E7D32,stroke-width:2px
    style MOST fill:#4CAF50,stroke:#2E7D32,stroke-width:2px
    style RESULT fill:#9C27B0,stroke:#6A1B9A,stroke-width:3px
    style LOG fill:#9C27B0,stroke:#6A1B9A,stroke-width:3px
    style RETURN fill:#9C27B0,stroke:#6A1B9A,stroke-width:3px
```

### 3. Rule Generator

```mermaid
flowchart TD
    START[Input<br/>Language: csharp<br/>Categories] --> CHECK{Check Cache<br/>Rules exist?}
    
    CHECK -->|Yes| LOAD[Load from Cache<br/>Fast! No AI call]
    
    CHECK -->|No| GEN[Generate New Rules]
    
    GEN --> BASE[Load Base Rules<br/>security.md<br/>performance.md]
    
    BASE --> PROMPT[Build AI Prompt<br/>Adapt rules for C#]
    
    PROMPT --> AI_CALL[Call AI Provider<br/>Groq/Claude/GPT]
    
    AI_CALL --> RESPONSE[AI Response<br/>Generated markdown]
    
    RESPONSE --> SAVE[Save Rule Files<br/>rules/csharp-*.md]
    
    SAVE --> LOAD
    
    LOAD --> COMBINE[Combine Rules<br/>Base + Language]
    
    COMBINE --> OUTPUT[Output<br/>Complete Rule Set]
    
    OUTPUT --> NEXT[Feed to<br/>AI Reviewer]
    
    style START fill:#2196F3,stroke:#1565C0,stroke-width:3px
    style CHECK fill:#4CAF50,stroke:#2E7D32,stroke-width:3px
    style LOAD fill:#4CAF50,stroke:#2E7D32,stroke-width:3px
    style GEN fill:#FF9800,stroke:#E65100,stroke-width:3px
    style BASE fill:#FF9800,stroke:#E65100,stroke-width:3px
    style PROMPT fill:#FF9800,stroke:#E65100,stroke-width:3px
    style AI_CALL fill:#9C27B0,stroke:#6A1B9A,stroke-width:3px
    style RESPONSE fill:#9C27B0,stroke:#6A1B9A,stroke-width:3px
    style SAVE fill:#00BCD4,stroke:#00838F,stroke-width:3px
    style COMBINE fill:#FFEB3B,stroke:#F57F17,stroke-width:3px
    style OUTPUT fill:#FFEB3B,stroke:#F57F17,stroke-width:3px
    style NEXT fill:#FFEB3B,stroke:#F57F17,stroke-width:3px
```

### 4. AI Reviewer

```mermaid
flowchart TD
    START[Review Request<br/>Diff + Files + Language] --> PREP[Prepare Prompt]
    
    PREP --> BUILD[Build Context<br/>Diff + Rules + Focus]
    
    BUILD --> PROVIDER{Select AI Provider}
    
    PROVIDER -->|groq| GROQ[Groq API<br/>Llama 3.3<br/>Fast & Free]
    
    PROVIDER -->|anthropic| CLAUDE[Anthropic API<br/>Claude 3.5<br/>High Quality]
    
    PROVIDER -->|openai| GPT[OpenAI API<br/>GPT-4<br/>Standard]
    
    GROQ --> RESPONSE[AI Response<br/>JSON format]
    
    CLAUDE --> RESPONSE
    GPT --> RESPONSE
    
    RESPONSE --> PARSE[Parse JSON<br/>Extract data]
    
    PARSE --> VALIDATE{Validation<br/>Valid JSON?}
    
    VALIDATE -->|Invalid| ERROR[Error Handling<br/>Safe default]
    
    VALIDATE -->|Valid| NORMALIZE[Normalize Data<br/>Lowercase severity]
    
    NORMALIZE --> ISSUES{Analyze Issues<br/>Count by severity}
    
    ISSUES --> CRITICAL{Critical Issues?}
    
    CRITICAL -->|Yes| BLOCK[Set Flags<br/>block_merge=true]
    
    CRITICAL -->|No| SCORE{Check Score<br/>score >= 8?}
    
    SCORE -->|Yes| APPROVE[Approve<br/>block_merge=false]
    
    SCORE -->|No| WARN[Warning<br/>block_merge=false]
    
    BLOCK --> RESULT[Create ReviewResult]
    APPROVE --> RESULT
    WARN --> RESULT
    ERROR --> RESULT
    
    RESULT --> LOG[Log Results]
    
    LOG --> OUTPUT[Return to<br/>Comment Service]
    
    style START fill:#2196F3,stroke:#1565C0,stroke-width:3px
    style PREP fill:#00BCD4,stroke:#00838F,stroke-width:2px
    style BUILD fill:#00BCD4,stroke:#00838F,stroke-width:2px
    style PROVIDER fill:#9C27B0,stroke:#6A1B9A,stroke-width:3px
    style RESPONSE fill:#9C27B0,stroke:#6A1B9A,stroke-width:3px
    style PARSE fill:#9C27B0,stroke:#6A1B9A,stroke-width:3px
    style GROQ fill:#FF6B35,stroke:#D84315,stroke-width:3px
    style CLAUDE fill:#6A5ACD,stroke:#483D8B,stroke-width:3px
    style GPT fill:#10A37F,stroke:#0A7A5D,stroke-width:3px
    style VALIDATE fill:#4CAF50,stroke:#2E7D32,stroke-width:2px
    style NORMALIZE fill:#4CAF50,stroke:#2E7D32,stroke-width:2px
    style ISSUES fill:#4CAF50,stroke:#2E7D32,stroke-width:2px
    style CRITICAL fill:#4CAF50,stroke:#2E7D32,stroke-width:2px
    style SCORE fill:#4CAF50,stroke:#2E7D32,stroke-width:2px
    style ERROR fill:#F44336,stroke:#C62828,stroke-width:2px
    style BLOCK fill:#FFEB3B,stroke:#F57F17,stroke-width:3px
    style APPROVE fill:#FFEB3B,stroke:#F57F17,stroke-width:3px
    style WARN fill:#FFEB3B,stroke:#F57F17,stroke-width:3px
    style RESULT fill:#FFEB3B,stroke:#F57F17,stroke-width:3px
    style LOG fill:#FFEB3B,stroke:#F57F17,stroke-width:3px
    style OUTPUT fill:#FFEB3B,stroke:#F57F17,stroke-width:3px
```

### 5. Comment Service

```mermaid
flowchart TD
    INPUT[Review Result<br/>score + issues] --> STRATEGY{Comment Strategy}
    
    STRATEGY -->|summary| SUMMARY[Format Summary Only]
    STRATEGY -->|inline| INLINE[Format Inline Only]
    STRATEGY -->|both| BOTH[Format Both]
    
    BOTH --> SUMMARY
    BOTH --> INLINE
    
    SUMMARY --> BUILD_SUM[Build Summary Comment<br/>Score + Issues + Critical list]
    
    BUILD_SUM --> BRANCH{Check Target Branch<br/>In detailed_branches?}
    
    BRANCH -->|Yes - main/master/prod| TABLE[Add Detailed Table<br/>Severity x Type Matrix]
    
    BRANCH -->|No - feature/develop| SKIP[Skip Detailed Table]
    
    TABLE --> FINAL_SUM[Final Summary<br/>Markdown formatted]
    SKIP --> FINAL_SUM
    
    INLINE --> BUILD_INLINE[Build Inline Comments<br/>For each issue]
    
    BUILD_INLINE --> FORMAT_INLINE[Format Each Comment<br/>File + Line + Message]
    
    FORMAT_INLINE --> FINAL_INLINE[Inline Comments Array]
    
    FINAL_SUM --> COMBINE[Combine Results]
    FINAL_INLINE --> COMBINE
    
    COMBINE --> OUTPUT[Output<br/>Comments Ready]
    
    OUTPUT --> ADAPTER[Send to<br/>Platform Adapter]
    
    ADAPTER --> API[Platform API<br/>POST comments]
    
    API --> VISIBLE[Comments Visible<br/>in PR/MR page]
    
    style INPUT fill:#2196F3,stroke:#1565C0,stroke-width:3px
    style STRATEGY fill:#FF9800,stroke:#E65100,stroke-width:2px
    style BOTH fill:#FF9800,stroke:#E65100,stroke-width:2px
    style SUMMARY fill:#9C27B0,stroke:#6A1B9A,stroke-width:3px
    style BUILD_SUM fill:#9C27B0,stroke:#6A1B9A,stroke-width:3px
    style BRANCH fill:#9C27B0,stroke:#6A1B9A,stroke-width:3px
    style TABLE fill:#FFEB3B,stroke:#F57F17,stroke-width:2px
    style SKIP fill:#9C27B0,stroke:#6A1B9A,stroke-width:3px
    style FINAL_SUM fill:#9C27B0,stroke:#6A1B9A,stroke-width:3px
    style INLINE fill:#00BCD4,stroke:#00838F,stroke-width:3px
    style BUILD_INLINE fill:#00BCD4,stroke:#00838F,stroke-width:3px
    style FORMAT_INLINE fill:#00BCD4,stroke:#00838F,stroke-width:3px
    style FINAL_INLINE fill:#00BCD4,stroke:#00838F,stroke-width:3px
    style COMBINE fill:#4CAF50,stroke:#2E7D32,stroke-width:3px
    style OUTPUT fill:#4CAF50,stroke:#2E7D32,stroke-width:3px
    style VISIBLE fill:#4CAF50,stroke:#2E7D32,stroke-width:3px
    style ADAPTER fill:#607D8B,stroke:#37474F,stroke-width:2px
    style API fill:#607D8B,stroke:#37474F,stroke-width:2px
```

---

## 📁 Dosya Yapısı

```
mcp-server/
├── server.py                    # Ana FastAPI server
│
├── config.yaml                  # Konfigürasyon
│
├── webhook/                     # Webhook handling
│   ├── handler.py              # Platform detection
│   └── parsers/
│       ├── github_parser.py    # GitHub webhook parse
│       ├── gitlab_parser.py    # GitLab webhook parse
│       ├── bitbucket_parser.py # Bitbucket webhook parse
│       └── azure_parser.py     # Azure webhook parse
│
├── adapters/                    # Platform integrations
│   ├── base_adapter.py         # Abstract base
│   ├── github_adapter.py       # GitHub API
│   ├── gitlab_adapter.py       # GitLab API
│   ├── bitbucket_adapter.py    # Bitbucket API
│   └── azure_adapter.py        # Azure DevOps API
│
├── services/                    # Core logic
│   ├── language_detector.py   # Dil tespiti
│   ├── diff_analyzer.py        # Diff parsing
│   ├── rule_generator.py       # AI ile rule oluşturma
│   ├── ai_reviewer.py          # AI review engine
│   └── comment_service.py      # Comment formatting
│
├── models/                      # Data models
│   └── schemas.py              # Pydantic models
│
├── rules/                       # Review rules
│   ├── security.md             # Genel security
│   ├── performance.md          # Genel performance
│   ├── compilation.md          # Genel compilation
│   ├── best-practices.md       # Genel best practices
│   ├── csharp-security.md      # C# security (auto-generated)
│   ├── python-performance.md   # Python performance (auto-generated)
│   └── ...                     # Dil-kategori kombinasyonları
│
├── tools/                       # MCP tools
│   └── review_tools.py         # Manual review tools
│
└── docker/                      # Containerization
    ├── Dockerfile
    └── docker-compose.yml
```

---

## 📊 Veri Akışı

```
PR Açılır
    ↓
Webhook Gelir (JSON payload)
    ↓
Platform Tespit Edilir (headers)
    ↓
PR Verisi Parse Edilir (parser)
    ↓
Diff API'den Çekilir (adapter)
    ↓
Dosyalar Listelenir (diff analyzer)
    ↓
Dil Tespit Edilir (language detector)
    ↓
Rule'lar Hazırlanır (rule generator)
    ├─ Cache'de var mı? → Yükle
    └─ Yok mu? → AI ile oluştur → Kaydet
    ↓
AI'a Gönderilir (ai reviewer)
    ├─ Diff
    ├─ Language-specific rules
    └─ Focus areas
    ↓
Review Sonucu Alınır (JSON)
    ├─ Score (0-10)
    ├─ Issues (severity, line, file)
    └─ Block merge? (critical varsa true)
    ↓
Yorumlar Formatlanır (comment service)
    ├─ Summary comment
    └─ Inline comments
    ↓
Platform'a Yazılır (adapter)
    ├─ Post comments (API)
    └─ Update status (success/failure)
    ↓
Developer Görür (PR sayfası)
```

---

## 🎯 Kritik Bileşenler

### 1. Platform Agnostic Design
- Tek webhook endpoint tüm platformları destekler
- Header-based platform detection
- Unified PR data model

### 2. Language-Aware Review
- 25+ dil desteği
- Otomatik dil tespiti
- Dile özel kurallar (AI-generated)

### 3. Intelligent Caching
- Language rules cache
- Mevcut rule varsa yeniden oluşturulmaz
- Performans optimizasyonu

### 4. Flexible AI Provider
- Groq (hızlı, ücretsiz)
- Anthropic Claude (kaliteli)
- OpenAI GPT-4 (standart)
- Runtime'da değiştirilebilir

### 5. Smart Comment Strategy
- Summary: Genel özet
- Inline: Satır bazlı yorumlar
- Both: Her ikisi de
- Branch-specific detailed tables

---

**🎨 Architecture by Design:**
- ✅ **Modular**: Her component bağımsız
- ✅ **Scalable**: Yeni platform ekleme kolay
- ✅ **Maintainable**: Temiz kod yapısı
- ✅ **Testable**: Unit test friendly
- ✅ **Flexible**: Config-driven behavior
