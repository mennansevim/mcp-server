"""
Inject realistic mock data into LiveLogStore and AnalyticsStore for demo/screenshots.
"""
from __future__ import annotations
import time
import random
from models.schemas import ReviewResult, ReviewIssue, IssueSeverity


MOCK_PRS = [
    {"platform": "github", "pr_id": "PR-142", "title": "feat: Add user authentication module",
     "author": "sevim.mennano", "repo": "mennano/backend-api",
     "source_branch": "feature/auth", "target_branch": "main"},
    {"platform": "github", "pr_id": "PR-138", "title": "fix: Resolve SQL injection in search endpoint",
     "author": "ahmet.yilmaz", "repo": "mennano/backend-api",
     "source_branch": "fix/sql-injection", "target_branch": "main"},
    {"platform": "gitlab", "pr_id": "MR-87", "title": "refactor: Migrate payment service to async",
     "author": "elif.demir", "repo": "mennano/payment-service",
     "source_branch": "refactor/async-payments", "target_branch": "develop"},
    {"platform": "bitbucket", "pr_id": "PR-56", "title": "feat: Add Redis caching layer",
     "author": "can.ozturk", "repo": "mennano/order-service",
     "source_branch": "feature/redis-cache", "target_branch": "main"},
    {"platform": "azure_devops", "pr_id": "PR-203", "title": "chore: Update dependencies & fix CVEs",
     "author": "zeynep.kaya", "repo": "mennano/infra-tools",
     "source_branch": "chore/dep-update", "target_branch": "main"},
    {"platform": "github", "pr_id": "PR-145", "title": "feat: Implement WebSocket notification system",
     "author": "sevim.mennano", "repo": "mennano/backend-api",
     "source_branch": "feature/ws-notifications", "target_branch": "main"},
    {"platform": "gitlab", "pr_id": "MR-91", "title": "fix: XSS vulnerability in user profile page",
     "author": "mehmet.arslan", "repo": "mennano/web-frontend",
     "source_branch": "fix/xss-profile", "target_branch": "main"},
    {"platform": "github", "pr_id": "PR-148", "title": "feat: Add rate limiting middleware",
     "author": "ahmet.yilmaz", "repo": "mennano/backend-api",
     "source_branch": "feature/rate-limit", "target_branch": "main"},
]

REVIEW_SCENARIOS = [
    {
        "summary": "Critical SQL injection found in search endpoint. Hardcoded DB password detected. AI-generated boilerplate code identified.",
        "score": 3,
        "issues": [
            ReviewIssue(severity=IssueSeverity.CRITICAL, title="SQL Injection in search query",
                       description="User input directly concatenated into SQL query without parameterization.",
                       file_path="src/services/search_service.py", line_number=45, category="injection",
                       owasp_id="A3", cwe_id="CWE-89", threat_type="injection",
                       suggestion="Use parameterized queries with SQLAlchemy ORM."),
            ReviewIssue(severity=IssueSeverity.CRITICAL, title="Hardcoded database password",
                       description="Database connection string with plaintext password found in source code.",
                       file_path="src/config/database.py", line_number=12, category="secret_leak",
                       owasp_id="A2", cwe_id="CWE-798", threat_type="cryptographic_failures",
                       suggestion="Move to environment variables or a secrets manager."),
            ReviewIssue(severity=IssueSeverity.HIGH, title="Missing input validation on search parameter",
                       description="No length or format validation on user-provided search string.",
                       file_path="src/api/search.py", line_number=28, category="broken_access_control",
                       owasp_id="A1", threat_type="broken_access_control"),
            ReviewIssue(severity=IssueSeverity.MEDIUM, title="AI Slop: Redundant comments",
                       description="Comments that simply restate what the code does: '# Initialize the database connection'.",
                       file_path="src/config/database.py", line_number=8, category="ai_slop"),
            ReviewIssue(severity=IssueSeverity.MEDIUM, title="AI Slop: Generic variable naming",
                       description="Variables named 'data', 'result', 'temp' reduce code readability.",
                       file_path="src/services/search_service.py", line_number=32, category="ai_slop"),
            ReviewIssue(severity=IssueSeverity.LOW, title="Missing docstring",
                       description="Public function lacks documentation.", file_path="src/api/search.py",
                       line_number=15, category="maintainability"),
        ]
    },
    {
        "summary": "Clean refactoring with minor async pattern issues. Good security posture.",
        "score": 8,
        "issues": [
            ReviewIssue(severity=IssueSeverity.MEDIUM, title="Mixed async patterns",
                       description="File uses both callback and async/await patterns inconsistently.",
                       file_path="src/services/payment.py", line_number=67, category="ai_slop"),
            ReviewIssue(severity=IssueSeverity.LOW, title="Unused import",
                       description="'asyncio.sleep' imported but never used.",
                       file_path="src/services/payment.py", line_number=3, category="maintainability"),
        ]
    },
    {
        "summary": "Redis integration looks solid. Minor configuration concerns.",
        "score": 7,
        "issues": [
            ReviewIssue(severity=IssueSeverity.HIGH, title="Redis connection without TLS",
                       description="Redis client connects without encryption, exposing data in transit.",
                       file_path="src/cache/redis_client.py", line_number=15, category="security_misconfiguration",
                       owasp_id="A5", threat_type="security_misconfiguration",
                       suggestion="Enable TLS on Redis connection."),
            ReviewIssue(severity=IssueSeverity.MEDIUM, title="No TTL on cache entries",
                       description="Cache entries set without expiration may cause memory issues.",
                       file_path="src/cache/redis_client.py", line_number=42, category="performance"),
            ReviewIssue(severity=IssueSeverity.LOW, title="AI Slop: TODO scaffold",
                       description="TODO: implement error handling — incomplete scaffold code.",
                       file_path="src/cache/redis_client.py", line_number=55, category="ai_slop"),
        ]
    },
    {
        "summary": "Dependency updates look good. One known CVE still present in transitive dependency.",
        "score": 9,
        "issues": [
            ReviewIssue(severity=IssueSeverity.MEDIUM, title="Outdated cryptography package",
                       description="cryptography==3.4.6 has known CVE-2023-23931.",
                       file_path="requirements.txt", line_number=12, category="vulnerable_components",
                       owasp_id="A6", threat_type="vulnerable_components",
                       suggestion="Upgrade to cryptography>=41.0.0."),
        ]
    },
    {
        "summary": "WebSocket implementation has SSRF risk and missing auth. AI slop patterns detected in generated code.",
        "score": 4,
        "issues": [
            ReviewIssue(severity=IssueSeverity.CRITICAL, title="SSRF via WebSocket proxy endpoint",
                       description="User-controlled URL passed to internal HTTP client without validation. Attacker could access internal services or cloud metadata.",
                       file_path="src/ws/proxy.py", line_number=23, category="ssrf",
                       owasp_id="A10", cwe_id="CWE-918", threat_type="ssrf",
                       suggestion="Validate URL against allowlist, block internal/private IP ranges."),
            ReviewIssue(severity=IssueSeverity.HIGH, title="Missing WebSocket authentication",
                       description="WebSocket connections accepted without token verification.",
                       file_path="src/ws/handler.py", line_number=10, category="authentication",
                       owasp_id="A7", threat_type="auth_failures",
                       suggestion="Verify JWT token in WebSocket handshake."),
            ReviewIssue(severity=IssueSeverity.HIGH, title="No rate limiting on WebSocket messages",
                       description="Clients can send unlimited messages, enabling DoS.",
                       file_path="src/ws/handler.py", line_number=35, category="insecure_design",
                       owasp_id="A4", threat_type="insecure_design"),
            ReviewIssue(severity=IssueSeverity.MEDIUM, title="AI Slop: Hallucinated API call",
                       description="Using 'websocket.send_json_async()' which doesn't exist in the library.",
                       file_path="src/ws/handler.py", line_number=48, category="ai_slop"),
            ReviewIssue(severity=IssueSeverity.MEDIUM, title="AI Slop: Copy-paste duplication",
                       description="Same error handling block repeated 4 times, should be extracted.",
                       file_path="src/ws/handler.py", line_number=52, category="ai_slop"),
            ReviewIssue(severity=IssueSeverity.LOW, title="Logging sensitive data",
                       description="Connection tokens logged at INFO level.",
                       file_path="src/ws/handler.py", line_number=8, category="logging",
                       owasp_id="A9", threat_type="logging_failures"),
        ]
    },
    {
        "summary": "XSS fix is correct and comprehensive. Good use of DOMPurify.",
        "score": 9,
        "issues": [
            ReviewIssue(severity=IssueSeverity.LOW, title="Consider Content-Security-Policy header",
                       description="Adding CSP header would provide defense-in-depth against XSS.",
                       file_path="src/middleware/security.js", line_number=5, category="security_misconfiguration",
                       owasp_id="A5", threat_type="security_misconfiguration"),
        ]
    },
    {
        "summary": "Rate limiting implementation is solid. Token bucket algorithm well implemented.",
        "score": 8,
        "issues": [
            ReviewIssue(severity=IssueSeverity.MEDIUM, title="Rate limit bypass via X-Forwarded-For",
                       description="Rate limiting uses client IP from X-Forwarded-For header which can be spoofed.",
                       file_path="src/middleware/rate_limit.py", line_number=22, category="broken_access_control",
                       owasp_id="A1", threat_type="broken_access_control",
                       suggestion="Use the rightmost IP or configure trusted proxy count."),
            ReviewIssue(severity=IssueSeverity.LOW, title="Missing rate limit response headers",
                       description="X-RateLimit-Remaining and Retry-After headers not set.",
                       file_path="src/middleware/rate_limit.py", line_number=45, category="best_practices"),
        ]
    },
    {
        "summary": "Authentication module has critical broken access control. Emergency fix needed.",
        "score": 2,
        "issues": [
            ReviewIssue(severity=IssueSeverity.CRITICAL, title="Broken access control: Admin endpoint unprotected",
                       description="GET /api/admin/users accessible without authentication, leaking all user data.",
                       file_path="src/api/admin.py", line_number=15, category="broken_access_control",
                       owasp_id="A1", cwe_id="CWE-862", threat_type="broken_access_control"),
            ReviewIssue(severity=IssueSeverity.CRITICAL, title="JWT secret key hardcoded",
                       description="JWT signing key 'super-secret-key-123' found in source code.",
                       file_path="src/auth/jwt_handler.py", line_number=8, category="secret_leak",
                       owasp_id="A2", cwe_id="CWE-798", threat_type="cryptographic_failures"),
            ReviewIssue(severity=IssueSeverity.HIGH, title="Password stored as MD5 hash",
                       description="MD5 is cryptographically broken. Use bcrypt or argon2.",
                       file_path="src/auth/password.py", line_number=22, category="cryptographic_failures",
                       owasp_id="A2", cwe_id="CWE-328", threat_type="cryptographic_failures"),
            ReviewIssue(severity=IssueSeverity.HIGH, title="No JWT token expiration",
                       description="JWT tokens issued without 'exp' claim, valid forever.",
                       file_path="src/auth/jwt_handler.py", line_number=30, category="authentication",
                       owasp_id="A7", threat_type="auth_failures"),
            ReviewIssue(severity=IssueSeverity.MEDIUM, title="AI Slop: Catch-all exception handler",
                       description="except Exception used without specific error handling.",
                       file_path="src/auth/jwt_handler.py", line_number=42, category="ai_slop"),
            ReviewIssue(severity=IssueSeverity.MEDIUM, title="Missing brute force protection",
                       description="No login attempt limiting. Attacker can try unlimited passwords.",
                       file_path="src/api/auth.py", line_number=35, category="insecure_design",
                       owasp_id="A4", threat_type="insecure_design"),
            ReviewIssue(severity=IssueSeverity.LOW, title="Login failures not logged",
                       description="Failed authentication attempts not recorded for monitoring.",
                       file_path="src/api/auth.py", line_number=40, category="logging",
                       owasp_id="A9", threat_type="logging_failures"),
        ]
    },
]

REVIEW_STEPS = [
    ("webhook_received", "Webhook received from {platform}", "info"),
    ("platform_detected", "Platform identified: {platform}", "info"),
    ("diff_fetched", "Diff fetched: {files} files, {bytes} bytes", "info"),
    ("language_detected", "Language detected: {lang}", "info"),
    ("rules_loaded", "Rules loaded: {rules} files ({lang}-specific)", "info"),
    ("ai_review_started", "AI review started with {provider} ({model})", "info"),
    ("security_scan", "OWASP Top 10 security scan in progress...", "info"),
    ("ai_slop_check", "AI slop detection running...", "info"),
    ("ai_review_completed", "AI review completed: score {score}/10, {issues} issues found", "info"),
    ("comment_posted", "Review comment posted to {platform} {pr_id}", "info"),
    ("status_updated", "PR status set to {status}", "info"),
]

PROVIDERS = [("groq", "llama-3.3-70b"), ("openai", "gpt-4o"), ("anthropic", "claude-3.5-sonnet")]
LANGUAGES = ["python", "typescript", "csharp", "java", "go"]


def inject_mock_data(live_logs, analytics):
    """Inject realistic mock data for demo screenshots."""

    for i, pr in enumerate(MOCK_PRS):
        scenario = REVIEW_SCENARIOS[i % len(REVIEW_SCENARIOS)]
        result = ReviewResult(
            summary=scenario["summary"],
            score=scenario["score"],
            issues=scenario["issues"],
        )

        provider, model = random.choice(PROVIDERS)
        lang = random.choice(LANGUAGES)
        files = random.randint(2, 12)
        diff_bytes = random.randint(1200, 8500)
        rules_count = random.randint(3, 7)

        run_id = live_logs.start_run(
            platform=pr["platform"],
            pr_id=pr["pr_id"],
            title=pr["title"],
            author=pr["author"],
            source_branch=pr.get("source_branch"),
            target_branch=pr.get("target_branch"),
            repo=pr.get("repo"),
        )

        fmt = {
            "platform": pr["platform"].replace("_", " ").title(),
            "files": files, "bytes": diff_bytes, "lang": lang.title(),
            "rules": rules_count, "provider": provider.title(), "model": model,
            "score": scenario["score"], "issues": result.total_issues,
            "pr_id": pr["pr_id"],
            "status": "failure ❌" if result.block_merge else "success ✅",
        }

        for step, msg_tpl, level in REVIEW_STEPS:
            live_logs.append_event(run_id, step=step, message=msg_tpl.format(**fmt), level=level)

        if i == 0:
            pass
        elif i == len(MOCK_PRS) - 1:
            live_logs.fail_run(run_id, error="AI provider timeout after 30s — retrying...")
        else:
            live_logs.complete_run(
                run_id,
                score=scenario["score"],
                issues=result.total_issues,
                critical=result.critical_count,
            )

        analytics.record_review(
            result,
            pr_id=pr["pr_id"],
            repo=pr.get("repo", ""),
            author=pr["author"],
            platform=pr["platform"],
        )
