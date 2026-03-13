"""
MCP Code Review Server
Platform-agnostic AI-powered code review via webhooks and MCP tools
"""
from __future__ import annotations

import os
import yaml
import structlog
from contextlib import asynccontextmanager
from copy import deepcopy
from pathlib import Path
from typing import Any
from fastapi import FastAPI, Request, HTTPException, Query
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv

# MCP SDK
try:
    from mcp.server import Server as MCPServer
    from mcp.server.sse import SseServerTransport
    from mcp.types import Tool, TextContent
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    MCPServer = None
    SseServerTransport = None
    Tool = Any  # type: ignore[assignment]
    TextContent = Any  # type: ignore[assignment]

# Local imports
from models import Platform, ReviewRequest
from webhook import WebhookHandler
from services import AIReviewer, DiffAnalyzer, CommentService
from services.rules_service import RulesHelper
from services.live_log_store import LiveLogStore
from services.ui_logs_config import parse_ui_logs_config
from services.analytics_store import AnalyticsStore
from tools import ReviewTools


# Load environment variables
load_dotenv()

# Configure logging
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()
    ]
)
logger = structlog.get_logger()

ALLOWED_COMMENT_STRATEGIES = {"summary", "inline", "both"}
ALLOWED_TEMPLATES = {"default", "detailed", "executive"}
AI_PROVIDER_MODELS: dict[str, list[str]] = {
    "openai": ["gpt-4o-mini", "gpt-4o", "gpt-4-turbo-preview"],
    "anthropic": ["claude-3-5-sonnet-20241022"],
    "groq": ["llama-3.3-70b-versatile", "llama-3.1-70b-versatile", "mixtral-8x7b-32768"],
}
ALLOWED_AI_PROVIDERS = set(AI_PROVIDER_MODELS.keys())
CONFIG_FILE_PATH = Path(os.getenv("CONFIG_FILE_PATH", "config.yaml"))
CONFIG_OVERRIDES_PATH = Path(os.getenv("CONFIG_OVERRIDES_PATH", "config.overrides.yaml"))


def _read_yaml_file(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as f:
        loaded = yaml.safe_load(f) or {}
    if not isinstance(loaded, dict):
        return {}
    return loaded


def _deep_merge_dict(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    result = deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = _deep_merge_dict(result[key], value)
        else:
            result[key] = deepcopy(value)
    return result


def load_runtime_config() -> dict[str, Any]:
    base = _read_yaml_file(CONFIG_FILE_PATH)
    overrides = _read_yaml_file(CONFIG_OVERRIDES_PATH)
    return _deep_merge_dict(base, overrides)


def extract_editable_config(raw_config: dict[str, Any]) -> dict[str, Any]:
    review_cfg = raw_config.get("review") or {}
    ui_cfg = raw_config.get("ui") or {}
    logs_cfg = ui_cfg.get("logs") or {}
    ai_cfg = raw_config.get("ai") or {}

    provider = str(ai_cfg.get("provider", "")).lower()
    providers_cfg = ai_cfg.get("providers")
    if (not provider or provider not in ALLOWED_AI_PROVIDERS) and isinstance(providers_cfg, list) and providers_cfg:
        primary = str(ai_cfg.get("primary") or "").lower()
        if primary in ALLOWED_AI_PROVIDERS:
            provider = primary
        else:
            first = providers_cfg[0]
            if isinstance(first, dict):
                provider = str(first.get("name", "")).lower()
    if not provider:
        provider = "openai"
    if provider not in ALLOWED_AI_PROVIDERS:
        provider = "openai"
    model = str(ai_cfg.get("model") or "")
    if not model and isinstance(providers_cfg, list):
        for item in providers_cfg:
            if not isinstance(item, dict):
                continue
            if str(item.get("name", "")).lower() == provider:
                model = str(item.get("model") or "")
                break
    if not model:
        model = AI_PROVIDER_MODELS[provider][0]
    if model not in AI_PROVIDER_MODELS[provider]:
        model = AI_PROVIDER_MODELS[provider][0]

    template_cfg = review_cfg.get("template") or {}
    template_name = template_cfg.get("name", "default") if isinstance(template_cfg, dict) else "default"
    if template_name not in ALLOWED_TEMPLATES:
        template_name = "default"

    return {
        "ui": {
            "logs": {
                "poll_interval_seconds": int(logs_cfg.get("poll_interval_seconds", 3)),
                "max_events_per_poll": int(logs_cfg.get("max_events_per_poll", 200)),
            }
        },
        "review": {
            "comment_strategy": review_cfg.get("comment_strategy", "summary"),
            "template": template_name,
            "focus": list(review_cfg.get("focus") or []),
        },
        "ai": {
            "provider": provider,
            "model": model,
        },
    }


def persist_editable_overrides(editable_config: dict[str, Any]) -> None:
    CONFIG_OVERRIDES_PATH.parent.mkdir(parents=True, exist_ok=True)
    with CONFIG_OVERRIDES_PATH.open("w", encoding="utf-8") as f:
        yaml.safe_dump(editable_config, f, allow_unicode=True, sort_keys=False)


# Load configuration
config = load_runtime_config()


class CodeReviewServer:
    """Main code review server"""
    
    def __init__(self):
        self.config = config
        self.webhook_handler = WebhookHandler()
        
        ai_config = config["ai"]
        self.rules_helper = RulesHelper()
        self.ai_reviewer = AIReviewer(ai_config=ai_config)
        
        self.diff_analyzer = DiffAnalyzer()
        self.analytics = AnalyticsStore()
      
        self.ui_logs_config = parse_ui_logs_config(self.config)
        self.live_logs = LiveLogStore(max_events_per_run=self.ui_logs_config.max_events_per_poll)
        template_config = config.get("review", {}).get("template")
        self.comment_service = CommentService(template_config=template_config)

        
        # Initialize platform adapters
        self.adapters = {}
        self._init_adapters()
        
        # MCP Tools
        self.review_tools = ReviewTools(self.ai_reviewer, self.diff_analyzer)
        
        logger.info("code_review_server_initialized")

    def update_runtime_config(self, updated_config: dict[str, Any]) -> dict[str, Any]:
        global config
        self.config = updated_config
        config = deepcopy(updated_config)
        self.ui_logs_config = parse_ui_logs_config(self.config)
        self.live_logs.set_max_events_per_run(self.ui_logs_config.max_events_per_poll)
        self.ai_reviewer = AIReviewer(ai_config=self.config.get("ai", {}))
        self.review_tools = ReviewTools(self.ai_reviewer, self.diff_analyzer)
        template_config = self.config.get("review", {}).get("template")
        self.comment_service = CommentService(template_config=template_config)
        return extract_editable_config(self.config)
    
    def _init_adapters(self):
        """Initialize enabled platform adapters"""
        platforms_config = self.config['platforms']
        
        if platforms_config.get('github', {}).get('enabled'):
            try:
                from adapters.github_adapter import GitHubAdapter
                self.adapters[Platform.GITHUB] = GitHubAdapter()
            except Exception as e:
                logger.warning("github_adapter_init_failed", error=str(e))
        
        if platforms_config.get('gitlab', {}).get('enabled'):
            try:
                from adapters.gitlab_adapter import GitLabAdapter
                self.adapters[Platform.GITLAB] = GitLabAdapter()
            except Exception as e:
                logger.warning("gitlab_adapter_init_failed", error=str(e))
        
        if platforms_config.get('bitbucket', {}).get('enabled'):
            try:
                from adapters.bitbucket_adapter import BitbucketAdapter
                self.adapters[Platform.BITBUCKET] = BitbucketAdapter()
            except Exception as e:
                logger.warning("bitbucket_adapter_init_failed", error=str(e))
        
        if platforms_config.get('azure', {}).get('enabled'):
            try:
                from adapters.azure_adapter import AzureAdapter
                self.adapters[Platform.AZURE] = AzureAdapter()
            except Exception as e:
                logger.warning("azure_adapter_init_failed", error=str(e))

    def _start_live_run(self, pr_data) -> str | None:
        try:
            return self.live_logs.start_run(
                platform=pr_data.platform.value,
                pr_id=str(pr_data.pr_id),
                title=pr_data.title,
                author=pr_data.author,
                source_branch=pr_data.source_branch,
                target_branch=pr_data.target_branch,
                repo=pr_data.repo_full_name,
            )
        except Exception as e:
            logger.warning("live_run_start_failed", error=str(e))
            return None

    def _emit_live_event(
        self,
        run_id: str | None,
        *,
        step: str,
        message: str,
        level: str = "info",
        meta: dict[str, Any] | None = None,
    ) -> None:
        if not run_id:
            return
        try:
            self.live_logs.append_event(
                run_id,
                step=step,
                message=message,
                level=level,
                meta=meta,
            )
        except Exception as e:
            logger.warning("live_event_append_failed", run_id=run_id, error=str(e))

    def _complete_live_run(self, run_id: str | None, *, score: int, issues: int, critical: int) -> None:
        if not run_id:
            return
        try:
            self.live_logs.complete_run(run_id, score=score, issues=issues, critical=critical)
        except Exception as e:
            logger.warning("live_run_complete_failed", run_id=run_id, error=str(e))

    def _fail_live_run(self, run_id: str | None, *, error: str) -> None:
        if not run_id:
            return
        try:
            self.live_logs.fail_run(run_id, error=error)
        except Exception as e:
            logger.warning("live_run_fail_failed", run_id=run_id, error=str(e))
    
    async def process_webhook(self, request: Request) -> dict:
        """
        Process incoming webhook from any platform

        Args:
            request: FastAPI request

        Returns:
            Response dict
        """
        run_id: str | None = None

        def out(
            message: str,
            *,
            step: str = "console",
            level: str = "info",
            meta: dict[str, Any] | None = None,
        ) -> None:
            print(message)
            self._emit_live_event(run_id, step=step, message=message, level=level, meta=meta)

        out("\n" + "=" * 80, step="console_banner")
        out("🔔 WEBHOOK RECEIVED", step="console_banner")
        out("=" * 80, step="console_banner")

        # Parse webhook
        pr_data = await self.webhook_handler.handle(request)

        if not pr_data:
            out("⚠️  Ignored: Not a PR event or unsupported platform", step="ignored", level="warning")
            out("=" * 80 + "\n", step="console_banner")
            return {"status": "ignored", "message": "Not a PR event or unsupported platform"}

        # Start live run before detailed prints so console lines are streamed to UI.
        run_id = self._start_live_run(pr_data)

        out(f"📦 Platform: {pr_data.platform.value.upper()}", step="console_header")
        out(f"🔗 PR #{pr_data.pr_id}: {pr_data.title}", step="console_header")
        out(f"👤 Author: {pr_data.author}", step="console_header")
        out(f"🌿 {pr_data.source_branch} → {pr_data.target_branch}", step="console_header")
        out("-" * 80, step="console_header")

        logger.info("processing_webhook", platform=pr_data.platform.value, pr_id=pr_data.pr_id)

        # Get platform adapter
        adapter = self.adapters.get(pr_data.platform)
        if not adapter:
            out(f"❌ ERROR: No adapter available for {pr_data.platform.value}", step="adapter", level="error")
            out("=" * 80 + "\n", step="console_banner")
            logger.error("no_adapter_available", platform=pr_data.platform.value)
            self._fail_live_run(run_id, error="Platform adapter not available")
            return {
                "status": "error",
                "message": "Platform adapter not available",
                "run_id": run_id,
                "pr_id": pr_data.pr_id,
                "platform": pr_data.platform.value,
            }

        try:
            # Fetch actual diff
            out("📥 Step 1/5: Fetching diff from platform...", step="step_1")
            diff = await adapter.fetch_diff(pr_data)
            if not diff:
                out("❌ Failed to fetch diff", step="step_1", level="error")
                out("=" * 80 + "\n", step="console_banner")
                logger.warning("no_diff_fetched", pr_id=pr_data.pr_id)
                self._fail_live_run(run_id, error="Failed to fetch diff")
                return {
                    "status": "error",
                    "message": "Failed to fetch diff",
                    "run_id": run_id,
                    "pr_id": pr_data.pr_id,
                    "platform": pr_data.platform.value,
                }
            out(f"✅ Diff fetched successfully ({len(diff)} bytes)", step="step_1", meta={"bytes": len(diff)})
            print()

            pr_data.diff = diff

            # Analyze diff
            out("🔍 Step 2/5: Analyzing diff...", step="step_2")
            diff_info = self.diff_analyzer.parse_diff(diff)
            pr_data.files_changed = [f["path"] for f in diff_info["files"]]
            out(
                f"✅ Found {len(pr_data.files_changed)} changed file(s):",
                step="step_2",
                meta={"files_count": len(pr_data.files_changed)},
            )
            for file in pr_data.files_changed[:5]:
                out(f"   📄 {file}", step="step_2_file")
            if len(pr_data.files_changed) > 5:
                out(f"   ... and {len(pr_data.files_changed) - 5} more", step="step_2_file")
            print()

            # Perform AI review
            out("🤖 Step 3/5: Starting AI code review...", step="step_3")
            review_config = self.config["review"]
            ai_cfg = self.config.get("ai", {})
            if isinstance(ai_cfg.get("providers"), list) and ai_cfg["providers"]:
                primary = ai_cfg.get("primary") or ai_cfg["providers"][0].get("name")
                model = None
                for p in ai_cfg["providers"]:
                    if (p.get("name") or "").lower() == (primary or "").lower():
                        model = p.get("model")
                        break
                out(f"   Provider: {str(primary).upper() if primary else 'UNKNOWN'}", step="step_3")
                out(f"   Model: {model}", step="step_3")
            else:
                out(f"   Provider: {ai_cfg.get('provider', 'groq').upper()}", step="step_3")
                out(f"   Model: {ai_cfg.get('model')}", step="step_3")
            out(f"   Focus areas: {', '.join(review_config.get('focus', []))}", step="step_3")
            print()

            review_result = await self.ai_reviewer.review(
                diff=diff,
                files_changed=pr_data.files_changed,
                focus_areas=review_config.get("focus", []),
            )

            out("✅ AI Review completed!", step="step_3")
            out(f"   Score: {review_result.score}/10", step="step_3")
            out(f"   Issues: {review_result.total_issues} total", step="step_3")
            if review_result.critical_count > 0:
                out(f"   🔴 Critical: {review_result.critical_count}", step="step_3")
            if review_result.high_count > 0:
                out(f"   🟠 High: {review_result.high_count}", step="step_3")
            if review_result.medium_count > 0:
                out(f"   🟡 Medium: {review_result.medium_count}", step="step_3")
            print()

            # Post comments based on strategy
            out("💬 Step 4/5: Posting review comments...", step="step_4")
            strategy = review_config.get("comment_strategy", "both")
            out(f"   Strategy: {strategy}", step="step_4")

            # Check if detailed table should be shown for this branch
            detailed_branches = review_config.get("detailed_analysis_branches", [])
            show_detailed_table = pr_data.target_branch in detailed_branches

            if show_detailed_table:
                out(
                    f"   📊 Detailed analysis table enabled for target branch: {pr_data.target_branch}",
                    step="step_4",
                )

            if strategy in ["summary", "both"]:
                out("   📝 Posting summary comment...", step="step_4")
                summary_comment = self.comment_service.format_summary_comment(
                    review_result,
                    show_detailed_table=show_detailed_table,
                )
                await adapter.post_summary_comment(pr_data, summary_comment)
                out("   ✅ Summary comment posted", step="step_4")

            if strategy in ["inline", "both"]:
                inline_comments = self.comment_service.format_inline_comments(review_result)
                if inline_comments:
                    out(f"   💭 Posting {len(inline_comments)} inline comment(s)...", step="step_4")
                    await adapter.post_inline_comments(pr_data, inline_comments)
                    out("   ✅ Inline comments posted", step="step_4")
            print()

            # Update status
            out("📊 Step 5/5: Updating PR status...", step="step_5")
            if review_result.block_merge:
                status_msg = "Critical issues found - merge blocked"
                out("   ❌ Status: FAILURE", step="step_5", level="error")
                out(f"   Message: {status_msg}", step="step_5", level="error")
                await adapter.update_status(pr_data, "failure", status_msg)
            elif review_result.score >= 8:
                status_msg = f"Code quality: {review_result.score}/10"
                out("   ✅ Status: SUCCESS", step="step_5")
                out(f"   Message: {status_msg}", step="step_5")
                await adapter.update_status(pr_data, "success", status_msg)
            else:
                status_msg = f"Review complete: {review_result.score}/10"
                out("   ✅ Status: SUCCESS", step="step_5")
                out(f"   Message: {status_msg}", step="step_5")
                await adapter.update_status(pr_data, "success", status_msg)
            print()

            logger.info(
                "review_completed",
                pr_id=pr_data.pr_id,
                score=review_result.score,
                issues=review_result.total_issues,
            )

            out("🎉 REVIEW COMPLETED SUCCESSFULLY", step="summary")
            out(f"   PR: #{pr_data.pr_id}", step="summary")
            out(f"   Score: {review_result.score}/10", step="summary")
            out(f"   Issues: {review_result.total_issues}", step="summary")
            out(
                f"   Status: {'BLOCKED' if review_result.block_merge else 'APPROVED' if review_result.score >= 8 else 'REVIEW NEEDED'}",
                step="summary",
            )
            out("=" * 80 + "\n", step="console_banner")
            self._complete_live_run(
                run_id,
                score=review_result.score,
                issues=review_result.total_issues,
                critical=review_result.critical_count,
            )
            self.analytics.record_review(
                review_result,
                pr_id=str(pr_data.pr_id),
                repo=pr_data.repo_full_name,
                author=pr_data.author,
                platform=pr_data.platform.value,
            )

            return {
                "status": "success",
                "pr_id": pr_data.pr_id,
                "run_id": run_id,
                "platform": pr_data.platform.value,
                "ai_provider": self.ai_reviewer.last_provider_used,
                "ai_model": self.ai_reviewer.last_model_used,
                "score": review_result.score,
                "issues": review_result.total_issues,
                "critical": review_result.critical_count,
            }

        except Exception as e:
            out("❌ ERROR during review process:", step="error", level="error")
            out(f"   {str(e)}", step="error", level="error")
            out("=" * 80 + "\n", step="console_banner")
            logger.exception("webhook_processing_failed", error=str(e))
            self._fail_live_run(run_id, error=str(e))
            return {
                "status": "error",
                "message": str(e),
                "run_id": run_id,
            }

# Create server instance
review_server = CodeReviewServer()

# FastAPI app
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    print("\n" + "="*80)
    print("🚀 MCP CODE REVIEW SERVER STARTING")
    print("="*80)
    print(f"📊 Version: 1.0.0")
    # Backward compatible display (legacy keys) + new multi-provider config
    ai_cfg = config.get("ai", {})
    if isinstance(ai_cfg.get("providers"), list) and ai_cfg["providers"]:
        providers = [p.get("name") for p in ai_cfg["providers"] if isinstance(p, dict)]
        print(f"🤖 AI Providers: {', '.join([str(p).upper() for p in providers if p])}")
        primary = ai_cfg.get("primary") or (providers[0] if providers else None)
        print(f"⭐ Primary: {str(primary).upper() if primary else 'UNKNOWN'}")
    else:
        print(f"🤖 AI Provider: {ai_cfg.get('provider', 'groq').upper()}")
        print(f"🧠 Model: {ai_cfg.get('model')}")
    print(f"🔌 Platforms: {', '.join([p.value for p in review_server.adapters.keys()])}")
    print(f"💬 Comment Strategy: {config['review']['comment_strategy']}")
    tmpl_name = config.get("review", {}).get("template", {}).get("name", "default")
    print(f"📄 Review Template: {tmpl_name}")
    print(f"🔍 Focus Areas: {', '.join(config['review']['focus'])}")
    print("="*80)
    print("✅ Server ready to receive webhooks!")
    print("="*80 + "\n")
    logger.info("server_starting")
    yield
    print("\n" + "="*80)
    print("🛑 SERVER SHUTTING DOWN")
    print("="*80 + "\n")
    logger.info("server_shutting_down")

app = FastAPI(
    title="MCP Code Review Server By Mennano",
    description="AI-powered code review with platform integration",
    version="1.0.0",
    lifespan=lifespan
)

UI_DIST_DIR = Path(__file__).resolve().parent / "ui" / "dist"

if UI_DIST_DIR.exists():
    assets_dir = UI_DIST_DIR / "assets"
    if assets_dir.exists():
        app.mount("/ui/assets", StaticFiles(directory=assets_dir), name="ui-assets")


def _resolve_ui_file(path: str) -> Path:
    target = (UI_DIST_DIR / path).resolve()
    if UI_DIST_DIR.resolve() not in target.parents and target != UI_DIST_DIR.resolve():
        raise HTTPException(status_code=404, detail="Not found")
    return target


@app.get("/ui")
async def ui_root():
    if not UI_DIST_DIR.exists():
        raise HTTPException(status_code=404, detail="UI build not found")
    return FileResponse(UI_DIST_DIR / "index.html")


@app.get("/ui/{path:path}")
async def ui_path(path: str):
    if not UI_DIST_DIR.exists():
        raise HTTPException(status_code=404, detail="UI build not found")

    requested = _resolve_ui_file(path)
    if requested.is_file():
        return FileResponse(requested)
    return FileResponse(UI_DIST_DIR / "index.html")


@app.get("/")
async def root():
    """Health check"""
    return {
        "name": "MCP Code Review Server By Mennano",
        "version": "1.0.0",
        "status": "healthy",
        "platforms": list(review_server.adapters.keys())
    }


@app.get("/rules")
async def rules_index(language: str | None = None, category: str | None = None):
    """List available rule files."""
    items = review_server.rules_helper.list_rules(language=language, category=category)
    return {"count": len(items), "rules": items}


@app.get("/rules/resolve")
async def rules_resolve(focus: list[str] = Query(default=[]), language: str | None = None):
    """Resolve which rules apply for focus areas + optional language."""
    return review_server.rules_helper.resolve_rules(focus_areas=focus, language=language)


@app.get("/rules/{filename}")
async def rules_get(filename: str):
    """Fetch a specific rule file content."""
    content = review_server.rules_helper.get_rule(filename)
    if content is None:
        raise HTTPException(status_code=404, detail="Rule not found")
    return {"filename": filename, "content": content}


@app.get("/templates")
async def list_templates():
    """List available review templates and current selection."""
    from review_templates import BUILTIN_TEMPLATES
    from pathlib import Path

    custom_dir = Path("custom_templates")
    custom_files = [f.name for f in custom_dir.glob("*.md")] if custom_dir.exists() else []

    return {
        "active": review_server.comment_service.template.name,
        "builtin": [
            {"name": t.name, "description": t.description}
            for t in (cls() for cls in BUILTIN_TEMPLATES.values())
        ],
        "custom_files": custom_files,
    }


@app.post("/templates/switch")
async def switch_template(body: dict):
    """
    Switch the active review template at runtime.
    Body: {"name": "detailed"} or {"name": "custom", "file": "my_team.md"}
    """
    from review_templates import get_template

    new_tmpl = get_template(body)
    review_server.comment_service.template = new_tmpl
    logger.info("template_switched", name=new_tmpl.name)
    return {"status": "ok", "active": new_tmpl.name}


@app.get("/api/logs/config")
async def logs_config():
    cfg = review_server.ui_logs_config
    return {
        "poll_interval_seconds": cfg.poll_interval_seconds,
        "max_events_per_poll": cfg.max_events_per_poll,
    }


@app.get("/api/config")
async def get_config():
    return extract_editable_config(review_server.config)


@app.put("/api/config")
async def put_config(payload: dict[str, Any]):
    current = extract_editable_config(review_server.config)
    merged = deepcopy(current)

    payload_ui = payload.get("ui") if isinstance(payload, dict) else None
    if isinstance(payload_ui, dict):
        payload_logs = payload_ui.get("logs")
        if isinstance(payload_logs, dict):
            if "poll_interval_seconds" in payload_logs:
                merged["ui"]["logs"]["poll_interval_seconds"] = int(payload_logs["poll_interval_seconds"])
            if "max_events_per_poll" in payload_logs:
                merged["ui"]["logs"]["max_events_per_poll"] = int(payload_logs["max_events_per_poll"])

    payload_review = payload.get("review") if isinstance(payload, dict) else None
    if isinstance(payload_review, dict):
        if "comment_strategy" in payload_review:
            strategy = str(payload_review["comment_strategy"])
            if strategy not in ALLOWED_COMMENT_STRATEGIES:
                raise HTTPException(status_code=400, detail="Invalid comment strategy")
            merged["review"]["comment_strategy"] = strategy

        if "template" in payload_review:
            tmpl = str(payload_review["template"]).lower()
            if tmpl not in ALLOWED_TEMPLATES:
                raise HTTPException(status_code=400, detail=f"Invalid template. Allowed: {', '.join(sorted(ALLOWED_TEMPLATES))}")
            merged["review"]["template"] = tmpl

        if "focus" in payload_review:
            focus = payload_review["focus"]
            if not isinstance(focus, list) or not all(isinstance(item, str) for item in focus):
                raise HTTPException(status_code=400, detail="review.focus must be a list of strings")
            merged["review"]["focus"] = [item.strip() for item in focus if item.strip()]

    payload_ai = payload.get("ai") if isinstance(payload, dict) else None
    provider_changed = False
    if isinstance(payload_ai, dict):
        if "provider" in payload_ai:
            provider = str(payload_ai["provider"]).lower()
            if provider not in ALLOWED_AI_PROVIDERS:
                raise HTTPException(status_code=400, detail="Invalid AI provider")
            provider_changed = provider != merged["ai"]["provider"]
            merged["ai"]["provider"] = provider

        if "model" in payload_ai:
            model = str(payload_ai["model"])
            if model not in AI_PROVIDER_MODELS[merged["ai"]["provider"]]:
                raise HTTPException(status_code=400, detail="Invalid AI model for provider")
            merged["ai"]["model"] = model

    if provider_changed and merged["ai"]["model"] not in AI_PROVIDER_MODELS[merged["ai"]["provider"]]:
        merged["ai"]["model"] = AI_PROVIDER_MODELS[merged["ai"]["provider"]][0]

    # Clamp UI logs config by existing parser rules.
    normalized_ui_logs = parse_ui_logs_config({"ui": {"logs": merged["ui"]["logs"]}})
    merged["ui"]["logs"]["poll_interval_seconds"] = normalized_ui_logs.poll_interval_seconds
    merged["ui"]["logs"]["max_events_per_poll"] = normalized_ui_logs.max_events_per_poll

    new_runtime_config = deepcopy(review_server.config)
    new_runtime_config.setdefault("ui", {}).setdefault("logs", {})
    new_runtime_config["ui"]["logs"]["poll_interval_seconds"] = merged["ui"]["logs"]["poll_interval_seconds"]
    new_runtime_config["ui"]["logs"]["max_events_per_poll"] = merged["ui"]["logs"]["max_events_per_poll"]

    new_runtime_config.setdefault("review", {})
    new_runtime_config["review"]["comment_strategy"] = merged["review"]["comment_strategy"]
    new_runtime_config["review"]["focus"] = merged["review"]["focus"]
    new_runtime_config["review"]["template"] = {"name": merged["review"]["template"]}
    new_runtime_config.setdefault("ai", {})
    new_runtime_config["ai"]["provider"] = merged["ai"]["provider"]
    new_runtime_config["ai"]["model"] = merged["ai"]["model"]

    # Keep multi-provider config in sync when present.
    providers_cfg = new_runtime_config["ai"].get("providers")
    if isinstance(providers_cfg, list):
        matched = False
        for item in providers_cfg:
            if not isinstance(item, dict):
                continue
            if str(item.get("name", "")).lower() == merged["ai"]["provider"]:
                item["model"] = merged["ai"]["model"]
                matched = True
        if not matched:
            providers_cfg.append({"name": merged["ai"]["provider"], "model": merged["ai"]["model"]})
        new_runtime_config["ai"]["primary"] = merged["ai"]["provider"]

    editable = review_server.update_runtime_config(new_runtime_config)
    try:
        persist_editable_overrides(editable)
    except OSError as e:
        raise HTTPException(status_code=500, detail=f"Failed to persist config: {e}") from e
    return editable


@app.get("/api/logs/active")
async def logs_active():
    runs = review_server.live_logs.list_active_runs()
    return {"count": len(runs), "runs": runs}


@app.get("/api/logs/runs")
async def logs_runs():
    runs = review_server.live_logs.list_runs()
    return {"count": len(runs), "runs": runs}


@app.get("/api/logs/runs/{run_id}/events")
async def logs_run_events(run_id: str, cursor: int = 0, limit: int = 200):
    try:
        run, events, next_cursor = review_server.live_logs.get_events_since(
            run_id,
            cursor=cursor,
            limit=limit,
        )
        return {
            "run": run,
            "events": events,
            "next_cursor": next_cursor,
        }
    except KeyError:
        raise HTTPException(status_code=404, detail="Run not found")


@app.get("/api/analytics/overview")
async def analytics_overview():
    return review_server.analytics.get_overview()


@app.get("/api/analytics/trend")
async def analytics_trend(limit: int = 50):
    return {"trend": review_server.analytics.get_score_trend(limit)}


@app.get("/api/analytics/top-issues")
async def analytics_top_issues(limit: int = 10):
    return {"top_issues": review_server.analytics.get_top_issues(limit)}


@app.get("/api/analytics/security")
async def analytics_security():
    return review_server.analytics.get_security_breakdown()


@app.get("/api/analytics/authors")
async def analytics_authors(limit: int = 20):
    return {"authors": review_server.analytics.get_author_stats(limit)}


@app.get("/api/analytics/recent")
async def analytics_recent(limit: int = 20):
    return {"reviews": review_server.analytics.get_recent_reviews(limit)}


@app.post("/webhook")
async def webhook_endpoint(request: Request):
    """
    Universal webhook endpoint - automatically detects platform
    """
    try:
        result = await review_server.process_webhook(request)
        return JSONResponse(content=result)
    except Exception as e:
        print("\n" + "="*80)
        print("❌ WEBHOOK ERROR")
        print("="*80)
        print(f"Error: {str(e)}")
        print("="*80 + "\n")
        logger.exception("webhook_error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/mcp/sse")
async def mcp_sse_endpoint(request: Request):
    """
    MCP Server-Sent Events endpoint for MCP clients
    """
    if not MCP_AVAILABLE:
        raise HTTPException(status_code=503, detail="MCP SDK is not installed in this environment")

    # Create MCP server
    mcp_server = MCPServer("code-review-server")
    
    # Register MCP tools
    @mcp_server.list_tools()
    async def list_tools() -> list[Tool]:
        return review_server.review_tools.get_tools()
    
    @mcp_server.call_tool()
    async def call_tool(name: str, arguments: dict) -> list[TextContent]:
        result = await review_server.review_tools.execute_tool(name, arguments)
        return [TextContent(type="text", text=result)]
    
    # Create SSE transport
    async with SseServerTransport("/mcp/messages") as transport:
        await mcp_server.connect(transport)
        await transport.handle_sse(request)


if __name__ == "__main__":
    import uvicorn
    
    server_config = config['server']
    uvicorn.run(
        app,
        host=server_config.get('host', '0.0.0.0'),
        port=server_config.get('port', 8000),
        log_level="info"
    )
