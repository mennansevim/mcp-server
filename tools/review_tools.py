"""
MCP Tools for manual code review
"""
import json
import structlog
from typing import List
from mcp.types import Tool

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
                description="Review code snippet or diff and provide feedback",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "code": {
                            "type": "string",
                            "description": "Code snippet or diff to review"
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
                            "description": "Programming language (optional)",
                            "default": "auto"
                        },
                        "focus": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Focus areas: security, performance, bugs, style",
                            "default": ["security", "bugs", "performance"]
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
                description="Scan code for security vulnerabilities",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "code": {
                            "type": "string",
                            "description": "Code to scan for security issues"
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
            elif name == "analyze_diff":
                return await self._analyze_diff(arguments)
            elif name == "security_scan":
                return await self._security_scan(arguments)
            else:
                return json.dumps({"error": f"Unknown tool: {name}"})
        except Exception as e:
            logger.exception("tool_execution_failed", tool=name, error=str(e))
            return json.dumps({"error": str(e)})
    
    async def _review_code(self, args: dict) -> str:
        """Review code using AI"""
        code = args['code']
        language = args.get('language', 'auto')
        focus = args.get('focus', ['security', 'bugs', 'performance'])
        provider = args.get("provider")
        model = args.get("model")
        
        # Perform review
        review_result = await self.ai_reviewer.review(
            diff=code,
            files_changed=[f"code.{language}"],
            focus_areas=focus,
            provider=provider,
            model=model,
        )
        
        # Format result
        result = {
            "ai_provider": getattr(self.ai_reviewer, "last_provider_used", None),
            "ai_model": getattr(self.ai_reviewer, "last_model_used", None),
            "summary": review_result.summary,
            "score": review_result.score,
            "total_issues": review_result.total_issues,
            "issues": [
                {
                    "severity": issue.severity.value,
                    "title": issue.title,
                    "description": issue.description,
                    "category": issue.category,
                    "suggestion": issue.suggestion
                }
                for issue in review_result.issues
            ]
        }
        
        return json.dumps(result, indent=2)
    
    async def _analyze_diff(self, args: dict) -> str:
        """Analyze git diff"""
        diff = args['diff']
        
        # Parse diff
        diff_info = self.diff_analyzer.parse_diff(diff)
        
        # Get file stats
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
        language = args.get('language', 'auto')
        provider = args.get("provider")
        model = args.get("model")
        
        # Perform security-focused review
        review_result = await self.ai_reviewer.review(
            diff=code,
            files_changed=[f"code.{language}"],
            focus_areas=['security'],
            provider=provider,
            model=model,
        )
        
        # Filter only security issues
        security_issues = [
            issue for issue in review_result.issues
            if issue.category == 'security'
        ]
        
        result = {
            "ai_provider": getattr(self.ai_reviewer, "last_provider_used", None),
            "ai_model": getattr(self.ai_reviewer, "last_model_used", None),
            "security_score": 10 - len(security_issues),
            "vulnerabilities_found": len(security_issues),
            "critical_count": sum(1 for i in security_issues if i.severity.value == 'critical'),
            "issues": [
                {
                    "severity": issue.severity.value,
                    "title": issue.title,
                    "description": issue.description,
                    "suggestion": issue.suggestion
                }
                for issue in security_issues
            ]
        }
        
        return json.dumps(result, indent=2)

