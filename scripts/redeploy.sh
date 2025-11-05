#!/bin/bash

echo "🔄 MCP Server - Redeploy Script"
echo "================================"
echo ""

# Renkler
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$SCRIPT_DIR"

echo -e "${BLUE}🔍 Mevcut durumu kontrol ediyorum...${NC}"
echo ""

# Container çalışıyor mu?
if podman ps --format "{{.Names}}" | grep -q "^mcp-server$"; then
    echo -e "${YELLOW}🛑 Eski container durduruluyor...${NC}"
    podman stop mcp-server
    podman rm mcp-server
    echo -e "${GREEN}  ✅ Eski container kaldırıldı${NC}"
else
    echo -e "${BLUE}  ℹ️  Çalışan container yok${NC}"
fi

echo ""

# Eski image'ı temizle (opsiyonel, yer kazanmak için)
if [ "$1" == "--clean" ]; then
    echo -e "${YELLOW}🧹 Eski image'lar temizleniyor...${NC}"
    podman image prune -f
    echo -e "${GREEN}  ✅ Temizlendi${NC}"
    echo ""
fi

# Yeni image build et
echo -e "${YELLOW}🔨 Yeni image build ediliyor...${NC}"
echo ""
podman build -f docker/Dockerfile -t mcp-code-review:latest . 

if [ $? -ne 0 ]; then
    echo ""
    echo -e "${RED}❌ Build başarısız!${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}✅ Build başarılı!${NC}"
echo ""

# Container'ı başlat
echo -e "${YELLOW}🚀 Yeni container başlatılıyor...${NC}"
podman run -d \
  --name mcp-server \
  -p 8000:8000 \
  --env-file .env \
  --restart unless-stopped \
  mcp-code-review:latest

if [ $? -ne 0 ]; then
    echo ""
    echo -e "${RED}❌ Container başlatılamadı!${NC}"
    echo ""
    echo "Log'ları kontrol edin:"
    echo "  podman logs mcp-server"
    exit 1
fi

echo -e "${GREEN}✅ Container başlatıldı!${NC}"
echo ""

# Health check
echo -e "${BLUE}⏳ Server başlaması bekleniyor (5 saniye)...${NC}"
sleep 5

echo ""
echo -e "${BLUE}🏥 Health check yapılıyor...${NC}"
HEALTH_CHECK=$(curl -s http://localhost:8000/ 2>/dev/null)

if echo "$HEALTH_CHECK" | grep -q "healthy"; then
    echo -e "${GREEN}✅ Server sağlıklı ve çalışıyor!${NC}"
    echo ""
    echo "$HEALTH_CHECK" | python3 -m json.tool 2>/dev/null || echo "$HEALTH_CHECK"
else
    echo -e "${YELLOW}⚠️  Server henüz yanıt vermiyor${NC}"
    echo ""
    echo "Log'ları kontrol edin:"
    echo "  podman logs mcp-server"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo -e "${GREEN}🎉 Redeploy Tamamlandı!${NC}"
echo ""
echo "📊 Container Bilgileri:"
podman ps --filter "name=mcp-server" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
echo ""
echo "🔍 Canlı log'lar için:"
echo "   podman logs -f mcp-server"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

