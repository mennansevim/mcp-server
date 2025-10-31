# 🔗 GitHub Entegrasyonu - MCP Code Review

MCP Server'ı GitHub projenize entegre etmenin 2 yolu var:

---

## 🚀 Yöntem 1: GitHub Actions (ÖNERİLEN - Kolay)

Bu yöntemde server'ınız cloud'da (Heroku, Railway, Fly.io) veya kendi sunucunuzda çalışıyor olmalı.

### Adım 1: Server'ı Deploy Edin

**Seçenek A: Localhost (Test için - ngrok ile)**
```bash
# Terminal 1: Server'ı başlat
cd /Users/sevimm/Documents/Projects/mcp-server
source venv/bin/activate
python server.py

# Terminal 2: ngrok ile internete aç
brew install ngrok  # veya: https://ngrok.com
ngrok http 8000

# ngrok'dan aldığınız URL'i not edin:
# https://abc123.ngrok.io
```

**Seçenek B: Railway (Ücretsiz - ÖNERİLEN)**
```bash
# Railway CLI kur
brew install railway

# Deploy et
cd /Users/sevimm/Documents/Projects/mcp-server
railway init
railway up

# URL'i al
railway domain
# https://your-app.railway.app
```

**Seçenek C: Fly.io (Ücretsiz)**
```bash
# Fly CLI kur
brew install flyctl

# Deploy et
cd /Users/sevimm/Documents/Projects/mcp-server
fly launch
fly deploy

# https://your-app.fly.dev
```

---

### Adım 2: GitHub Repo'nuzda Secrets Ekleyin

1. GitHub repo'nuza gidin
2. **Settings** → **Secrets and variables** → **Actions**
3. **New repository secret** ile ekleyin:

```
REVIEW_SERVER_URL = https://your-server-url.com
GROQ_API_KEY = gsk_your_actual_groq_key
GITHUB_TOKEN = ghp_your_github_token
```

---

### Adım 3: GitHub Actions Workflow Oluşturun

Repo'nuzda `.github/workflows/ai-code-review.yml` dosyası oluşturun:

```yaml
name: AI Code Review

on:
  pull_request:
    types: [opened, synchronize, reopened]

jobs:
  ai-review:
    runs-on: ubuntu-latest
    permissions:
      pull-requests: write
      contents: read
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
        with:
          fetch-depth: 0
      
      - name: Get PR diff
        id: diff
        run: |
          # PR diff'ini al
          gh pr diff ${{ github.event.pull_request.number }} > pr.diff
        env:
          GH_TOKEN: ${{ github.token }}
      
      - name: Trigger AI Review
        run: |
          # MCP Server'a webhook gönder
          curl -X POST ${{ secrets.REVIEW_SERVER_URL }}/webhook \
            -H "Content-Type: application/json" \
            -H "X-GitHub-Event: pull_request" \
            -H "X-GitHub-Delivery: ${{ github.run_id }}" \
            -d @- << 'EOF'
          {
            "action": "${{ github.event.action }}",
            "pull_request": {
              "id": ${{ github.event.pull_request.id }},
              "number": ${{ github.event.pull_request.number }},
              "title": "${{ github.event.pull_request.title }}",
              "html_url": "${{ github.event.pull_request.html_url }}",
              "diff_url": "${{ github.event.pull_request.diff_url }}",
              "head": {
                "sha": "${{ github.event.pull_request.head.sha }}"
              }
            },
            "repository": {
              "full_name": "${{ github.repository }}",
              "name": "${{ github.event.repository.name }}",
              "owner": {
                "login": "${{ github.repository_owner }}"
              }
            }
          }
          EOF
      
      - name: Comment status
        if: always()
        uses: actions/github-script@v7
        with:
          script: |
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: '🤖 AI Code Review başlatıldı! Sonuçlar birazdan gelecek...'
            })
```

---

## 🎣 Yöntem 2: GitHub Webhook (Direkt)

Bu yöntemde GitHub direkt olarak server'ınıza webhook gönderir.

### Adım 1: Server Public URL'i Hazırlayın

```bash
# Localhost için ngrok
ngrok http 8000
# URL: https://abc123.ngrok.io

# Veya cloud deployment (Railway/Fly.io/Heroku)
```

### Adım 2: GitHub'da Webhook Ekleyin

1. Repo → **Settings** → **Webhooks** → **Add webhook**

2. Formu doldurun:
```
Payload URL: https://your-server.com/webhook
Content type: application/json
Secret: (boş bırakabilirsiniz şimdilik)

Events:
✅ Pull requests
✅ Pull request reviews
```

3. **Add webhook** tıklayın

### Adım 3: Test Edin

1. Yeni bir branch oluşturun
2. Bir değişiklik yapın
3. PR açın
4. AI review yorumları otomatik gelecek! 🎉

---

## 📋 Test Senaryosu

Şimdi hızlıca test edelim:

### Test Repo Oluşturun

```bash
# Yeni test repo
mkdir ~/test-ai-review
cd ~/test-ai-review
git init

# İlk commit
echo "# Test AI Review" > README.md
git add .
git commit -m "Initial commit"

# GitHub'a push
gh repo create test-ai-review --public --source=. --remote=origin --push
```

### Test PR Açın

```bash
# Yeni branch
git checkout -b feature/add-login

# Güvenlik açığı içeren kod ekle
cat > auth.py << 'EOF'
def login(username, password):
    query = f"SELECT * FROM users WHERE username='{username}'"
    return db.execute(query)
EOF

git add auth.py
git commit -m "Add login function"
git push -u origin feature/add-login

# PR aç
gh pr create --title "Add login function" --body "Test AI review"
```

### Sonuç

PR'da AI review yorumu göreceksiniz:

```markdown
## 🤖 AI Code Review

**Score:** 2/10 ⚠️

### 📝 Summary
The code changes introduce significant security vulnerabilities...

### 📊 Issues Found
- Total: **3**
- 🔴 Critical: **1**
- 🟠 High: **1**

### ⚠️ Important Issues

#### 🔴 SQL Injection Vulnerability
**Severity:** CRITICAL
**Location:** `auth.py` (Line 2)

Using string concatenation for SQL queries...

**Suggestion:**
> Use parameterized queries...
```

---

## 🛠️ Hangi Yöntemi Seçmeliyim?

| Özellik | GitHub Actions | Webhook |
|---------|---------------|---------|
| **Kurulum** | ✅ Kolay | ⚠️ Orta |
| **Server Gerekli** | ✅ Cloud/Ngrok | ✅ Public URL |
| **Gecikme** | ⚠️ ~30 saniye | ✅ Anında |
| **Maliyet** | ✅ Ücretsiz | ⚠️ Hosting |
| **Güvenlik** | ✅ GitHub yönetir | ⚠️ Siz yönetirsiniz |

**Öneri:** Başlangıç için **GitHub Actions + ngrok** kullanın!

---

## 🚀 Hızlı Başlangıç Scripti

Tek komutla test edin:

```bash
cd /Users/sevimm/Documents/Projects/mcp-server
./quick_github_test.sh
```

Bu script:
1. ✅ Server'ı başlatır
2. ✅ ngrok ile public URL oluşturur
3. ✅ Test repo oluşturur
4. ✅ PR açar
5. ✅ AI review'ı tetikler

---

## 🐛 Sorun Giderme

### Webhook gelmedi
```bash
# Server log'ları kontrol et
tail -f server.log

# GitHub webhook delivery'leri kontrol et
# Repo → Settings → Webhooks → Recent Deliveries
```

### Review yorumu gelmedi
```bash
# GitHub token izinlerini kontrol et
curl -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/OWNER/REPO/issues/1/comments
```

### Server'a erişilemiyor
```bash
# Firewall kontrol et
curl https://your-server.com/

# Health check
curl https://your-server.com/
# Beklenen: {"status": "healthy"}
```

---

**Hazır! Şimdi GitHub projenize entegre edebilirsiniz! 🎊**

