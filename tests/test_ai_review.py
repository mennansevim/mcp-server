#!/usr/bin/env python3
"""
MCP Server AI Review Test Script
Test Groq LLM ile gerçek bir code review
"""
import asyncio
import sys
import os
from dotenv import load_dotenv

# .env dosyasını yükle
load_dotenv()

from services.ai_reviewer import AIReviewer

# Test için güvenlik açığı içeren kod
VULNERABLE_CODE = """
--- a/auth.py
+++ b/auth.py
@@ -1,10 +1,15 @@
+import sqlite3
+
 def login(username, password):
-    # TODO: Implement login
-    pass
+    # SQL Injection vulnerability!
+    conn = sqlite3.connect('users.db')
+    query = f"SELECT * FROM users WHERE username='{username}' AND password='{password}'"
+    cursor = conn.execute(query)
+    user = cursor.fetchone()
+    return user is not None

 def get_user_data(user_id):
-    # TODO: Implement
-    pass
+    # No input validation
+    query = f"SELECT * FROM data WHERE id={user_id}"
+    return db.execute(query).fetchall()
"""

GOOD_CODE = """
--- a/utils.py
+++ b/utils.py
@@ -1,5 +1,10 @@
+from typing import List
+
 def calculate_total(items):
-    return sum(items)
+    # Added type hints and error handling
+    total = sum(item.price for item in items if item.price > 0)
+    return round(total, 2)
"""

async def test_vulnerable_code():
    """SQL injection içeren kodu test et"""
    print("\n" + "="*60)
    print("🔍 TEST 1: Güvenlik Açığı Testi")
    print("="*60)
    
    reviewer = AIReviewer(provider="groq", model="llama-3.3-70b-versatile")
    
    result = await reviewer.review(
        diff=VULNERABLE_CODE,
        files_changed=["auth.py"],
        focus_areas=["security", "bugs", "best_practices"]
    )
    
    print(f"\n📊 Sonuçlar:")
    print(f"   Skor: {result.score}/10")
    print(f"   Toplam Sorun: {result.total_issues}")
    print(f"   🔴 Critical: {result.critical_count}")
    print(f"   🟠 High: {result.high_count}")
    print(f"   🟡 Medium: {result.medium_count}")
    print(f"   Merge Engellensin mi: {'❌ EVET' if result.block_merge else '✅ Hayır'}")
    
    print(f"\n💬 Özet:")
    print(f"   {result.summary}")
    
    if result.issues:
        print(f"\n⚠️  Bulunan Sorunlar:")
        for i, issue in enumerate(result.issues[:3], 1):
            print(f"\n   {i}. [{issue.severity.upper()}] {issue.title}")
            print(f"      📄 Dosya: {issue.file_path} (Satır: {issue.line_number})")
            print(f"      📝 {issue.description[:100]}...")
            if issue.suggestion:
                print(f"      💡 Öneri: {issue.suggestion[:100]}...")
    
    return result

async def test_good_code():
    """İyi kod örneğini test et"""
    print("\n" + "="*60)
    print("🔍 TEST 2: İyi Kod Testi")
    print("="*60)
    
    reviewer = AIReviewer(provider="groq", model="llama-3.3-70b-versatile")
    
    result = await reviewer.review(
        diff=GOOD_CODE,
        files_changed=["utils.py"],
        focus_areas=["code_quality", "best_practices"]
    )
    
    print(f"\n📊 Sonuçlar:")
    print(f"   Skor: {result.score}/10")
    print(f"   Toplam Sorun: {result.total_issues}")
    print(f"   Onaylanabilir: {'✅ EVET' if result.approval_recommended else '❌ Hayır'}")
    
    print(f"\n💬 Özet:")
    print(f"   {result.summary}")
    
    return result

async def main():
    print("\n🤖 MCP Server - Groq LLM AI Review Test")
    print("=" * 60)
    
    try:
        # Test 1: Güvenlik açığı
        result1 = await test_vulnerable_code()
        
        # Test 2: İyi kod
        result2 = await test_good_code()
        
        print("\n" + "="*60)
        print("✅ TÜM TESTLER TAMAMLANDI!")
        print("="*60)
        print(f"\n🎯 Sonuç:")
        print(f"   Groq LLM başarıyla çalışıyor! ✅")
        print(f"   SQL injection tespit edildi: {'✅' if result1.critical_count > 0 else '❌'}")
        print(f"   İyi kod yüksek puan aldı: {'✅' if result2.score >= 7 else '❌'}")
        
    except Exception as e:
        print(f"\n❌ HATA: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())

