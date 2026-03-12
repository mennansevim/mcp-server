"""
AI-powered code review (provider-agnostic).

Supports Groq/OpenAI/Anthropic and is designed to be extended with new providers
via services/ai_providers/*.
"""
import json
import structlog
from typing import List, Optional, Dict

from models import ReviewResult, ReviewIssue, IssueSeverity
from services.language_detector import LanguageDetector
from services.rule_generator import RuleGenerator, RULE_CATEGORIES
from services.rules_service import RulesHelper
from services.ai_providers import AIProviderRouter, AIProviderError

logger = structlog.get_logger()


class AIReviewer:
    """AI-powered code reviewer"""
    
    # Mapping of focus areas to rule files
    RULE_FILES = {
        "compilation": "compilation.md",
        "security": "security.md",
        "performance": "performance.md",
        "dotnet": "dotnet-fundamentals.md",
        "dotnet_fundamentals": "dotnet-fundamentals.md",
        "best_practices": "best-practices.md",
        "code_quality": "best-practices.md",
        "bugs": "compilation.md",  # Bugs often cause compilation issues
    }
    
    REVIEW_PROMPT = """You are an expert code reviewer with deep knowledge of multiple programming languages. Analyze the following code changes and provide detailed, critical feedback.

Focus areas: {focus_areas}

Code diff:
{diff}

Files changed:
{files}

**CRITICAL CHECKS (Must verify - CHECK EVERY LINE CAREFULLY - NO EXCEPTIONS):**

1. **COMPILATION/SYNTAX ERRORS** - HIGHEST PRIORITY: Will this code compile/run?
   
   **MISSING KEYWORDS** - Check EVERY language:
   - ❌ **C#**: `await`, `async`, `static`, `var`, `public`, `private`, `protected`
   - ❌ **JavaScript/TypeScript**: `await`, `async`, `let`, `const`, `var`, `function`
   - ❌ **Python**: `await`, `async`, `def`, `return`
   - ❌ **Java**: `public`, `private`, `protected`, `static`, `return`, `throws`
   - ❌ **Go**: `var`, `:=`, `func`, `return`
   - ❌ **Rust**: `let`, `let mut`, `fn`, `return`
   - ❌ **PHP**: `$`, `function`, `return`
   - ❌ **Ruby**: `def`, `end`, `return`
   
   **TYPE MISMATCHES** - Check EVERY assignment:
   - ❌ Cannot assign incompatible types (e.g., `string? line = 1;` - int to string)
   - ❌ Type mismatches in function parameters
   - ❌ Type mismatches in return values
   - ❌ **C#**: `string? = 1`, `int = "test"` → COMPILATION ERROR
   - ❌ **TypeScript**: `const count: number = "test"` → COMPILATION ERROR
   - ❌ **Python**: `count: int = "test"` → RUNTIME ERROR
   - ❌ **Java**: `String str = 1` → COMPILATION ERROR
   - ❌ **Go**: `var count int = "test"` → COMPILATION ERROR
   - ❌ **Rust**: `let count: i32 = "test"` → COMPILATION ERROR
   
   **INVALID PROPERTY/METHOD NAMES**:
   - ❌ Typos in property names (e.g., `PropertyNameCaseInsensitive` → `_PropertyNameCaseInsensitive`)
   - ❌ Typos in method names
   - ❌ Invalid attribute access (Python: `obj.methd()` → AttributeError)
   - ❌ Invalid property access (JavaScript: `obj.proprty` → undefined)
   - ❌ Underscore prefix added incorrectly (only valid for private fields)
   
   **SYNTAX ERRORS**:
   - ❌ Missing semicolons (C#, Java, JavaScript)
   - ❌ Unmatched braces, brackets, parentheses
   - ❌ Incorrect indentation (Python - causes SyntaxError)
   - ❌ Missing `end` keyword (Ruby)
   - ❌ Missing closing braces
   
   **MISSING IMPORTS**:
   - ❌ Required using/import statements removed
   - ❌ Typos in import paths or module names
   
   **BREAKING CHANGES**:
   - ❌ Removed methods, changed signatures
   - ❌ Changed return types

2. **LOGIC ERRORS**: 
   - Will the code behave as intended?
   - Are there edge cases not handled?
   - Could this cause runtime errors?

3. **SECURITY VULNERABILITIES**:
   - SQL injection, XSS, CSRF risks
   - Exposed secrets or credentials
   - Unsafe deserialization

4. **CODE QUALITY**:
   - Best practices violated
   - Performance issues
   - Maintainability concerns

5. **AI SLOP DETECTION** — Identify low-quality AI-generated code patterns:
   - 🤖 **Obvious/redundant comments**: Comments that just restate the code (e.g., `// Initialize the variable`, `// Return the result`, `// Import the module`, `// Loop through items`)
   - 🤖 **Generic placeholder names**: Variables like `data`, `result`, `temp`, `item`, `value`, `obj`, `thing` used without meaningful context
   - 🤖 **Boilerplate bloat**: Overly verbose code that could be expressed more concisely (e.g., unnecessary null checks already handled by the framework, manually implementing what a one-liner library call does)
   - 🤖 **Copy-paste patterns**: Repetitive blocks with minimal variation that should be refactored into a loop or helper function
   - 🤖 **Catch-all exception handling**: Generic `catch (Exception e)` / `except Exception` without specific handling or meaningful recovery
   - 🤖 **Hallucinated APIs**: Using methods, properties, or classes that don't exist in the framework/library version
   - 🤖 **TODO/FIXME placeholders left by AI**: Comments like `// TODO: implement this`, `// Add error handling here` left as unfinished scaffolding
   - 🤖 **Inconsistent patterns**: Mixing different coding styles in the same file (e.g., callbacks and async/await, var and explicit types)
   
   For each AI slop issue, use category: "ai_slop" and severity: "medium" or "low".
   **AI Slop issues must NEVER be "critical" or "high" — they are informational quality warnings, NOT merge blockers.**

**MANDATORY RULES - NO EXCEPTIONS:**
- If you see ANY missing keyword (`await`, `var`, `let`, `const`, `$`, `fn`, `func`, `def`, etc.) → **CRITICAL, block_merge=true**
- If you see ANY type mismatch (e.g., `string? = 1`, `int = "test"`, `const count: number = "test"`) → **CRITICAL, block_merge=true**
- If you see ANY invalid property/method name (typo, wrong prefix) → **CRITICAL, block_merge=true**
- If you see ANY syntax error (missing semicolon, unmatched braces, wrong indentation) → **CRITICAL, block_merge=true**
- If code won't compile/run → **ALWAYS mark as CRITICAL and block_merge=true**
- **CHECK EVERY LINE OF THE DIFF - NO DETAIL IS TOO SMALL**

**⚠️ SHORT-CIRCUIT RULE:**
If you find ANY compilation or syntax error (code won't compile/run), STOP immediately.
Do NOT check security, performance, code quality, or any other category.
Only report the compilation/syntax errors and nothing else.
Rationale: if code cannot compile, all other checks are meaningless.

**If code has compilation/syntax errors or will break the build, mark as CRITICAL and set block_merge=true.**

Provide your review in JSON format:
{{
    "summary": "DETAILED summary - MUST explicitly state if code won't compile/run. List ALL compilation errors found. If there are CRITICAL errors, start with '🚨 CRITICAL ERRORS FOUND:' and list them clearly.",
    "score": 3,
    "ai_slop_detected": true,
    "issues": [
        {{
            "severity": "critical",
            "title": "CRITICAL: Missing await keyword",
            "description": "DETAILED explanation: The code calls an async method without 'await' keyword. This will cause compilation error in C# because async methods return Task and must be awaited. Line X shows: 'writer.WriteLineAsync(...)' but should be 'await writer.WriteLineAsync(...)'. IMPACT: Code will NOT compile.",
            "file_path": "path/to/file.cs",
            "line_number": 42,
            "code_snippet": "writer.WriteLineAsync(JsonSerializer.Serialize(error));",
            "suggestion": "Add 'await' keyword: await writer.WriteLineAsync(JsonSerializer.Serialize(error));",
            "category": "compilation"
        }},
        {{
            "severity": "medium",
            "title": "AI Slop: Redundant comments restating the code",
            "description": "Multiple comments simply restate what the code does (e.g., '// Initialize the list') instead of explaining why. This is a hallmark of AI-generated code that wasn't reviewed.",
            "file_path": "path/to/file.cs",
            "line_number": 15,
            "code_snippet": "// Initialize the list\nvar list = new List<string>();",
            "suggestion": "Remove obvious comments or replace them with comments explaining the business logic and intent.",
            "category": "ai_slop"
        }}
    ],
    "approval_recommended": false,
    "block_merge": true
}}

**CRITICAL:** 
- Severity MUST be lowercase: "critical", "high", "medium", "low", "info" (NOT "CRITICAL", "HIGH", etc.)
- For compilation errors, ALWAYS use severity: "critical"
- Title MUST start with "CRITICAL:" for critical issues
- Description MUST explain WHY it won't compile and WHAT the impact is
- If multiple critical errors exist, list ALL of them clearly

Be EXTREMELY CRITICAL and THOROUGH. Check every line of the diff. Better to flag false positives than miss real compilation errors. If you see ANY syntax error, type mismatch, or missing keyword → mark as CRITICAL.
"""
    
    def __init__(
        self,
        provider: str = "anthropic",
        model: Optional[str] = None,
        *,
        ai_config: Optional[dict] = None,
    ):
        """
        Backward compatible:
          AIReviewer(provider="groq", model="...") still works.

        Recommended:
          AIReviewer(ai_config=config["ai"])
        """
        if ai_config is None:
            ai_config = {
                "provider": provider,
                "model": model,
                "temperature": 0.3,
                "max_tokens": 4096,
            }

        self.ai_config = ai_config
        self.router = AIProviderRouter(ai_config)
        self.last_provider_used: Optional[str] = None
        self.last_model_used: Optional[str] = None

        self.rules_helper = RulesHelper()
        self.rule_generator = RuleGenerator(ai_config=ai_config, rules_helper=self.rules_helper)

        logger.info(
            "ai_reviewer_initialized",
            primary_provider=self.router.primary,
        )
    
    def _load_rules(self, focus_areas: List[str], language: Optional[str] = None) -> str:
        """Load relevant rules from local rule files."""
        result = self.rules_helper.resolve_rules(focus_areas, language=language)
        content = result.get("content", "")
        files = result.get("files", [])

        if files:
            logger.info("rules_loaded", files=files, language=language)
        else:
            logger.info("no_rules_resolved", focus_areas=focus_areas, language=language)

        return content
    
    async def review(
        self,
        diff: str,
        files_changed: List[str],
        focus_areas: List[str],
        *,
        provider: Optional[str] = None,
        model: Optional[str] = None,
    ) -> ReviewResult:
        """
        Review code changes using AI
        
        Args:
            diff: Git diff text
            files_changed: List of changed file paths
            focus_areas: Areas to focus on (security, performance, etc.)
            
        Returns:
            ReviewResult with findings
        """
        try:
            # Dil tespiti yap
            detected_language = LanguageDetector.detect_from_files(files_changed)
            
            if detected_language:
                logger.info("language_detected_for_review", language=detected_language, files_count=len(files_changed))
                
                # Dile özel rule dosyalarını oluştur (yoksa)
                # Sadece focus_areas'daki kategoriler için oluştur
                categories_to_generate = []
                for area in focus_areas:
                    category = area.lower().replace('_', '-')
                    if category in RULE_CATEGORIES:
                        categories_to_generate.append(category)
                
                if categories_to_generate:
                    await self.rule_generator.generate_all_rules_for_language(
                        language=detected_language,
                        categories=categories_to_generate,
                        force_regenerate=False  # Mevcut dosyaları yeniden oluşturma
                    )
            
            # Load relevant rules (dil tespit edildiyse dile özel)
            rules = self._load_rules(focus_areas, language=detected_language)
            
            # Build enhanced prompt with rules
            prompt_parts = [
                self.REVIEW_PROMPT.format(
                    focus_areas=", ".join(focus_areas),
                    diff=diff[:10000],  # Limit diff size
                    files="\n".join(files_changed)
                )
            ]
            
            if rules:
                prompt_parts.append("\n---\n## SPECIFIC RULES TO FOLLOW:\n")
                prompt_parts.append(rules[:15000])  # Limit rules size
                prompt_parts.append("\n---\nApply these rules strictly when reviewing the code above.")
            
            prompt = "\n".join(prompt_parts)
            
            logger.info(
                "requesting_ai_review",
                primary_provider=self.router.primary,
                files_count=len(files_changed),
                rules_loaded=bool(rules),
            )

            system_msg = "You are an expert code reviewer."
            provider_used, model_used, response = self.router.chat(
                system=system_msg,
                user=prompt,
                provider_override=provider,
                model_override=model,
            )
            self.last_provider_used = provider_used
            self.last_model_used = model_used
            
            # Parse AI response
            review_data = self._parse_ai_response(response)
            
            # Normalize severity values (convert uppercase to lowercase)
            normalized_issues = []
            for issue in review_data.get("issues", []):
                if "severity" in issue:
                    severity = issue["severity"]
                    # Convert uppercase to lowercase
                    if isinstance(severity, str):
                        severity_lower = severity.lower()
                        # Map common variations
                        severity_map = {
                            "critical": "critical",
                            "high": "high",
                            "medium": "medium",
                            "low": "low",
                            "info": "info",
                            "information": "info",
                            "minor": "low",
                            "major": "high",
                        }
                        issue["severity"] = severity_map.get(severity_lower, severity_lower)
                
                # AI Slop issues must never block merge — cap at medium
                if issue.get("category") == "ai_slop" and issue.get("severity") in ("critical", "high"):
                    issue["severity"] = "medium"

                # Ensure critical issues have detailed descriptions
                if issue.get("severity") == "critical":
                    desc = issue.get("description", "")
                    if not desc.startswith(("CRITICAL", "🚨", "❌", "critical")):
                        issue["description"] = f"🚨 CRITICAL: {desc}"
                    title = issue.get("title", "")
                    if not title.startswith(("CRITICAL", "🚨", "❌")):
                        issue["title"] = f"CRITICAL: {title}"
                
                normalized_issues.append(issue)
            
            # Short-circuit: if compilation/syntax errors exist, drop everything else
            compilation_issues = [
                i for i in normalized_issues
                if i.get("severity") == "critical"
                and i.get("category", "").lower() in ("compilation", "syntax")
            ]
            if compilation_issues:
                normalized_issues = compilation_issues
                logger.info("short_circuit_compilation", kept=len(compilation_issues))

            summary = review_data.get("summary", "AI review completed")
            critical_issues = [i for i in normalized_issues if i.get("severity") == "critical"]

            if critical_issues:
                critical_summary = f"🚨 CRITICAL ERRORS FOUND ({len(critical_issues)}):\n"
                for idx, issue in enumerate(critical_issues, 1):
                    critical_summary += f"{idx}. {issue.get('title', 'Unknown issue')} - {issue.get('description', '')[:100]}...\n"
                summary = critical_summary + "\n" + summary

            ai_slop_from_response = review_data.get("ai_slop_detected", False)
            ai_slop_issues = [i for i in normalized_issues if i.get("category") == "ai_slop"]

            result = ReviewResult(
                summary=summary,
                score=review_data.get("score", 7),
                issues=[
                    ReviewIssue(**issue)
                    for issue in normalized_issues
                ],
                approval_recommended=review_data.get("approval_recommended", True),
                block_merge=review_data.get("block_merge", False) or len(critical_issues) > 0,
                ai_slop_detected=ai_slop_from_response or len(ai_slop_issues) > 0,
            )
            
            logger.info(
                "review_completed",
                total_issues=result.total_issues,
                critical=result.critical_count,
                score=result.score
            )
            
            return result
            
        except Exception as e:
            logger.exception("review_failed", error=str(e))
            # Return a safe default result with detailed error message
            error_msg = str(e)
            if "severity" in error_msg.lower() or "validation" in error_msg.lower():
                error_msg = f"🚨 CRITICAL: Review validation error - {error_msg}. Please check that severity values are lowercase ('critical', 'high', 'medium', 'low', 'info') and all required fields are present."
            
            return ReviewResult(
                summary=f"🚨 Review failed: {error_msg}",
                score=0,
                issues=[],
                approval_recommended=False,
                block_merge=True
            )

    def _build_chat_request(self, system: str, user: str, model: str):
        # local import to avoid circulars at module import time
        from services.ai_providers.base import ChatRequest

        return ChatRequest(
            system=system,
            user=user,
            model=model,
            temperature=self.router.temperature,
            max_tokens=self.router.max_tokens,
        )
    
    def _parse_ai_response(self, response: str) -> dict:
        """Parse AI response to structured data"""
        try:
            # Try to find JSON in the response
            start = response.find('{')
            end = response.rfind('}') + 1
            
            if start != -1 and end > start:
                json_str = response[start:end]
                return json.loads(json_str)
            else:
                # Fallback: return basic structure
                return {
                    "summary": response[:500],
                    "score": 7,
                    "issues": [],
                    "approval_recommended": True
                }
        except json.JSONDecodeError:
            logger.warning("failed_to_parse_ai_response")
            return {
                "summary": "Failed to parse AI response",
                "score": 5,
                "issues": [],
                "approval_recommended": False
            }

