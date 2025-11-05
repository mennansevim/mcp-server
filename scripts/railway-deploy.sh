#!/bin/bash

echo "🚂 Railway Deployment Script"
echo "============================="
echo ""

# Renkler
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

# Railway CLI kontrolü
if ! command -v railway &> /dev/null; then
    echo -e "${YELLOW}📦 Railway CLI kuruluyor...${NC}"
    brew install railway
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}❌ Railway CLI kurulamadı!${NC}"
        echo ""
        echo "Manuel kurulum:"
        echo "  brew install railway"
        echo "  # veya"
        echo "  npm install -g @railway/cli"
        exit 1
    fi
fi

echo -e "${GREEN}✅ Railway CLI kurulu: $(railway --version)${NC}"
echo ""

# Login kontrolü
echo -e "${BLUE}🔐 Railway login kontrol ediliyor...${NC}"
railway whoami &> /dev/null

if [ $? -ne 0 ]; then
    echo -e "${YELLOW}⚠️  Railway'e giriş yapmanız gerekiyor${NC}"
    echo ""
    railway login
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}❌ Login başarısız!${NC}"
        exit 1
    fi
fi

echo -e "${GREEN}✅ Railway'e giriş yapıldı${NC}"
echo ""

# Project oluştur veya bağlan
echo -e "${BLUE}📂 Project oluşturuluyor...${NC}"
railway init

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Project oluşturulamadı!${NC}"
    exit 1
fi

echo ""
echo -e "${YELLOW}🔑 Environment variables ekleniyor...${NC}"
echo ""

# .env dosyasından oku
if [ -f .env ]; then
    echo -e "${BLUE}💡 .env dosyasından environment variables okunuyor...${NC}"
    
    # GROQ_API_KEY
    GROQ_KEY=$(grep GROQ_API_KEY .env | cut -d '=' -f2)
    if [ ! -z "$GROQ_KEY" ]; then
        railway variables set GROQ_API_KEY="$GROQ_KEY"
        echo -e "${GREEN}  ✅ GROQ_API_KEY eklendi${NC}"
    fi
    
    # GITHUB_TOKEN
    GITHUB_TOKEN=$(grep GITHUB_TOKEN .env | cut -d '=' -f2)
    if [ ! -z "$GITHUB_TOKEN" ]; then
        railway variables set GITHUB_TOKEN="$GITHUB_TOKEN"
        echo -e "${GREEN}  ✅ GITHUB_TOKEN eklendi${NC}"
    fi
    
    # GITLAB_TOKEN (opsiyonel)
    GITLAB_TOKEN=$(grep GITLAB_TOKEN .env | cut -d '=' -f2)
    if [ ! -z "$GITLAB_TOKEN" ]; then
        railway variables set GITLAB_TOKEN="$GITLAB_TOKEN"
        echo -e "${GREEN}  ✅ GITLAB_TOKEN eklendi${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  .env dosyası bulunamadı!${NC}"
    echo ""
    echo "Manuel olarak environment variables ekleyin:"
    echo "  railway variables set GROQ_API_KEY=gsk_..."
    echo "  railway variables set GITHUB_TOKEN=ghp_..."
fi

echo ""
echo -e "${YELLOW}🚀 Deployment başlatılıyor...${NC}"
echo ""

railway up

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Deployment başarısız!${NC}"
    echo ""
    echo "Log'ları kontrol edin:"
    echo "  railway logs"
    exit 1
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo -e "${GREEN}🎉 Deployment Başarılı!${NC}"
echo ""

# URL al
echo -e "${BLUE}🌐 Deployment URL'i alınıyor...${NC}"
DEPLOYMENT_URL=$(railway domain)

if [ ! -z "$DEPLOYMENT_URL" ]; then
    echo -e "${GREEN}✅ Deployment URL:${NC}"
    echo "   $DEPLOYMENT_URL"
    echo ""
    echo -e "${YELLOW}📝 Sonraki Adımlar:${NC}"
    echo ""
    echo "1. GitHub Repository Settings → Secrets → Actions"
    echo "2. New secret ekle:"
    echo "   Name: REVIEW_SERVER_URL"
    echo "   Value: $DEPLOYMENT_URL"
    echo ""
    echo "3. Workflow dosyasında kullan:"
    echo "   WEBHOOK_URL: \${{ secrets.REVIEW_SERVER_URL }}/webhook"
    echo ""
    echo "4. Test et:"
    echo "   curl $DEPLOYMENT_URL/"
fi

echo ""
echo -e "${BLUE}📊 Kullanışlı Komutlar:${NC}"
echo ""
echo "  🔍 Log'ları göster:"
echo "     railway logs"
echo ""
echo "  📊 Status:"
echo "     railway status"
echo ""
echo "  🌐 URL'i aç:"
echo "     railway open"
echo ""
echo "  🔑 Environment variables:"
echo "     railway variables"
echo ""
echo "  🚀 Yeniden deploy:"
echo "     railway up"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Health check
if [ ! -z "$DEPLOYMENT_URL" ]; then
    echo -e "${BLUE}🏥 Health check yapılıyor...${NC}"
    sleep 10
    
    HEALTH=$(curl -s "$DEPLOYMENT_URL/" 2>/dev/null)
    if echo "$HEALTH" | grep -q "healthy"; then
        echo -e "${GREEN}✅ Server sağlıklı ve çalışıyor!${NC}"
        echo ""
        echo "$HEALTH" | python3 -m json.tool 2>/dev/null || echo "$HEALTH"
    else
        echo -e "${YELLOW}⚠️  Server henüz hazır değil (birkaç dakika sürebilir)${NC}"
        echo ""
        echo "Log'ları izleyin:"
        echo "  railway logs -f"
    fi
fi

echo ""
echo -e "${GREEN}🎉 Hazırsınız! AI code review artık production'da! 🚀${NC}"
echo ""

