"""
MCP Tools for manual code review
"""
import json
import structlog
from typing import List

try:
    from mcp.types import Tool
except ImportError:
    from dataclasses import dataclass
    from typing import Any

    @dataclass
    class Tool:  # type: ignore[override]
        name: str
        description: str
        inputSchema: dict[str, Any]

logger = structlog.get_logger()


class ReviewTools:
    """MCP tools for code review"""
    
    def __init__(self, ai_reviewer, diff_analyzer):
        self.ai_reviewer = ai_reviewer
        self.diff_analyzer = diff_analyzer
    
    def get_tools(self) -> List[Tool]:
        """Return available MCP tools"""
        return [
            Tool(
                name="review_code",
                description="Review a code snippet or diff and provide AI-powered feedback with security, compilation, performance and best-practice analysis",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "code": {
                            "type": "string",
                            "description": "Code snippet or diff to review"
                        },
                        "file_path": {
                            "type": "string",
                            "description": "Original file path (e.g. 'Services/UserService.cs'). Helps AI give context-aware feedback."
                        },
                        "provider": {
                            "type": "string",
                            "description": "AI provider override (openai, anthropic, groq). If omitted, uses server config."
                        },
                        "model": {
                            "type": "string",
                            "description": "Model override (provider-specific)."
                        },
                        "language": {
                            "type": "string",
                            "description": "Programming language (e.g. csharp, python, typescript). Auto-detected from file_path if omitted.",
                            "default": "auto"
                        },
                        "focus": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Focus areas: compilation, security, performance, bugs, best_practices, code_quality",
                            "default": ["compilation", "security", "bugs", "performance", "best_practices"]
                        }
                    },
                    "required": ["code"]
                }
            ),
            Tool(
                name="review_file",
                description="Perform a thorough review of a complete source file — ideal for reviewing .cs, .py, .ts, .js, .go files from an IDE like Rider or VS Code",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "code": {
                            "type": "string",
                            "description": "Full file content to review"
                        },
                        "file_path": {
                            "type": "string",
                            "description": "File path (e.g. 'Controllers/UserController.cs'). Used for context and language detection."
                        },
                        "provider": {
                            "type": "string",
                            "description": "AI provider override (openai, anthropic, groq). If omitted, uses server config."
                        },
                        "model": {
                            "type": "string",
                            "description": "Model override (provider-specific)."
                        },
                        "language": {
                            "type": "string",
                            "description": "Programming language (e.g. csharp, python, typescript). Auto-detected from file_path if omitted.",
                            "default": "auto"
                        },
                        "focus": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Focus areas: compilation, security, performance, bugs, best_practices, code_quality",
                            "default": ["compilation", "security", "bugs", "performance", "best_practices"]
                        }
                    },
                    "required": ["code"]
                }
            ),
            Tool(
                name="analyze_diff",
                description="Analyze git diff and provide statistics",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "diff": {
                            "type": "string",
                            "description": "Git diff in unified format"
                        }
                    },
                    "required": ["diff"]
                }
            ),
            Tool(
                name="security_scan",
                description="Deep security scan using OWASP Top 10 framework — finds SQL injection, XSS, hardcoded secrets, insecure deserialization and more",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "code": {
                            "type": "string",
                            "description": "Code to scan for security issues"
                        },
                        "file_path": {
                            "type": "string",
                            "description": "File path for context (e.g. 'Repositories/OrderRepo.cs')"
                        },
                        "provider": {
                            "type": "string",
                            "description": "AI provider override (openai, anthropic, groq). If omitted, uses server config."
                        },
                        "model": {
                            "type": "string",
                            "description": "Model override (provider-specific)."
                        },
                        "language": {
                            "type": "string",
                            "description": "Programming language"
                        }
                    },
                    "required": ["code"]
                }
            )
        ]
    
    async def execute_tool(self, name: str, arguments: dict) -> str:
        """Execute a tool"""
        try:
            if name == "review_code":
                return await self._review_code(arguments)
            elif name == "review_file":
                return await self._review_file(arguments)
            elif name == "analyze_diff":
                return await self._analyze_diff(arguments)
            elif name == "security_scan":
                return await self._security_scan(arguments)
            else:
                return json.dumps({"error": f"Unknown tool: {name}"})
        except Exception as e:
            logger.exception("tool_execution_failed", tool=name, error=str(e))
            return json.dumps({"error": str(e)})

    @staticmethod
    def _detect_language(file_path: str | None, language: str | None) -> str:
        """Detect language from file_path or explicit parameter."""
        if language and language != "auto":
            return language
        if file_path:
            from services.language_detector import LanguageDetector
            detected = LanguageDetector.detect_from_files([file_path])
            if detected:
                return detected
        return "auto"

    async def _review_code(self, args: dict) -> str:
        """Review code — uses file review for standalone code, diff review for diffs"""
        code = args['code']
        file_path = args.get('file_path', '')
        language = self._detect_language(file_path, args.get('language'))
        focus = args.get('focus', ['compilation', 'security', 'bugs', 'performance', 'best_practices'])
        provider = args.get("provider")
        model = args.get("model")

        is_diff = code.lstrip().startswith(('diff --git', '--- a/', '+++ b/', '@@'))

        if is_diff:
            review_result = await self.ai_reviewer.review(
                diff=code,
                files_changed=[file_path] if file_path else [f"code.{language}"],
                focus_areas=focus,
                provider=provider,
                model=model,
            )
        else:
            review_result = await self.ai_reviewer.review_file(
                code=code,
                file_path=file_path or f"code.{language}",
                language=language,
                focus_areas=focus,
                provider=provider,
                model=model,
            )
        
        result = {
            "ai_provider": getattr(self.ai_reviewer, "last_provider_used", None),
            "ai_model": getattr(self.ai_reviewer, "last_model_used", None),
            "summary": review_result.summary,
            "score": review_result.score,
            "total_issues": review_result.total_issues,
            "critical_count": review_result.critical_count,
            "high_count": review_result.high_count,
            "block_merge": review_result.block_merge,
            "ai_slop_detected": review_result.ai_slop_detected,
            "security_score": review_result.security_score,
            "issues": [
                {
                    "severity": issue.severity.value,
                    "title": issue.title,
                    "description": issue.description,
                    "file_path": issue.file_path,
                    "line_number": issue.line_number,
                    "code_snippet": issue.code_snippet,
                    "category": issue.category,
                    "suggestion": issue.suggestion,
                }
                for issue in review_result.issues
            ]
        }
        
        return json.dumps(result, indent=2, ensure_ascii=False)

    async def _review_file(self, args: dict) -> str:
        """Full file review — thorough standalone file analysis"""
        code = args['code']
        file_path = args.get('file_path', '')
        language = self._detect_language(file_path, args.get('language'))
        focus = args.get('focus', ['compilation', 'security', 'bugs', 'performance', 'best_practices'])
        provider = args.get("provider")
        model = args.get("model")

        review_result = await self.ai_reviewer.review_file(
            code=code,
            file_path=file_path or f"code.{language}",
            language=language,
            focus_areas=focus,
            provider=provider,
            model=model,
        )

        result = {
            "ai_provider": getattr(self.ai_reviewer, "last_provider_used", None),
            "ai_model": getattr(self.ai_reviewer, "last_model_used", None),
            "file_path": file_path,
            "language": language,
            "summary": review_result.summary,
            "score": review_result.score,
            "total_issues": review_result.total_issues,
            "critical_count": review_result.critical_count,
            "high_count": review_result.high_count,
            "medium_count": review_result.medium_count,
            "low_count": review_result.low_count,
            "block_merge": review_result.block_merge,
            "ai_slop_detected": review_result.ai_slop_detected,
            "ai_slop_count": review_result.ai_slop_count,
            "security_score": review_result.security_score,
            "security_issues_count": review_result.security_issues_count,
            "owasp_categories_hit": review_result.owasp_categories_hit,
            "issues": [
                {
                    "severity": issue.severity.value,
                    "title": issue.title,
                    "description": issue.description,
                    "file_path": issue.file_path,
                    "line_number": issue.line_number,
                    "line_end": issue.line_end,
                    "code_snippet": issue.code_snippet,
                    "category": issue.category,
                    "suggestion": issue.suggestion,
                    "owasp_id": issue.owasp_id,
                    "cwe_id": issue.cwe_id,
                    "threat_type": issue.threat_type,
                }
                for issue in review_result.issues
            ],
        }

        return json.dumps(result, indent=2, ensure_ascii=False)
    
    async def _analyze_diff(self, args: dict) -> str:
        """Analyze git diff"""
        diff = args['diff']
        
        diff_info = self.diff_analyzer.parse_diff(diff)
        
        files = diff_info['files']
        file_stats = self.diff_analyzer.get_file_extension_stats([f['path'] for f in files])
        
        result = {
            "summary": {
                "files_changed": diff_info['files_count'],
                "additions": diff_info['total_additions'],
                "deletions": diff_info['total_deletions'],
                "net_change": diff_info['total_additions'] - diff_info['total_deletions']
            },
            "file_types": file_stats,
            "files": [
                {
                    "path": f['path'],
                    "additions": f['additions'],
                    "deletions": f['deletions'],
                    "is_new": f['is_new'],
                    "is_deleted": f['is_deleted']
                }
                for f in files
            ]
        }
        
        return json.dumps(result, indent=2)
    
    async def _security_scan(self, args: dict) -> str:
        """Focused security scan"""
        code = args['code']
        file_path = args.get('file_path', '')
        language = self._detect_language(file_path, args.get('language'))
        provider = args.get("provider")
        model = args.get("model")
        
        review_result = await self.ai_reviewer.review_file(
            code=code,
            file_path=file_path or f"code.{language}",
            language=language,
            focus_areas=['security'],
            provider=provider,
            model=model,
        )
        
        security_issues = [
            issue for issue in review_result.issues
            if issue.category == 'security'
        ]
        
        result = {
            "ai_provider": getattr(self.ai_reviewer, "last_provider_used", None),
            "ai_model": getattr(self.ai_reviewer, "last_model_used", None),
            "security_score": review_result.security_score,
            "vulnerabilities_found": len(security_issues),
            "critical_count": sum(1 for i in security_issues if i.severity.value == 'critical'),
            "high_count": sum(1 for i in security_issues if i.severity.value == 'high'),
            "owasp_categories_hit": review_result.owasp_categories_hit,
            "secret_leak_detected": review_result.secret_leak_detected,
            "issues": [
                {
                    "severity": issue.severity.value,
                    "title": issue.title,
                    "description": issue.description,
                    "file_path": issue.file_path,
                    "line_number": issue.line_number,
                    "code_snippet": issue.code_snippet,
                    "suggestion": issue.suggestion,
                    "owasp_id": issue.owasp_id,
                    "cwe_id": issue.cwe_id,
                    "threat_type": issue.threat_type,
                }
                for issue in security_issues
            ]
        }
        
        return json.dumps(result, indent=2, ensure_ascii=False)
