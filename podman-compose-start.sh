#!/bin/bash

echo "🐳 MCP Server - Podman Compose ile Başlatma"
echo "============================================"
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

# Podman compose kurulu mu?
if ! command -v podman-compose &> /dev/null; then
    echo -e "${YELLOW}⚠️  podman-compose bulunamadı, yükleniyor...${NC}"
    pip3 install podman-compose
fi

echo -e "${BLUE}✅ Podman kurulu: $(podman --version)${NC}"
echo -e "${BLUE}✅ Podman Compose kurulu: $(podman-compose --version)${NC}"

# Podman machine çalışıyor mu?
if ! podman machine list 2>/dev/null | grep -q "Currently running"; then
    echo -e "${YELLOW}⚠️  Podman machine çalışmıyor, başlatılıyor...${NC}"
    podman machine start
    sleep 3
fi

echo -e "${BLUE}✅ Podman machine çalışıyor${NC}"
echo ""

# Eski container'ları durdur
echo -e "${YELLOW}🧹 Eski container'lar temizleniyor...${NC}"
podman-compose down 2>/dev/null || true

echo ""
echo -e "${YELLOW}🔨 Container build ediliyor ve başlatılıyor...${NC}"
echo ""

# Compose ile başlat
podman-compose up -d --build

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Container başlatılamadı!${NC}"
    echo ""
    echo "Log'ları kontrol edin:"
    echo "  podman-compose logs"
    exit 1
fi

echo ""
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
    echo -e "${RED}⚠️  Server henüz yanıt vermiyor (normal olabilir)${NC}"
    echo ""
    echo "Log'ları kontrol edin:"
    echo "  podman-compose logs"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo -e "${GREEN}🎉 MCP Server Podman Compose ile Çalışıyor!${NC}"
echo ""
echo "📊 Kullanışlı Komutlar:"
echo ""
echo "  🔍 Log'ları göster:"
echo "     podman-compose logs -f"
echo ""
echo "  📊 Container durumu:"
echo "     podman-compose ps"
echo ""
echo "  🔄 Yeniden başlat:"
echo "     podman-compose restart"
echo ""
echo "  🛑 Durdur:"
echo "     podman-compose stop"
echo ""
echo "  🗑️  Kaldır:"
echo "     podman-compose down"
echo ""
echo "  🧪 Test et:"
echo "     curl http://localhost:8000/"
echo ""
echo "  🌐 Server URL:"
echo "     http://localhost:8000"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# İlk log'ları göster
echo -e "${BLUE}📋 Server başlangıç logları:${NC}"
echo ""
podman-compose logs --tail=20
echo ""
echo -e "${YELLOW}💡 Canlı log'ları izlemek için:${NC}"
echo "   podman-compose logs -f"
echo ""


