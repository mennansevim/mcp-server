# 🔄 Update & Redeploy Workflow

Kod değişikliği yaptıktan sonra adım adım rehber.

---

## 📝 Senaryo: Kod Değiştirdiniz

```bash
# Örnek: comment_service.py'de değişiklik yaptınız
vim services/comment_service.py
```

---

## 🔄 Update Workflow

### **Yöntem 1: Hızlı Script (Önerilen)**

```bash
./redeploy.sh
```

**Bu script ne yapar:**
1. ✅ Eski container'ı durdurur ve siler
2. ✅ Yeni image build eder
3. ✅ Yeni container başlatır
4. ✅ Health check yapar
5. ✅ Sonucu gösterir

**Eski image'ları da temizlemek için:**
```bash
./redeploy.sh --clean
```

---

### **Yöntem 2: Manuel Adımlar**

#### 1️⃣ Eski Container'ı Durdur
```bash
podman stop mcp-server
podman rm mcp-server
```

#### 2️⃣ Yeni Image Build Et
```bash
podman build -t mcp-code-review:latest .
```

#### 3️⃣ Yeni Container Başlat
```bash
podman run -d \
  --name mcp-server \
  -p 8000:8000 \
  --env-file .env \
  --restart unless-stopped \
  mcp-code-review:latest
```

#### 4️⃣ Test Et
```bash
# Health check
curl http://localhost:8000/

# Log'ları izle
podman logs -f mcp-server
```

---

## 🚀 Production Deployment

### **Senaryo: Railway'de Deploy Edilmiş**

#### Yöntem A: Git Push (Otomatik)

Railway GitHub repo'nuzu izliyor:

```bash
# 1. Değişiklikleri commit et
git add .
git commit -m "feat: improve comment formatting"

# 2. Push et
git push origin main
```

✅ **Railway otomatik deploy eder!** (3-5 dakika)

#### Yöntem B: Railway CLI (Manuel)

```bash
# Deploy et
railway up

# Log'ları izle
railway logs -f
```

---

### **Senaryo: Render'da Deploy Edilmiş**

#### Otomatik Deploy:
```bash
git push origin main
```
✅ Render otomatik rebuild ve deploy eder

#### Manuel Deploy:
```
Render Dashboard → Manual Deploy → Clear build cache & deploy
```

---

### **Senaryo: Fly.io'da Deploy Edilmiş**

```bash
# Deploy et
flyctl deploy

# Status kontrol
flyctl status

# Log'lar
flyctl logs -f
```

---

## 🧪 Test Workflow (Güvenli Deployment)

### Local Test → Production Deploy

```bash
# 1. Local'de test et
./redeploy.sh
curl http://localhost:8000/

# 2. Test PR oluştur (local server ile)
# ngrok ile test yapabilirsiniz

# 3. Her şey OK ise production'a push
git add .
git commit -m "feat: tested feature"
git push origin main
```

---

## 📊 Common Update Scenarios

### **1. Config Değişikliği (config.yaml)**

```bash
# Local
vim config.yaml
./redeploy.sh

# Production (Railway)
railway variables set SOME_CONFIG=value
railway restart
```

### **2. Environment Variable Değişikliği**

```bash
# Local
vim .env
./redeploy.sh

# Production (Railway)
railway variables set GROQ_API_KEY=new_key_...
railway restart
```

### **3. Dependency Ekleme (requirements.txt)**

```bash
# Local
echo "new-package==1.0.0" >> requirements.txt
./redeploy.sh

# Production
git push origin main  # Otomatik rebuild
```

### **4. Kod Değişikliği (services/, adapters/, etc.)**

```bash
# Local
vim services/ai_reviewer.py
./redeploy.sh

# Production
git commit -am "fix: improve AI prompts"
git push origin main
```

---

## 🔍 Debugging Update Issues

### Local Container Başlamıyor

```bash
# Log'ları kontrol et
podman logs mcp-server

# Container içine gir
podman exec -it mcp-server /bin/bash

# Manuel çalıştır (debug)
podman run -it --rm \
  --env-file .env \
  mcp-code-review:latest \
  /bin/bash
  
# İçeride:
python server.py
```

### Production Deploy Başarısız

```bash
# Railway
railway logs
railway status

# Render
Dashboard → Events → Build logs

# Fly.io
flyctl logs
flyctl status
```

### Environment Variable Eksik

```bash
# Railway
railway variables
railway variables set MISSING_VAR=value

# Render
Dashboard → Environment → Add Variable → Manual Deploy
```

---

## ⚡ Zero-Downtime Deployment (Advanced)

### Railway (Otomatik)
✅ Railway zero-downtime deployment yapar

### Blue-Green Deployment (Manuel)

```bash
# Eski: mcp-server (port 8000)
# Yeni: mcp-server-new (port 8001)

# 1. Yeni container başlat
podman run -d \
  --name mcp-server-new \
  -p 8001:8000 \
  --env-file .env \
  mcp-code-review:latest

# 2. Test et
curl http://localhost:8001/

# 3. OK ise eski container'ı durdur
podman stop mcp-server
podman rm mcp-server

# 4. Yeni container'ı rename et
podman rename mcp-server-new mcp-server

# 5. Port değiştir (opsiyonel)
# Nginx/Traefik gibi reverse proxy kullan
```

---

## 🎯 Best Practices

### 1. **Git Workflow**
```bash
# Feature branch kullan
git checkout -b feature/new-comment-format
# ... değişiklikler ...
git commit -m "feat: add emoji to comments"
git push origin feature/new-comment-format

# PR aç, merge et
# Production otomatik deploy edilir
```

### 2. **Versiyonlama**
```bash
# Git tag kullan
git tag -a v1.1.0 -m "Add inline comment support"
git push origin v1.1.0

# Railway'de specific version deploy et
railway up --tag v1.1.0
```

### 3. **Rollback**
```bash
# Railway
railway rollback

# Manuel (Git)
git revert HEAD
git push origin main
```

### 4. **Monitoring**
```bash
# Health check cron job
*/5 * * * * curl -f https://your-app.railway.app/ || echo "Server down!"

# Uptime monitoring
# - UptimeRobot (ücretsiz)
# - Better Uptime
```

---

## 📅 Update Checklist

Deployment öncesi kontrol listesi:

- [ ] Kod değişikliği yapıldı
- [ ] Local'de test edildi (`./redeploy.sh`)
- [ ] Health check geçti (`curl localhost:8000/`)
- [ ] Test PR oluşturuldu (opsiyonel)
- [ ] AI review çalıştı (opsiyonel)
- [ ] Git commit/push yapıldı
- [ ] Production deploy edildi
- [ ] Production health check yapıldı
- [ ] Log'lar kontrol edildi
- [ ] GitHub Secret'lar güncellendi (eğer URL değiştiyse)

---

## 🚨 Emergency Rollback

Bir şeyler ters gittiyse hızlı rollback:

### Railway
```bash
railway rollback
```

### Git (Tüm platformlar)
```bash
# Son commit'i geri al
git revert HEAD
git push origin main

# Veya önceki commit'e dön
git reset --hard HEAD~1
git push --force origin main  # ⚠️ Dikkatli kullanın
```

### Manuel (Local)
```bash
# Eski image'ı kullan
podman images  # Eski image ID'yi bul
podman tag OLD_IMAGE_ID mcp-code-review:latest
./redeploy.sh
```

---

## 📚 Hızlı Komutlar

```bash
# Local redeploy
./redeploy.sh

# Production deploy (Railway)
git push origin main

# Log'ları izle
podman logs -f mcp-server           # Local
railway logs -f                      # Railway

# Container durumu
podman ps                            # Local
railway status                       # Railway

# Test
curl http://localhost:8000/          # Local
curl https://your-app.railway.app/   # Production
```

---

## 🎉 Özet

### Local Development Cycle:
```
Kod değiştir → ./redeploy.sh → Test et → Git commit → Push
```

### Production Deployment:
```
Git push → Platform otomatik deploy → Health check → ✅
```

**Update süresi:**
- Local: ~2 dakika (build + start)
- Railway: ~3-5 dakika (otomatik)
- Render: ~5-10 dakika (otomatik)

---

**Hazırsınız! İyi deployment'lar! 🚀**

