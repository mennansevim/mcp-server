"""
OWASP Top 10 Updater — fetches the latest OWASP Top 10 from the official
GitHub repository and generates a consolidated rules/owasp-top10.md file.

Primary source: https://github.com/OWASP/Top10  (2021 edition, A01–A10)
The updater pulls raw markdown content via the GitHub API and produces a
review-oriented rule file that the AI reviewer consumes dynamically.
"""

from __future__ import annotations

import json
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import requests
import structlog

logger = structlog.get_logger()

RULES_DIR = Path(__file__).parent.parent / "rules"
DATA_DIR = Path(__file__).parent.parent / "data"
OWASP_RULE_FILE = RULES_DIR / "owasp-top10.md"
OWASP_UPDATE_LOG = DATA_DIR / "owasp_update_log.json"

GITHUB_API = "https://api.github.com"
OWASP_REPO = "OWASP/Top10"
OWASP_CONTENT_PATH = "2021/docs"

OWASP_CATEGORIES = [
    ("A01_2021-Broken_Access_Control.md", "A01", "Broken Access Control"),
    ("A02_2021-Cryptographic_Failures.md", "A02", "Cryptographic Failures"),
    ("A03_2021-Injection.md", "A03", "Injection"),
    ("A04_2021-Insecure_Design.md", "A04", "Insecure Design"),
    ("A05_2021-Security_Misconfiguration.md", "A05", "Security Misconfiguration"),
    ("A06_2021-Vulnerable_and_Outdated_Components.md", "A06", "Vulnerable and Outdated Components"),
    ("A07_2021-Identification_and_Authentication_Failures.md", "A07", "Identification and Authentication Failures"),
    ("A08_2021-Software_and_Data_Integrity_Failures.md", "A08", "Software and Data Integrity Failures"),
    ("A09_2021-Security_Logging_and_Monitoring_Failures.md", "A09", "Security Logging and Monitoring Failures"),
    ("A10_2021-Server-Side_Request_Forgery_(SSRF).md", "A10", "Server-Side Request Forgery (SSRF)"),
]


class OWASPUpdater:
    """Fetches and consolidates the OWASP Top 10 into a single rule file."""

    def __init__(self, *, github_token: Optional[str] = None):
        self.session = requests.Session()
        self.session.headers["Accept"] = "application/vnd.github.v3+json"
        self.session.headers["User-Agent"] = "mcp-code-review-owasp-updater"
        if github_token:
            self.session.headers["Authorization"] = f"token {github_token}"

    def update(self, *, force: bool = False) -> dict[str, Any]:
        """
        Fetch latest OWASP Top 10 and regenerate rules/owasp-top10.md.

        Returns status dict with update details.
        """
        logger.info("owasp_update_start")

        sections: list[str] = []
        fetched_count = 0
        errors: list[str] = []

        for filename, code, title in OWASP_CATEGORIES:
            try:
                content = self._fetch_file(filename)
                if content:
                    section = self._parse_section(content, code, title)
                    sections.append(section)
                    fetched_count += 1
                else:
                    errors.append(f"{code}: empty response")
            except Exception as e:
                logger.warning("owasp_fetch_failed", category=code, error=str(e))
                errors.append(f"{code}: {e}")

        if fetched_count == 0:
            logger.error("owasp_update_failed_all")
            return {"status": "failed", "reason": "all_fetches_failed", "errors": errors}

        rule_content = self._build_rule_file(sections)

        self._backup_existing()
        RULES_DIR.mkdir(parents=True, exist_ok=True)
        OWASP_RULE_FILE.write_text(rule_content, encoding="utf-8")

        self._log_update(fetched_count, errors)

        logger.info("owasp_update_complete", fetched=fetched_count, errors=len(errors))
        return {
            "status": "updated",
            "fetched": fetched_count,
            "total": len(OWASP_CATEGORIES),
            "errors": errors,
            "rule_file": str(OWASP_RULE_FILE),
        }

    def get_current_version_info(self) -> Optional[dict[str, Any]]:
        """Return the last update log entry, or None."""
        if not OWASP_UPDATE_LOG.exists():
            return None
        try:
            data = json.loads(OWASP_UPDATE_LOG.read_text(encoding="utf-8"))
            entries = data.get("updates", [])
            return entries[-1] if entries else None
        except Exception:
            return None

    # -- internal helpers -----------------------------------------------------

    def _fetch_file(self, filename: str) -> Optional[str]:
        """Fetch a single OWASP markdown file from GitHub."""
        url = f"{GITHUB_API}/repos/{OWASP_REPO}/contents/{OWASP_CONTENT_PATH}/{filename}"
        resp = self.session.get(url, timeout=30)
        if resp.status_code == 404:
            logger.warning("owasp_file_not_found", filename=filename)
            return None
        resp.raise_for_status()

        data = resp.json()
        download_url = data.get("download_url")
        if not download_url:
            return None

        raw = self.session.get(download_url, timeout=30)
        raw.raise_for_status()
        return raw.text

    @staticmethod
    def _parse_section(raw_md: str, code: str, title: str) -> str:
        """Extract relevant content from an OWASP category markdown file."""
        lines = raw_md.strip().splitlines()

        description_lines: list[str] = []
        cwes: list[str] = []
        in_description = False

        for line in lines:
            stripped = line.strip()

            cwe_match = re.findall(r"CWE-\d+", stripped)
            if cwe_match:
                cwes.extend(cwe_match)

            if stripped.startswith("## Description") or stripped.startswith("## Overview"):
                in_description = True
                continue
            if in_description:
                if stripped.startswith("## "):
                    in_description = False
                    continue
                description_lines.append(line)

        description = "\n".join(description_lines).strip()
        if not description:
            description = "\n".join(lines[2:30]).strip()

        unique_cwes = sorted(set(cwes))

        section = f"### {code} — {title}\n\n"
        if unique_cwes:
            section += f"**Related CWEs:** {', '.join(unique_cwes)}\n\n"
        section += description[:2000]
        return section

    @staticmethod
    def _build_rule_file(sections: list[str]) -> str:
        now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        header = f"""# OWASP Top 10 — 2021 Edition (Review Rules)

> Auto-generated from the official OWASP/Top10 GitHub repository.
> Last updated: {now}
>
> These rules are injected into AI code reviews when security is a focus area.
> For the latest source see: https://github.com/OWASP/Top10

---

## How to Use in Reviews

For each security issue found, include:
- `category`: "security"
- `owasp_id`: The relevant OWASP category code (e.g. "A01", "A03")
- `cwe_id`: The most specific CWE identifier if known
- `threat_type`: One of injection, broken_auth, sensitive_data, xxe, broken_access,
  misconfig, xss, deserialization, vulnerable_deps, insufficient_logging, secret_leak

---

"""
        body = "\n\n---\n\n".join(sections)
        severity_table = """

---

## Severity Guidelines

| OWASP Category | Default Severity |
|----------------|-----------------|
| A01 — Broken Access Control | HIGH–CRITICAL |
| A02 — Cryptographic Failures | HIGH–CRITICAL |
| A03 — Injection | CRITICAL |
| A04 — Insecure Design | MEDIUM–HIGH |
| A05 — Security Misconfiguration | MEDIUM–HIGH |
| A06 — Vulnerable Components | MEDIUM–HIGH |
| A07 — Auth Failures | HIGH–CRITICAL |
| A08 — Integrity Failures | HIGH |
| A09 — Logging Failures | LOW–MEDIUM |
| A10 — SSRF | HIGH–CRITICAL |
"""
        return header + body + severity_table

    def _backup_existing(self) -> None:
        if OWASP_RULE_FILE.exists():
            ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            backup = OWASP_RULE_FILE.with_suffix(f".{ts}.bak.md")
            shutil.copy2(OWASP_RULE_FILE, backup)
            logger.info("owasp_backup_created", path=str(backup))

    def _log_update(self, fetched: int, errors: list[str]) -> None:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        log_data: dict[str, Any] = {"updates": []}
        if OWASP_UPDATE_LOG.exists():
            try:
                log_data = json.loads(OWASP_UPDATE_LOG.read_text(encoding="utf-8"))
            except Exception:
                pass

        log_data.setdefault("updates", []).append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "fetched": fetched,
            "total": len(OWASP_CATEGORIES),
            "errors": errors,
        })

        # Keep last 50 entries
        log_data["updates"] = log_data["updates"][-50:]
        OWASP_UPDATE_LOG.write_text(
            json.dumps(log_data, indent=2, ensure_ascii=False), encoding="utf-8"
        )
