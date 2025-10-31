#!/bin/bash

echo "🚀 GitHub PR AI Review - Hızlı Test"
echo "===================================="
echo ""

# Renkler
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 1. Server'ı başlat
echo -e "${YELLOW}📦 1. MCP Server başlatılıyor...${NC}"
cd "$(dirname "$0")"
source venv/bin/activate

# Server'ı arka planda başlat
nohup python server.py > server.log 2>&1 &
SERVER_PID=$!
echo $SERVER_PID > server.pid
echo -e "${GREEN}   ✅ Server başlatıldı (PID: $SERVER_PID)${NC}"
sleep 3

# 2. ngrok'u başlat (localhost'u internete aç)
echo ""
echo -e "${YELLOW}🌐 2. ngrok ile public URL oluşturuluyor...${NC}"

# ngrok kurulu mu kontrol et
if ! command -v ngrok &> /dev/null; then
    echo -e "${RED}   ❌ ngrok bulunamadı!${NC}"
    echo ""
    echo "   ngrok'u kurmak için:"
    echo "   brew install ngrok"
    echo "   veya: https://ngrok.com/download"
    echo ""
    kill $SERVER_PID
    exit 1
fi

# ngrok'u arka planda başlat
nohup ngrok http 8000 > /dev/null 2>&1 &
NGROK_PID=$!
echo $NGROK_PID > ngrok.pid
sleep 3

# ngrok URL'ini al
NGROK_URL=$(curl -s http://localhost:4040/api/tunnels | grep -o '"public_url":"https://[^"]*' | head -1 | cut -d'"' -f4)

if [ -z "$NGROK_URL" ]; then
    echo -e "${RED}   ❌ ngrok URL alınamadı!${NC}"
    kill $SERVER_PID
    kill $NGROK_PID
    exit 1
fi

echo -e "${GREEN}   ✅ Public URL: $NGROK_URL${NC}"

# 3. Health check
echo ""
echo -e "${YELLOW}🏥 3. Server health check...${NC}"
HEALTH=$(curl -s $NGROK_URL/)
if echo "$HEALTH" | grep -q "healthy"; then
    echo -e "${GREEN}   ✅ Server sağlıklı!${NC}"
else
    echo -e "${RED}   ❌ Server yanıt vermiyor!${NC}"
    kill $SERVER_PID
    kill $NGROK_PID
    exit 1
fi

# 4. Test repo oluştur
echo ""
echo -e "${YELLOW}📁 4. Test repository oluşturuluyor...${NC}"
echo ""
echo "   Bu adımı MANUEL yapmanız gerekiyor:"
echo ""
echo -e "${GREEN}   A) Mevcut bir GitHub repo'nuza eklemek için:${NC}"
echo ""
echo "   1. Repo'nuza gidin: https://github.com/KULLANICI_ADI/REPO_ADI"
echo "   2. Settings → Webhooks → Add webhook"
echo "   3. Payload URL: ${NGROK_URL}/webhook"
echo "   4. Content type: application/json"
echo "   5. Events: Pull requests seçin"
echo "   6. Add webhook tıklayın"
echo ""
echo -e "${GREEN}   B) VEYA GitHub Actions ile:${NC}"
echo ""
echo "   1. Repo'nuzda .github/workflows/ai-review.yml oluşturun"
echo "   2. Şu içeriği yapıştırın:"
echo ""
cat << 'WORKFLOW'
name: AI Code Review
on:
  pull_request:
    types: [opened, synchronize]
jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - name: Trigger Review
        run: |
          curl -X POST $NGROK_URL/webhook \
            -H "Content-Type: application/json" \
            -d '{"action":"opened","pull_request":{"number":1}}'
WORKFLOW
echo ""
echo "   (NGROK_URL'i gerçek URL ile değiştirin: $NGROK_URL)"
echo ""

# 5. Bekleme ve monitoring
echo ""
echo -e "${YELLOW}👀 5. Server izleniyor...${NC}"
echo ""
echo "   📊 Server logs: tail -f server.log"
echo "   🌐 ngrok dashboard: http://localhost:4040"
echo "   🔗 Webhook URL: $NGROK_URL/webhook"
echo ""
echo -e "${GREEN}   ✅ Her şey hazır! Şimdi GitHub'da PR açın!${NC}"
echo ""
echo "   Durdurmak için: Ctrl+C"
echo ""

# Cleanup function
cleanup() {
    echo ""
    echo -e "${YELLOW}🛑 Temizleniyor...${NC}"
    kill $SERVER_PID 2>/dev/null
    kill $NGROK_PID 2>/dev/null
    rm -f server.pid ngrok.pid
    echo -e "${GREEN}✅ Temizlendi!${NC}"
    exit 0
}

trap cleanup SIGINT SIGTERM

# Log'ları göster
tail -f server.log

