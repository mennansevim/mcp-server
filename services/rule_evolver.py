"""
Rule Evolver — generates repo-specific rule markdown files from historical
review feedback patterns.

Uses FeedbackAnalyzer output + base rules + AI to produce a targeted
`rules/repo/{owner}_{repo}.md` file that gets highest priority during reviews.
"""

from __future__ import annotations

import json
import structlog
from pathlib import Path
from typing import Any, Optional, TYPE_CHECKING

from services.feedback_analyzer import FeedbackAnalyzer
from services.review_store import ReviewStore
from services.ai_providers import AIProviderRouter

if TYPE_CHECKING:
    from services.rules_service import RulesHelper

logger = structlog.get_logger()

REPO_RULES_DIR = Path(__file__).parent.parent / "rules" / "repo"


class RuleEvolver:
    """Evolves repo-specific review rules based on accumulated feedback."""

    EVOLUTION_PROMPT = """Sen bir kod review uzmanısın. Aşağıda bir yazılım deposu (repo) hakkında geçmiş review verilerinden çıkarılmış pattern analizi bulunuyor.

**Repo:** {repo}

## Feedback Analiz Raporu

### Kategori Frekansı (En sık bulunan sorun tipleri)
{category_frequency}

### Severity Dağılımı
{severity_distribution}

### OWASP Hit Frekansı
{owasp_frequency}

### Tehdit Tipi Frekansı
{threat_type_frequency}

### Dosya Hotspot'ları (En çok sorun çıkan dosyalar)
{file_hotspots}

### Dizin Hotspot'ları
{directory_hotspots}

### Tekrarlayan Sorun Başlıkları
{recurring_titles}

### Review İstatistikleri
{review_stats}

---

## Mevcut Temel Kurallar
{base_rules}

---

## Görev

Bu repo'nun geçmiş review verilerine dayanarak, **repo'ya özel review kuralları** oluştur. Kurallar şu formatta olmalı:

1. Her kural için öncelik seviyesi (CRITICAL, HIGH, MEDIUM, LOW)
2. Somut kod örnekleri (Bad/Good formatında) — bu repo'da sık görülen hatalara göre
3. Tekrarlayan pattern'lere özel uyarılar
4. Hotspot dosya/dizinler için ekstra dikkat kuralları

**Kurallar bu repo'nun zayıf noktalarına odaklanmalı.** Genel kuralları tekrarlama; sadece bu repo'nun verisinde öne çıkan ve tekrarlayan sorunlara yönelik spesifik kurallar yaz.

Markdown formatında döndür. Başka açıklama ekleme."""

    def __init__(
        self,
        *,
        ai_config: Optional[dict] = None,
        rules_helper: Optional["RulesHelper"] = None,
        store: Optional[ReviewStore] = None,
        analyzer: Optional[FeedbackAnalyzer] = None,
    ):
        if ai_config is None:
            ai_config = {
                "provider": "groq",
                "model": None,
                "temperature": 0.3,
                "max_tokens": 8000,
            }
        self.router = AIProviderRouter(ai_config)
        self.rules_helper = rules_helper
        self.store = store or ReviewStore()
        self.analyzer = analyzer or FeedbackAnalyzer(self.store)

    async def evolve(
        self,
        repo: str,
        *,
        max_issues: int = 200,
        force: bool = False,
    ) -> dict[str, Any]:
        """
        Generate or update repo-specific rules based on feedback data.

        Returns dict with status info and the generated rule file path.
        """
        review_count = self.store.get_repo_review_count(repo)
        if review_count == 0:
            logger.info("rule_evolve_skip_no_data", repo=repo)
            return {"status": "skipped", "reason": "no_review_data", "repo": repo}

        report = self.analyzer.analyze(repo, max_issues=max_issues)

        if report["total_issues_analyzed"] < 3 and not force:
            logger.info("rule_evolve_skip_insufficient", repo=repo, issues=report["total_issues_analyzed"])
            return {"status": "skipped", "reason": "insufficient_data", "repo": repo}

        base_rules = self._load_base_rules()

        prompt = self.EVOLUTION_PROMPT.format(
            repo=repo,
            category_frequency=json.dumps(report["category_frequency"], indent=2),
            severity_distribution=json.dumps(report["severity_distribution"], indent=2),
            owasp_frequency=json.dumps(report["owasp_frequency"], indent=2),
            threat_type_frequency=json.dumps(report["threat_type_frequency"], indent=2),
            file_hotspots=json.dumps(report["file_hotspots"], indent=2),
            directory_hotspots=json.dumps(report["directory_hotspots"], indent=2),
            recurring_titles=json.dumps(report["top_recurring_titles"], indent=2),
            review_stats=json.dumps(report["review_stats"], indent=2),
            base_rules=base_rules[:6000],
        )

        system_msg = "Sen bir kod review kuralları uzmanısın. Verilen feedback verilerine göre repo'ya özel kurallar üretiyorsun."
        provider_used, model_used, response = self.router.chat(
            system=system_msg, user=prompt
        )

        rule_path = self._save_rule(repo, response)

        logger.info(
            "rule_evolved",
            repo=repo,
            path=str(rule_path),
            provider=provider_used,
            model=model_used,
            issues_analyzed=report["total_issues_analyzed"],
        )

        return {
            "status": "evolved",
            "repo": repo,
            "rule_path": str(rule_path),
            "provider": provider_used,
            "model": model_used,
            "issues_analyzed": report["total_issues_analyzed"],
            "review_count": review_count,
        }

    def should_evolve(self, repo: str, trigger_every: int = 10) -> bool:
        """Check whether enough new reviews have accumulated to justify re-evolution."""
        count = self.store.get_repo_review_count(repo)
        if count == 0:
            return False
        rule_path = self._rule_path(repo)
        if not rule_path.exists():
            return count >= 3
        return count % trigger_every == 0

    def get_repo_rule(self, repo: str) -> Optional[str]:
        """Return the current repo-specific rule content, or None."""
        p = self._rule_path(repo)
        if p.exists():
            return p.read_text(encoding="utf-8")
        return None

    # -- helpers --------------------------------------------------------------

    def _rule_path(self, repo: str) -> Path:
        safe_name = repo.replace("/", "_").replace("\\", "_")
        return REPO_RULES_DIR / f"{safe_name}.md"

    def _save_rule(self, repo: str, content: str) -> Path:
        REPO_RULES_DIR.mkdir(parents=True, exist_ok=True)
        path = self._rule_path(repo)
        path.write_text(content, encoding="utf-8")
        return path

    def _load_base_rules(self) -> str:
        """Load a representative sample of base rules for context."""
        parts: list[str] = []
        if self.rules_helper:
            for name in ("security.md", "compilation.md", "best-practices.md"):
                content = self.rules_helper.get_rule(name)
                if content:
                    parts.append(content[:2000])
        else:
            rules_dir = Path(__file__).parent.parent / "rules"
            for name in ("security.md", "compilation.md", "best-practices.md"):
                p = rules_dir / name
                if p.exists():
                    parts.append(p.read_text(encoding="utf-8")[:2000])
        return "\n\n---\n\n".join(parts)
