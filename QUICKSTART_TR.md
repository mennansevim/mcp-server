# 🚀 Hızlı Başlangıç Rehberi

MCP Code Review Server'ı 5 dakikada çalıştırın!

## ✅ Ön Gereksinimler

- Python 3.10+ (kurulu: 3.14 ✅)
- GitHub hesabı
- Groq hesabı (ücretsiz)

---

## 📋 Adım Adım Kurulum

### 1️⃣ Groq API Key Alın (2 dakika)

1. 🌐 https://console.groq.com adresine gidin
2. Google hesabınızla giriş yapın (ücretsiz)
3. Sol menüden **"API Keys"** seçin
4. **"Create API Key"** tıklayın
5. Key'i kopyalayın (başlangıç: `gsk_...`)

**Ücretsiz Limit**: Günde ~14,000 token (test için yeterli!)

---

### 2️⃣ GitHub Token Alın (2 dakika)

1. 🌐 https://github.com/settings/tokens/new adresine gidin
2. Formu doldurun:
   ```
   Note: MCP Code Review Server
   Expiration: 90 days
   
   Permissions (işaretleyin):
   ✅ repo
   ✅ write:discussion
   ```
3. **"Generate token"** tıklayın
4. Token'ı kopyalayın (başlangıç: `ghp_...`)

⚠️ Token'ı kaydedin! Bir daha göremezsiniz.

---

### 3️⃣ Projeyi Yapılandırın (1 dakika)

Terminal'de:

```bash
cd /Users/sevimm/Documents/Projects/mcp-server

# Virtual environment zaten kurulu, aktif edin:
source venv/bin/activate

# .env dosyası oluşturun:
cp .env.example .env

# Editör ile .env'i açın:
code .env  # veya: nano .env
```

**.env dosyasını düzenleyin:**

```bash
# Groq API Key (kopyaladığınız gerçek key)
GROQ_API_KEY=gsk_AbC123XyZ789_gerçek_key_buraya

# GitHub Token (kopyaladığınız gerçek token)
GITHUB_TOKEN=ghp_XyZ789AbC123_gerçek_token_buraya

# Diğerleri opsiyonel (boş bırakabilirsiniz)
# GITLAB_TOKEN=
# BITBUCKET_USERNAME=
# BITBUCKET_APP_PASSWORD=
```

Dosyayı kaydedin ve kapatın.

---

### 4️⃣ Server'ı Başlatın (30 saniye)

```bash
# Test script ile başlatın:
./test_server.sh

# Veya doğrudan:
python server.py
```

**Başarılı çıktı göreceksiniz:**
```
INFO:     Started server process
INFO:     Uvicorn running on http://0.0.0.0:8000
```

---

### 5️⃣ Test Edin

**Yeni bir terminal açın** ve çalıştırın:

```bash
curl http://localhost:8000/
```

**Beklenen sonuç:**
```json
{
  "name": "MCP Code Review Server",
  "version": "1.0.0",
  "status": "healthy",
  "platforms": ["github"]
}
```

✅ **Tebrikler! Server çalışıyor!** 🎉

---

## 🧪 Manuel Test (MCP Tools)

Server çalışırken ayrı bir terminal'de:

```bash
source venv/bin/activate
python
```

Python console'da:

```python
import asyncio
from services.ai_reviewer import AIReviewer

async def test():
    reviewer = AIReviewer(provider="groq", model="llama-3.3-70b-versatile")
    
    code = """
def login(username, password):
    query = f"SELECT * FROM users WHERE username='{username}'"
    return db.execute(query)
"""
    
    result = await reviewer.review(
        diff=code,
        files_changed=["auth.py"],
        focus_areas=["security", "bugs"]
    )
    
    print(f"Score: {result.score}/10")
    print(f"Issues: {result.total_issues}")
    print(f"Summary: {result.summary}")

asyncio.run(test())
```

**Beklenen**: SQL injection uyarısı ve güvenlik önerileri! 🔐

---

## 🔗 GitHub Webhook Kurulumu (CI/CD)

### GitHub Actions Örneği

1. Repo'nuza gidin: **Settings** → **Secrets and variables** → **Actions**
2. Secrets ekleyin:
   - `REVIEW_SERVER_URL`: Server URL'iniz (örn: `https://your-server.com`)
   - `GROQ_API_KEY`: Groq key'iniz

3. `.github/workflows/code-review.yml` oluşturun:

```yaml
name: AI Code Review

on:
  pull_request:
    types: [opened, synchronize]

jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - name: Trigger AI Review
        run: |
          curl -X POST ${{ secrets.REVIEW_SERVER_URL }}/webhook \
            -H "Content-Type: application/json" \
            -H "X-GitHub-Event: pull_request" \
            -d @- << EOF
          $(cat $GITHUB_EVENT_PATH)
          EOF
```

---

## 🐛 Sorun Giderme

### Server başlamıyor

```bash
# Log'ları kontrol edin
python server.py 2>&1 | tee server.log
```

**Yaygın hatalar:**

1. **"GROQ_API_KEY required"**
   → .env dosyasında GROQ_API_KEY eklenmiş mi kontrol edin

2. **"GITHUB_TOKEN required"**
   → .env dosyasında GITHUB_TOKEN eklenmiş mi kontrol edin

3. **"Port 8000 already in use"**
   → Başka bir process kullanıyor:
   ```bash
   lsof -ti:8000 | xargs kill -9
   ```

4. **"Module not found"**
   → Virtual environment aktif mi?
   ```bash
   source venv/bin/activate
   pip install -r requirements.txt
   ```

---

## 📚 İleri Seviye

### Model Değiştirme

`config.yaml` dosyasını düzenleyin:

```yaml
ai:
  provider: "groq"
  
  # Varsayılan (hızlı ve güçlü)
  model: "llama-3.3-70b-versatile"
  
  # Alternatifler:
  # model: "llama-3.1-70b-versatile"  # Biraz daha yavaş
  # model: "mixtral-8x7b-32768"       # Daha ucuz
```

### Comment Strategy Değiştirme

```yaml
review:
  comment_strategy: "both"  # summary, inline, veya both
  
  report_levels:
    - critical
    - high
    - medium
    # low ve info'yu ekleyebilirsiniz
```

---

## 🎯 Sonraki Adımlar

1. ✅ Server test edildi
2. ⏭️ GitHub repo'nuza webhook ekleyin
3. ⏭️ İlk PR'ınızı açın ve AI review görun!
4. ⏭️ GitLab, Bitbucket, Azure DevOps entegrasyonları ekleyin

---

## 🆘 Yardım

- GitHub Issues: Hata bildirin
- Documentation: `README.md` ve `examples/` klasörü
- Logs: `server.log` dosyasını kontrol edin

---

**Hazırsınız! 🚀 AI-powered code review keyfini çıkarın!**

