#!/usr/bin/env python3
"""
GitHub Webhook Simülasyonu Test Script
Gerçek bir GitHub PR webhook'unu simüle eder
"""
import requests
import json
import time
import sys

# Test için mock PR data (Gerçek GitHub webhook formatında)
MOCK_PR_PAYLOAD = {
    "action": "opened",
    "number": 123,
    "pull_request": {
        "id": 123456789,
        "number": 123,
        "title": "Fix authentication bug",
        "body": "This PR fixes a critical authentication vulnerability",
        "html_url": "https://github.com/test-user/test-repo/pull/123",
        "diff_url": "https://api.github.com/repos/test-user/test-repo/pulls/123",
        "state": "open",
        "user": {
            "login": "test-developer",
            "id": 12345
        },
        "head": {
            "sha": "abc123def456",
            "ref": "fix/auth-bug",
            "repo": {
                "id": 999,
                "name": "test-repo",
                "full_name": "test-user/test-repo",
                "owner": {
                    "login": "test-user"
                }
            }
        },
        "base": {
            "sha": "def456abc123",
            "ref": "main",
            "repo": {
                "id": 999,
                "name": "test-repo",
                "full_name": "test-user/test-repo",
                "owner": {
                    "login": "test-user"
                }
            }
        },
        "additions": 50,
        "deletions": 10,
        "changed_files": 3
    },
    "repository": {
        "id": 999,
        "name": "test-repo",
        "full_name": "test-user/test-repo",
        "html_url": "https://github.com/test-user/test-repo",
        "owner": {
            "login": "test-user",
            "id": 12345
        }
    }
}

def test_server_health(base_url):
    """Server'ın ayakta olup olmadığını kontrol et"""
    print("🏥 Server health check yapılıyor...")
    try:
        response = requests.get(f"{base_url}/", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Server sağlıklı!")
            print(f"   📊 Status: {data.get('status')}")
            print(f"   🔌 Platforms: {', '.join(data.get('platforms', []))}")
            return True
        else:
            print(f"   ❌ Server yanıt verdi ama status: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print(f"   ❌ Server'a bağlanılamıyor!")
        print(f"   💡 Server'ı başlatmayı deneyin: python server.py")
        return False
    except Exception as e:
        print(f"   ❌ Hata: {e}")
        return False

def send_webhook(base_url, payload):
    """Webhook gönder"""
    print("\n📤 GitHub webhook gönderiliyor...")
    print(f"   🎯 URL: {base_url}/webhook")
    print(f"   📦 PR: #{payload['number']} - {payload['pull_request']['title']}")
    
    headers = {
        "Content-Type": "application/json",
        "x-github-event": "pull_request",
        "x-github-delivery": "test-delivery-12345",
        "User-Agent": "GitHub-Hookshot/test"
    }
    
    try:
        response = requests.post(
            f"{base_url}/webhook",
            json=payload,
            headers=headers,
            timeout=30
        )
        
        print(f"\n📨 Webhook Response:")
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"\n✅ Webhook başarıyla işlendi!")
            print(f"\n📊 Sonuçlar:")
            print(f"   Status: {result.get('status')}")
            
            if result.get('status') == 'success':
                print(f"   PR ID: {result.get('pr_id')}")
                print(f"   Platform: {result.get('platform')}")
                print(f"   Skor: {result.get('score')}/10")
                print(f"   Toplam Sorun: {result.get('issues')}")
                print(f"   Critical: {result.get('critical')}")
            elif result.get('status') == 'ignored':
                print(f"   ⚠️  {result.get('message')}")
            else:
                print(f"   Message: {result.get('message')}")
            
            return result
        else:
            print(f"   ❌ Hata: {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            return None
            
    except requests.exceptions.Timeout:
        print(f"   ⏱️  Timeout! Server yanıt vermedi (30s)")
        print(f"   💡 AI review uzun sürebilir, loglara bakın: tail -f server.log")
        return None
    except Exception as e:
        print(f"   ❌ Hata: {e}")
        return None

def main():
    print("\n" + "="*60)
    print("🧪 GitHub Webhook Simülasyonu Test")
    print("="*60)
    
    base_url = "http://localhost:8000"
    
    # 1. Health check
    if not test_server_health(base_url):
        print("\n❌ Server çalışmıyor!")
        print("\n📝 Server'ı başlatmak için:")
        print("   Terminal 1:")
        print("   $ cd /Users/sevimm/Documents/Projects/mcp-server")
        print("   $ source venv/bin/activate")
        print("   $ python server.py")
        print("\n   Terminal 2 (bu script):")
        print("   $ python test_github_webhook.py")
        sys.exit(1)
    
    # Test 1: master branch'e PR (detaylı tablo ile)
    print("\n" + "-"*60)
    print("🧪 Test 1: master branch'e PR (Detaylı Tablo Var)")
    print("-"*60)
    payload_master = MOCK_PR_PAYLOAD.copy()
    payload_master["pull_request"]["base"]["ref"] = "master"
    result1 = send_webhook(base_url, payload_master)
    
    # Test 2: develop branch'e PR (detaylı tablo yok)
    print("\n" + "-"*60)
    print("🧪 Test 2: develop branch'e PR (Detaylı Tablo Yok)")
    print("-"*60)
    payload_develop = MOCK_PR_PAYLOAD.copy()
    payload_develop["pull_request"]["base"]["ref"] = "develop"
    payload_develop["number"] = 124
    payload_develop["pull_request"]["number"] = 124
    result2 = send_webhook(base_url, payload_develop)
    
    result = result1  # Ana sonuç olarak ilkini kullan
    
    if result:
        print("\n" + "="*60)
        print("✅ TEST TAMAMLANDI!")
        print("="*60)
        
        if result.get('status') == 'success':
            print("\n🎉 Webhook başarıyla işlendi!")
            print("💡 Gerçek GitHub PR'da şu yorumlar eklenirdi:")
            print("   - Summary comment (PR'ın üstünde)")
            print("   - Inline comments (sorunlu satırlarda)")
        elif result.get('status') == 'error':
            print("\n⚠️  Hata oluştu ama test çalıştı")
            print(f"   Hata mesajı: {result.get('message')}")
            print("\n💡 Bu normal olabilir çünkü:")
            print("   - Mock PR gerçek değil")
            print("   - GitHub API'ye ulaşılamıyor")
            print("   - .env dosyasında GITHUB_TOKEN eksik olabilir")
        else:
            print(f"\n⚠️  Status: {result.get('status')}")
            print(f"   Message: {result.get('message')}")
    else:
        print("\n❌ TEST BAŞARISIZ!")
        print("\n💡 Sorun giderme:")
        print("   1. Server loglarını kontrol edin: tail -f server.log")
        print("   2. .env dosyasını kontrol edin (GROQ_API_KEY, GITHUB_TOKEN)")
        print("   3. Server'ın 8000 portunda çalıştığından emin olun")
    
    print("\n" + "="*60)

if __name__ == "__main__":
    main()

