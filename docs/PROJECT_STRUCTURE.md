# 📁 Project Structure

```
mcp-server/
│
├── 📚 docs/                          # Documentation
│   ├── DEPLOYMENT.md                 # Deployment guide
│   ├── GITHUB_INTEGRATION.md         # GitHub setup
│   ├── SETUP_GITHUB_ACTIONS.md       # GitHub Actions config
│   ├── UPDATE_WORKFLOW.md            # Update & redeploy guide
│   └── PROJECT_STRUCTURE.md          # This file
│
├── 🐳 docker/                        # Container configuration
│   ├── Dockerfile                    # Multi-stage Docker build
│   └── docker-compose.yml            # Docker Compose setup
│
├── 🚀 scripts/                       # Deployment & setup scripts
│   ├── redeploy.sh                   # Quick redeploy (Podman)
│   ├── docker-start.sh               # Start with Docker
│   ├── podman-start.sh               # Start with Podman
│   ├── podman-compose-start.sh       # Podman Compose
│   └── railway-deploy.sh             # Deploy to Railway
│
├── 🧪 tests/                         # Test files
│   ├── test_ai_review.py             # AI review tests
│   ├── test_github_webhook.py        # Webhook simulation
│   ├── test_server.sh                # Server health check
│   └── test_webhook_full.sh          # Full integration test
│
├── 📋 logs/                          # Runtime logs (gitignored)
│   └── README.md                     # Log info
│
├── 📦 Core Application Files
│   ├── server.py                     # Main FastAPI server
│   ├── config.yaml                   # Server configuration
│   ├── requirements.txt              # Python dependencies
│   └── README.md                     # Main documentation
│
├── 🔌 adapters/                      # Platform adapters
│   ├── __init__.py
│   ├── base_adapter.py               # Base adapter interface
│   ├── github_adapter.py             # GitHub API client
│   ├── gitlab_adapter.py             # GitLab API client
│   ├── bitbucket_adapter.py          # Bitbucket API client
│   └── azure_adapter.py              # Azure DevOps API client
│
├── 🤖 services/                      # Business logic
│   ├── __init__.py
│   ├── ai_reviewer.py                # AI-powered code review
│   ├── comment_service.py            # Format review comments
│   └── diff_analyzer.py              # Parse git diffs
│
├── 📊 models/                        # Data models
│   ├── __init__.py
│   └── schemas.py                    # Pydantic models
│
├── 🔧 tools/                         # MCP Tools
│   ├── __init__.py
│   └── review_tools.py               # Manual review tools
│
├── 🌐 webhook/                       # Webhook handling
│   ├── __init__.py
│   ├── handler.py                    # Webhook router
│   └── parsers/                      # Platform-specific parsers
│       ├── __init__.py
│       ├── github_parser.py
│       ├── gitlab_parser.py
│       ├── bitbucket_parser.py
│       └── azure_parser.py
│
├── 📜 rules/                         # AI Review Rules
│   ├── README.md                     # Rules documentation
│   ├── compilation.md                # Syntax/compilation rules
│   ├── security.md                   # Security rules
│   ├── dotnet-fundamentals.md        # .NET best practices
│   ├── performance.md                # Performance rules
│   └── best-practices.md             # Code quality rules
│
└── 📝 examples/                      # CI/CD examples
    ├── github-actions.yml
    ├── gitlab-ci.yml
    ├── bitbucket-pipelines.yml
    └── azure-pipelines.yml
```

---

## 🎯 Key Directories

### `/docs` - Tüm Dokumentasyon
Deployment, setup, ve workflow rehberleri

### `/docker` - Container Dosyaları
Dockerfile ve docker-compose.yml

### `/scripts` - Otomasyon Scriptleri
Deployment ve test scriptleri

### `/tests` - Test Dosyaları
Unit testler ve integration testler

### `/rules` - AI Review Kuralları
Her kategori için detaylı rule'lar

### `/logs` - Runtime Logs
Server log'ları (gitignored)

---

## 🚀 Hızlı Başlangıç Komutları

```bash
# Development
python server.py

# Docker/Podman
./scripts/redeploy.sh

# Testing
./tests/test_server.sh

# Deployment
./scripts/railway-deploy.sh
```

---

## 📝 Dosya Organizasyon Prensipleri

1. **Separation of Concerns**
   - Core code (root)
   - Documentation (docs/)
   - Infrastructure (docker/, scripts/)
   - Tests (tests/)

2. **Easy Navigation**
   - Related files together
   - Clear naming
   - Logical grouping

3. **Clean Root**
   - Minimal files in root
   - Easy to find main entry point

---

## 🔄 Değişiklik Yapma

```bash
# Kod değişikliği
vim services/ai_reviewer.py
./scripts/redeploy.sh

# Docker değişikliği
vim docker/Dockerfile
./scripts/redeploy.sh

# Dokümantasyon
vim docs/DEPLOYMENT.md
git commit -m "docs: update deployment guide"
```

---

**Clean & Organized! 🎉**


