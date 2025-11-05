#!/bin/bash

echo "🧪 GitHub Webhook Tam Test - Server + Webhook"
echo "=============================================="
echo ""

# Renkler
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Değişkenler
SERVER_URL="http://localhost:8000"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# .env kontrolü
if [ ! -f "$SCRIPT_DIR/.env" ]; then
    echo -e "${RED}❌ .env dosyası bulunamadı!${NC}"
    echo ""
    echo "Lütfen önce .env dosyasını oluşturun:"
    echo "  cp .env.example .env"
    echo "  # Sonra GROQ_API_KEY ve GITHUB_TOKEN ekleyin"
    exit 1
fi

# Virtual environment aktif mi kontrol et
if [ -z "$VIRTUAL_ENV" ]; then
    echo -e "${YELLOW}🔧 Virtual environment aktif ediliyor...${NC}"
    cd "$SCRIPT_DIR"
    source venv/bin/activate
fi

# Server çalışıyor mu kontrol et
echo -e "${BLUE}🔍 Server durumu kontrol ediliyor...${NC}"
if curl -s "$SERVER_URL/" > /dev/null 2>&1; then
    echo -e "${GREEN}   ✅ Server zaten çalışıyor!${NC}"
    EXISTING_SERVER=true
else
    echo -e "${YELLOW}   📦 Server başlatılıyor...${NC}"
    EXISTING_SERVER=false
    
    # Server'ı arka planda başlat
    cd "$SCRIPT_DIR"
    nohup python server.py > server_test.log 2>&1 &
    SERVER_PID=$!
    echo $SERVER_PID > server_test.pid
    
    echo -e "${BLUE}   ⏳ Server başlaması bekleniyor (5 saniye)...${NC}"
    sleep 5
    
    # Server başladı mı kontrol et
    if curl -s "$SERVER_URL/" > /dev/null 2>&1; then
        echo -e "${GREEN}   ✅ Server başarıyla başlatıldı! (PID: $SERVER_PID)${NC}"
    else
        echo -e "${RED}   ❌ Server başlatılamadı!${NC}"
        echo "   Log'ları kontrol edin: cat server_test.log"
        exit 1
    fi
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Python test scriptini çalıştır
echo -e "${BLUE}🧪 Webhook test scripti çalıştırılıyor...${NC}"
echo ""
python "$SCRIPT_DIR/test_github_webhook.py"

TEST_EXIT_CODE=$?

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Server'ı başlattıysak, durdurup durdurmayacağımızı sor
if [ "$EXISTING_SERVER" = false ]; then
    echo -e "${YELLOW}📊 Server logları (son 20 satır):${NC}"
    echo ""
    tail -20 server_test.log
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    
    echo -e "${YELLOW}🔧 Server hala çalışıyor (PID: $(cat server_test.pid 2>/dev/null))${NC}"
    echo ""
    echo "Server'ı durdurmak ister misiniz? [y/N]"
    read -t 10 -n 1 STOP_SERVER
    echo ""
    
    if [ "$STOP_SERVER" = "y" ] || [ "$STOP_SERVER" = "Y" ]; then
        if [ -f server_test.pid ]; then
            SERVER_PID=$(cat server_test.pid)
            kill $SERVER_PID 2>/dev/null
            rm -f server_test.pid
            echo -e "${GREEN}✅ Server durduruldu${NC}"
        fi
    else
        echo -e "${BLUE}💡 Server çalışmaya devam ediyor${NC}"
        echo "   Durdurmak için: kill $(cat server_test.pid 2>/dev/null)"
        echo "   Log'ları görmek için: tail -f server_test.log"
    fi
fi

echo ""
if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}✅ TEST BAŞARILI!${NC}"
else
    echo -e "${RED}❌ TEST BAŞARISIZ!${NC}"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

exit $TEST_EXIT_CODE


