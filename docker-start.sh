#!/bin/bash

echo "🐳 MCP Server - Docker Container Başlatma"
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

# Docker kurulu mu kontrol et
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker bulunamadı!${NC}"
    echo ""
    echo "Docker kurulumu için:"
    echo "  https://www.docker.com/products/docker-desktop"
    exit 1
fi

echo -e "${BLUE}✅ Docker bulundu: $(docker --version)${NC}"

# Docker daemon çalışıyor mu?
if ! docker info >/dev/null 2>&1; then
    echo -e "${RED}❌ Docker daemon çalışmıyor!${NC}"
    echo ""
    echo "Docker Desktop'ı başlatın ve tekrar deneyin."
    exit 1
fi

echo -e "${BLUE}✅ Docker daemon çalışıyor${NC}"
echo ""

# Eski container'ı durdur ve temizle
echo -e "${YELLOW}🧹 Eski container'lar temizleniyor...${NC}"
docker stop mcp-server 2>/dev/null || true
docker rm mcp-server 2>/dev/null || true

# Image build et
echo ""
echo -e "${YELLOW}🔨 Container image build ediliyor...${NC}"
echo ""
docker build -t mcp-code-review:latest .

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
docker run -d \
  --name mcp-server \
  -p 8000:8000 \
  --env-file .env \
  -v "$SCRIPT_DIR/config.yaml:/app/config.yaml:ro" \
  --restart unless-stopped \
  mcp-code-review:latest

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Container başlatılamadı!${NC}"
    echo ""
    echo "Log'ları kontrol edin:"
    echo "  docker logs mcp-server"
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
    echo -e "${YELLOW}⚠️  Server henüz yanıt vermiyor (biraz daha bekleyin)${NC}"
    echo ""
    echo "Log'ları kontrol edin:"
    echo "  docker logs mcp-server"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo -e "${GREEN}🎉 MCP Server Docker'da Çalışıyor!${NC}"
echo ""
echo "📊 Kullanışlı Komutlar:"
echo ""
echo "  🔍 Log'ları göster:"
echo "     docker logs -f mcp-server"
echo ""
echo "  📊 Container durumu:"
echo "     docker ps"
echo ""
echo "  🔄 Yeniden başlat:"
echo "     docker restart mcp-server"
echo ""
echo "  🛑 Durdur:"
echo "     docker stop mcp-server"
echo ""
echo "  🗑️  Kaldır:"
echo "     docker rm -f mcp-server"
echo ""
echo "  🧪 Test et:"
echo "     curl http://localhost:8000/"
echo ""
echo "  🐚 Container içine gir:"
echo "     docker exec -it mcp-server /bin/bash"
echo ""
echo "  🌐 Server URL:"
echo "     http://localhost:8000"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Log'ları göster
echo -e "${BLUE}📋 Server başlangıç logları:${NC}"
echo ""
docker logs mcp-server
echo ""
echo -e "${YELLOW}💡 Canlı log'ları izlemek için:${NC}"
echo "   docker logs -f mcp-server"
echo ""


