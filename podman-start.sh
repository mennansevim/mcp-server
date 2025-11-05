#!/bin/bash

echo "🐳 MCP Server - Podman Container Başlatma"
echo "=========================================="
echo ""

# Renkler
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# .env kontrolü
if [ ! -f .env ]; then
    echo -e "${RED}❌ .env dosyası bulunamadı!${NC}"
    echo ""
    echo "Lütfen önce .env dosyasını oluşturun:"
    echo "  cp .env.example .env"
    echo "  # Sonra API key'leri ekleyin"
    exit 1
fi

echo -e "${BLUE}✅ .env dosyası bulundu${NC}"

# Podman kurulu mu kontrol et
if ! command -v podman &> /dev/null; then
    echo -e "${RED}❌ Podman bulunamadı!${NC}"
    echo ""
    echo "Podman kurulumu için:"
    echo "  brew install podman"
    echo "  podman machine init"
    echo "  podman machine start"
    exit 1
fi

echo -e "${BLUE}✅ Podman bulundu: $(podman --version)${NC}"

# Podman machine çalışıyor mu?
if ! podman machine list | grep -q "Currently running"; then
    echo -e "${YELLOW}⚠️  Podman machine çalışmıyor, başlatılıyor...${NC}"
    podman machine start
    sleep 3
fi

echo -e "${BLUE}✅ Podman machine çalışıyor${NC}"
echo ""

# Eski container'ı durdur ve temizle
echo -e "${YELLOW}🧹 Eski container'lar temizleniyor...${NC}"
podman stop mcp-server 2>/dev/null || true
podman rm mcp-server 2>/dev/null || true

# Image build et
echo ""
echo -e "${YELLOW}🔨 Container image build ediliyor...${NC}"
echo ""
podman build -t mcp-code-review:latest .

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Build başarısız!${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}✅ Build başarılı!${NC}"
echo ""

# Container'ı başlat
echo -e "${YELLOW}🚀 Container başlatılıyor...${NC}"
echo ""

# .env dosyasını yükle ve container'a geçir
podman run -d \
  --name mcp-server \
  -p 8000:8000 \
  --env-file .env \
  -v "$SCRIPT_DIR/config.yaml:/app/config.yaml:ro,z" \
  --restart unless-stopped \
  mcp-code-review:latest

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Container başlatılamadı!${NC}"
    echo ""
    echo "Log'ları kontrol edin:"
    echo "  podman logs mcp-server"
    exit 1
fi

echo -e "${GREEN}✅ Container başlatıldı!${NC}"
echo ""

# Biraz bekle
echo -e "${BLUE}⏳ Server başlaması bekleniyor (5 saniye)...${NC}"
sleep 5

# Health check
echo ""
echo -e "${BLUE}🏥 Health check yapılıyor...${NC}"
HEALTH_CHECK=$(curl -s http://localhost:8000/ 2>/dev/null)

if echo "$HEALTH_CHECK" | grep -q "healthy"; then
    echo -e "${GREEN}✅ Server sağlıklı ve çalışıyor!${NC}"
    echo ""
    echo "$HEALTH_CHECK" | python3 -m json.tool 2>/dev/null || echo "$HEALTH_CHECK"
else
    echo -e "${RED}❌ Server yanıt vermiyor!${NC}"
    echo ""
    echo "Log'ları kontrol edin:"
    echo "  podman logs mcp-server"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo -e "${GREEN}🎉 MCP Server Podman'de Çalışıyor!${NC}"
echo ""
echo "📊 Kullanışlı Komutlar:"
echo ""
echo "  🔍 Log'ları göster:"
echo "     podman logs -f mcp-server"
echo ""
echo "  📊 Container durumu:"
echo "     podman ps"
echo ""
echo "  🔄 Yeniden başlat:"
echo "     podman restart mcp-server"
echo ""
echo "  🛑 Durdur:"
echo "     podman stop mcp-server"
echo ""
echo "  🗑️  Kaldır:"
echo "     podman rm -f mcp-server"
echo ""
echo "  🧪 Test et:"
echo "     curl http://localhost:8000/"
echo ""
echo "  🌐 Server URL:"
echo "     http://localhost:8000"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Log'ları göster (10 saniye)
echo -e "${BLUE}📋 Server başlangıç logları:${NC}"
echo ""
podman logs mcp-server
echo ""
echo -e "${YELLOW}💡 Canlı log'ları izlemek için:${NC}"
echo "   podman logs -f mcp-server"
echo ""


