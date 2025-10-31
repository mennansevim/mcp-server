#!/bin/bash

echo "🚀 MCP Server Test Script"
echo "========================="
echo ""

# Check .env file
if [ ! -f .env ]; then
    echo "❌ .env dosyası bulunamadı!"
    echo "📝 Önce .env dosyasını oluşturun:"
    echo ""
    echo "   cp .env.example .env"
    echo "   # Sonra .env'i düzenleyip API key'leri ekleyin"
    echo ""
    exit 1
fi

echo "✅ .env dosyası bulundu"
echo ""

# Check Groq API key
if grep -q "gsk_your_actual_groq_key_here" .env; then
    echo "⚠️  Groq API Key henüz eklenmemiş!"
    echo "   .env dosyasında GROQ_API_KEY'i gerçek değerle değiştirin"
    echo ""
fi

# Check GitHub token
if grep -q "ghp_your_actual_github_token_here" .env; then
    echo "⚠️  GitHub Token henüz eklenmemiş!"
    echo "   .env dosyasında GITHUB_TOKEN'ı gerçek değerle değiştirin"
    echo ""
fi

# Activate venv
echo "🔧 Virtual environment aktif ediliyor..."
source venv/bin/activate

echo "🌐 Server başlatılıyor..."
echo ""
echo "Test için başka bir terminal'de şunu çalıştırın:"
echo ""
echo "   curl http://localhost:8000/"
echo ""
echo "Durdurmak için: Ctrl+C"
echo ""
echo "========================="
echo ""

# Start server
python server.py

