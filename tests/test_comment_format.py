#!/usr/bin/env python3
"""
Comment format testi - Detaylı tablo özelliğini test eder
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from models import ReviewResult, ReviewIssue, IssueSeverity
from services import CommentService

# Mock review result oluştur
def create_mock_review_result():
    """Test için mock review result"""
    issues = [
        # Critical issues
        ReviewIssue(
            severity=IssueSeverity.CRITICAL,
            title="SQL Injection vulnerability",
            description="User input is directly concatenated into SQL query",
            file_path="api/users.py",
            line_number=45,
            suggestion="Use parameterized queries",
            category="security"
        ),
        ReviewIssue(
            severity=IssueSeverity.CRITICAL,
            title="Null pointer dereference",
            description="Variable can be null at this point",
            file_path="core/processor.py",
            line_number=123,
            suggestion="Add null check before usage",
            category="reliability"
        ),
        
        # High severity issues
        ReviewIssue(
            severity=IssueSeverity.HIGH,
            title="Hardcoded credentials",
            description="API key is hardcoded in source code",
            file_path="config/settings.py",
            line_number=12,
            suggestion="Use environment variables",
            category="security"
        ),
        ReviewIssue(
            severity=IssueSeverity.HIGH,
            title="Memory leak detected",
            description="Connection not properly closed",
            file_path="db/connection.py",
            line_number=89,
            suggestion="Use context manager or finally block",
            category="performance"
        ),
        ReviewIssue(
            severity=IssueSeverity.HIGH,
            title="Magic numbers",
            description="Hardcoded values without explanation",
            file_path="utils/calculator.py",
            line_number=34,
            suggestion="Extract to named constants",
            category="maintainability"
        ),
        
        # Medium severity issues
        ReviewIssue(
            severity=IssueSeverity.MEDIUM,
            title="Missing error handling",
            description="Exception not caught",
            file_path="services/api.py",
            line_number=67,
            suggestion="Add try-catch block",
            category="reliability"
        ),
        ReviewIssue(
            severity=IssueSeverity.MEDIUM,
            title="Code duplication",
            description="Same logic repeated in multiple places",
            file_path="handlers/users.py",
            line_number=45,
            suggestion="Extract to reusable function",
            category="best_practices"
        ),
        ReviewIssue(
            severity=IssueSeverity.MEDIUM,
            title="Inefficient algorithm",
            description="O(n²) complexity can be optimized",
            file_path="utils/sorter.py",
            line_number=23,
            suggestion="Use built-in sort function",
            category="performance"
        ),
    ]
    
    result = ReviewResult(
        summary="Code review completed. Found critical security and reliability issues that must be addressed before merge.",
        score=6,
        issues=issues,
        approval_recommended=False,
        block_merge=True
    )
    
    return result

def main():
    print("\n" + "="*80)
    print("🧪 Comment Format Test - Detaylı Tablo Özelliği")
    print("="*80)
    
    comment_service = CommentService()
    review_result = create_mock_review_result()
    
    # Test 1: Detaylı tablo ile (master branch için)
    print("\n📊 Test 1: master/preprod branch için (DETAYLI TABLO VAR)")
    print("="*80)
    
    comment_with_table = comment_service.format_summary_comment(
        review_result, 
        show_detailed_table=True
    )
    
    print(comment_with_table)
    print("\n" + "="*80)
    
    # Test 2: Detaylı tablo olmadan (diğer branch'ler için)
    print("\n📝 Test 2: develop/feature branch için (DETAYLI TABLO YOK)")
    print("="*80)
    
    comment_without_table = comment_service.format_summary_comment(
        review_result, 
        show_detailed_table=False
    )
    
    print(comment_without_table)
    print("\n" + "="*80)
    
    # Farkı göster
    print("\n🔍 FARK ANALİZİ:")
    print("-"*80)
    print(f"Detaylı tablo ile: {len(comment_with_table)} karakter")
    print(f"Detaylı tablo olmadan: {len(comment_without_table)} karakter")
    print(f"Fark: {len(comment_with_table) - len(comment_without_table)} karakter")
    print()
    
    # Issue breakdown göster
    print("📊 Issue Dağılımı:")
    print(f"  🔴 Critical: {review_result.critical_count}")
    print(f"    - Security: 1")
    print(f"    - Reliability: 1")
    print(f"  🟠 Major/High: {review_result.high_count}")
    print(f"    - Security: 1")
    print(f"    - Maintainability: 1")
    print(f"    - Reliability: 1")
    print(f"  🟡 Minor/Medium: {review_result.medium_count}")
    print(f"    - Reliability: 1")
    print(f"    - Maintainability: 1")
    print(f"    - Reliability: 1")
    
    print("\n✅ Test tamamlandı!")
    print("="*80)

if __name__ == "__main__":
    main()

