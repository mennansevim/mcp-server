# 🚀 MCP Server Deployment Rehberi

Container'ınız hazır ve local'de çalışıyor! Şimdi production'a deploy edelim.

---

## 📊 Deployment Seçenekleri

| Platform | Maliyet | Zorluk | Süre | Önerilen |
|----------|---------|---------|------|----------|
| **Railway** | $5/ay | ⭐ Çok Kolay | 5 dk | ✅ En İyi |
| **Render** | Ücretsiz | ⭐⭐ Kolay | 10 dk | ✅ İyi |
| **Fly.io** | Ücretsiz | ⭐⭐ Kolay | 10 dk | ✅ İyi |
| **DigitalOcean** | $4/ay | ⭐⭐⭐ Orta | 20 dk | 💪 Güçlü |
| **AWS/Azure** | Değişken | ⭐⭐⭐⭐⭐ Zor | 1 saat | 🏢 Enterprise |

---

## 🌟 1. Railway (Önerilen - En Kolay)

### Neden Railway?
- ✅ GitHub repo'dan otomatik deploy
- ✅ Otomatik HTTPS
- ✅ Environment variables GUI
- ✅ Auto-scaling
- ✅ $5/ay (hobby plan)

### Adımlar:

1. **Railway hesabı aç**
   ```
   https://railway.app
   GitHub ile giriş yap
   ```

2. **New Project → Deploy from GitHub repo**
   ```
   mcp-server repository'sini seç
   ```

3. **Environment Variables ekle**
   ```
   GROQ_API_KEY=gsk_...
   GITHUB_TOKEN=ghp_...
   ```

4. **Deploy!**
   ```
   Otomatik build ve deploy başlar
   URL: https://mcp-server-production.up.railway.app
   ```

5. **GitHub Secret güncelle**
   ```
   Repository Settings → Secrets
   REVIEW_SERVER_URL = https://mcp-server-production.up.railway.app
   ```

✅ **Hazır!** GitHub PR'lar otomatik review alacak!

---

## 🆓 2. Render (Ücretsiz Tier)

### Adımlar:

1. **Render hesabı**
   ```
   https://render.com
   ```

2. **New → Web Service**
   ```
   Connect GitHub repo: mcp-server
   ```

3. **Ayarlar**
   ```
   Name: mcp-server
   Runtime: Docker
   Branch: main
   ```

4. **Environment Variables**
   ```
   GROQ_API_KEY=gsk_...
   GITHUB_TOKEN=ghp_...
   ```

5. **Deploy**
   ```
   URL: https://mcp-server.onrender.com
   ```

⚠️ **Not:** Ücretsiz tier 15 dakika inactivity sonrası sleep'e geçer.

---

## 🐳 3. Fly.io (Container Native)

### Kurulum:

```bash
# Fly CLI kur
brew install flyctl

# Login
flyctl auth login

# Deploy
cd /Users/sevimm/Documents/Projects/mcp-server
flyctl launch
```

### İnteraktif Setup:
```
? App Name: mcp-server
? Region: Amsterdam (ams)
? Postgres: No
? Redis: No
```

### Environment Variables:
```bash
flyctl secrets set GROQ_API_KEY=gsk_...
flyctl secrets set GITHUB_TOKEN=ghp_...
```

### Deploy:
```bash
flyctl deploy
```

URL: `https://mcp-server.fly.dev`

---

## 💪 4. DigitalOcean App Platform

### Adımlar:

1. **DigitalOcean hesabı**
   ```
   https://cloud.digitalocean.com
   ```

2. **Create → Apps → GitHub**
   ```
   Repository: mcp-server
   Branch: main
   ```

3. **App Spec**
   ```
   Type: Docker
   Port: 8000
   Instance Size: Basic ($4/mo)
   ```

4. **Environment Variables**
   ```
   GROQ_API_KEY=gsk_...
   GITHUB_TOKEN=ghp_...
   ```

5. **Deploy**
   ```
   URL: https://mcp-server-abc123.ondigitalocean.app
   ```

---

## 🏢 5. AWS ECS (Advanced)

Eğer AWS biliyorsanız ve güçlü infra istiyorsanız:

```bash
# ECR'a push
aws ecr create-repository --repository-name mcp-server
podman tag mcp-code-review:latest 123456789.dkr.ecr.us-east-1.amazonaws.com/mcp-server
podman push ...

# ECS Task Definition oluştur
# Service oluştur
# ALB kur
```

---

## 📝 Deployment Checklist

- [ ] Container local'de çalışıyor (`podman ps`)
- [ ] `.env` dosyası hazır
- [ ] GitHub repo public veya platform'a erişim verildi
- [ ] Environment variables ayarlandı
- [ ] HTTPS URL alındı
- [ ] GitHub Secret güncellendi (`REVIEW_SERVER_URL`)
- [ ] Test PR açıldı
- [ ] AI review yorumu geldi ✅

---

## 🧪 Test Deployment

Deploy sonrası test:

```bash
# Health check
curl https://your-app.platform.com/

# Webhook test (GitHub webhook simulator)
curl -X POST https://your-app.platform.com/webhook \
  -H "Content-Type: application/json" \
  -H "x-github-event: pull_request" \
  -d '{"action":"opened",...}'
```

---

## 🔒 Production Best Practices

### 1. Environment Variables
```bash
# Asla commit etmeyin!
GROQ_API_KEY=xxx
GITHUB_TOKEN=xxx
WEBHOOK_SECRET=xxx  # Opsiyonel güvenlik
```

### 2. HTTPS
✅ Tüm platformlar otomatik HTTPS verir

### 3. Rate Limiting
```yaml
# config.yaml'e eklenebilir
rate_limit:
  max_requests: 100
  window: 3600  # 1 saat
```

### 4. Monitoring
- Railway: Built-in logs
- Render: Logs sekmesi
- Fly.io: `flyctl logs`
- Sentry entegrasyonu (opsiyonel)

### 5. Auto-scaling
- Railway: Otomatik
- Render: Pro plan ile
- DigitalOcean: Manuel

---

## 💰 Maliyet Karşılaştırması

| Platform | Free Tier | Paid | Limit |
|----------|-----------|------|-------|
| **Railway** | $5 credit/ay | $5+/ay | 500 saat |
| **Render** | ✅ Ücretsiz | $7/ay | Sleep after 15min |
| **Fly.io** | ✅ 3 VM | $1.94/VM | 160GB bandwidth |
| **DigitalOcean** | ❌ | $4/ay | Always on |

---

## 🎯 Hızlı Başlangıç (Railway)

**5 dakikada deploy:**

```bash
# 1. Railway CLI kur
brew install railway

# 2. Login
railway login

# 3. Link repo
cd /Users/sevimm/Documents/Projects/mcp-server
railway link

# 4. Environment variables ekle
railway variables set GROQ_API_KEY=gsk_...
railway variables set GITHUB_TOKEN=ghp_...

# 5. Deploy!
railway up
```

✅ **Deployment URL:**
```bash
railway status
# URL: https://mcp-server-production-abc123.up.railway.app
```

---

## 🆘 Sorun Giderme

### Container başlamıyor
```bash
# Local test
podman logs mcp-server

# Platform logs
railway logs
# veya
flyctl logs
```

### Environment variables eksik
```bash
# Railway
railway variables

# Render
Dashboard → Environment → Add Variables
```

### Port hatası
```bash
# Dockerfile'da EXPOSE 8000 var mı kontrol et
# Platform'da PORT=8000 ayarla
```

---

## 📚 İleri Seviye

### Custom Domain
```bash
# Railway
Settings → Domains → Add Custom Domain
# your-domain.com → mcp-server

# DNS (Cloudflare)
CNAME mcp → abc123.up.railway.app
```

### CI/CD
```yaml
# .github/workflows/deploy.yml
on: push
jobs:
  deploy:
    - name: Deploy to Railway
      run: railway up
```

### Database (Eğer gerekirse)
```bash
# Railway'de PostgreSQL ekle
railway add postgresql

# Connection string otomatik env'e eklenir
DATABASE_URL=postgresql://...
```

---

## 🎉 Sonraki Adımlar

1. ✅ Platform seçin (Railway öneririz)
2. ✅ Deploy edin
3. ✅ GitHub Secret güncelleyin
4. ✅ Test PR açın
5. ✅ AI review keyfini çıkarın! 🚀

---

**Hangi platformu seçersiniz? Hemen başlayalım!** 🚀

