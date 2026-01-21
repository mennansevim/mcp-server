"""
AI-powered code review using OpenAI, Anthropic, or Groq
"""
import os
import json
import structlog
from pathlib import Path
from typing import List, Optional, Dict
from anthropic import Anthropic
from openai import OpenAI
from groq import Groq

from models import ReviewResult, ReviewIssue, IssueSeverity
from services.language_detector import LanguageDetector
from services.rule_generator import RuleGenerator, RULE_CATEGORIES

logger = structlog.get_logger()

# Rules directory
RULES_DIR = Path(__file__).parent.parent / "rules"


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

**MANDATORY RULES - NO EXCEPTIONS:**
- If you see ANY missing keyword (`await`, `var`, `let`, `const`, `$`, `fn`, `func`, `def`, etc.) → **CRITICAL, block_merge=true**
- If you see ANY type mismatch (e.g., `string? = 1`, `int = "test"`, `const count: number = "test"`) → **CRITICAL, block_merge=true**
- If you see ANY invalid property/method name (typo, wrong prefix) → **CRITICAL, block_merge=true**
- If you see ANY syntax error (missing semicolon, unmatched braces, wrong indentation) → **CRITICAL, block_merge=true**
- If code won't compile/run → **ALWAYS mark as CRITICAL and block_merge=true**
- **CHECK EVERY LINE OF THE DIFF - NO DETAIL IS TOO SMALL**

**If code has compilation/syntax errors or will break the build, mark as CRITICAL and set block_merge=true.**

Provide your review in JSON format:
{{
    "summary": "DETAILED summary - MUST explicitly state if code won't compile/run. List ALL compilation errors found. If there are CRITICAL errors, start with '🚨 CRITICAL ERRORS FOUND:' and list them clearly.",
    "score": 3,
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
    
    def __init__(self, provider: str = "anthropic", model: Optional[str] = None):
        self.provider = provider.lower()
        self.model = model
        
        if self.provider == "anthropic":
            self.client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
            self.model = model or "claude-3-5-sonnet-20241022"
        elif self.provider == "openai":
            self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            self.model = model or "gpt-4-turbo-preview"
        elif self.provider == "groq":
            self.client = Groq(api_key=os.getenv("GROQ_API_KEY"))
            self.model = model or "llama-3.3-70b-versatile"
        else:
            raise ValueError(f"Unsupported AI provider: {provider}")
        
        # Rule generator'ı aynı provider ile başlat
        self.rule_generator = RuleGenerator(provider=provider, model=model)
        
        logger.info("ai_reviewer_initialized", provider=self.provider, model=self.model)
    
    def _load_rules(self, focus_areas: List[str], language: Optional[str] = None) -> str:
        """
        Load relevant rules based on focus areas and detected language
        
        Args:
            focus_areas: Areas to focus on (security, performance, etc.)
            language: Detected programming language (python, csharp, etc.)
        """
        rules_content = []
        loaded_files = set()
        
        # Eğer dil tespit edildiyse, dile özel rule dosyalarını yükle
        if language:
            for area in focus_areas:
                # Kategori adını normalize et
                category = area.lower().replace('_', '-')
                
                # Eğer kategori RULE_CATEGORIES'de yoksa, eski mapping'i kullan
                if category not in RULE_CATEGORIES:
                    # Eski mapping'den kategori adını çıkar
                    rule_file = self.RULE_FILES.get(area.lower(), '')
                    if rule_file:
                        category = rule_file.replace('.md', '')
                    else:
                        # Mapping bulunamazsa, area'yı direkt kategori olarak kullan
                        category = area.lower().replace('_', '-')
                
                # Dile özel rule dosyası: {language}-{category}.md
                rule_filename = f"{language}-{category}.md"
                rule_path = RULES_DIR / rule_filename
                
                if rule_path.exists():
                    try:
                        with open(rule_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            rules_content.append(f"\n## Rules for {language.upper()}: {area.upper()}\n{content}")
                            loaded_files.add(rule_filename)
                            logger.info("loaded_language_specific_rules", language=language, area=area, file=rule_filename)
                    except Exception as e:
                        logger.warning("failed_to_load_language_rules", language=language, area=area, error=str(e))
        
        # Dile özel rule bulunamadıysa veya dil tespit edilmediyse, genel rule'ları yükle
        if not rules_content:
            for area in focus_areas:
                rule_file = self.RULE_FILES.get(area.lower())
                if rule_file and rule_file not in loaded_files:
                    rule_path = RULES_DIR / rule_file
                    if rule_path.exists():
                        try:
                            with open(rule_path, 'r', encoding='utf-8') as f:
                                content = f.read()
                                rules_content.append(f"\n## Rules for: {area.upper()}\n{content}")
                                loaded_files.add(rule_file)
                                logger.info("loaded_rules", area=area, file=rule_file)
                        except Exception as e:
                            logger.warning("failed_to_load_rules", area=area, error=str(e))
        
        if rules_content:
            return "\n\n".join(rules_content)
        return ""
    
    async def review(
        self,
        diff: str,
        files_changed: List[str],
        focus_areas: List[str]
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
            
            logger.info("requesting_ai_review", provider=self.provider, files_count=len(files_changed), rules_loaded=bool(rules))
            
            if self.provider == "anthropic":
                response = await self._review_with_anthropic(prompt)
            elif self.provider == "groq":
                response = await self._review_with_groq(prompt)
            else:
                response = await self._review_with_openai(prompt)
            
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
                
                # Ensure critical issues have detailed descriptions
                if issue.get("severity") == "critical":
                    desc = issue.get("description", "")
                    if not desc.startswith(("CRITICAL", "🚨", "❌", "critical")):
                        issue["description"] = f"🚨 CRITICAL: {desc}"
                    title = issue.get("title", "")
                    if not title.startswith(("CRITICAL", "🚨", "❌")):
                        issue["title"] = f"CRITICAL: {title}"
                
                normalized_issues.append(issue)
            
            # Enhance summary if critical issues found
            summary = review_data.get("summary", "AI review completed")
            critical_issues = [issue for issue in normalized_issues if issue.get("severity") == "critical"]
            
            if critical_issues:
                # Prepend critical issues summary
                critical_summary = f"🚨 CRITICAL ERRORS FOUND ({len(critical_issues)}):\n"
                for idx, issue in enumerate(critical_issues, 1):
                    critical_summary += f"{idx}. {issue.get('title', 'Unknown issue')} - {issue.get('description', '')[:100]}...\n"
                summary = critical_summary + "\n" + summary
            
            # Convert to ReviewResult
            result = ReviewResult(
                summary=summary,
                score=review_data.get("score", 7),
                issues=[
                    ReviewIssue(**issue)
                    for issue in normalized_issues
                ],
                approval_recommended=review_data.get("approval_recommended", True),
                block_merge=review_data.get("block_merge", False) or len(critical_issues) > 0
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
    
    async def _review_with_anthropic(self, prompt: str) -> str:
        """Get review from Anthropic Claude"""
        message = self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            temperature=0.3,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        return message.content[0].text
    
    async def _review_with_openai(self, prompt: str) -> str:
        """Get review from OpenAI"""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are an expert code reviewer."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=4096
        )
        return response.choices[0].message.content
    
    async def _review_with_groq(self, prompt: str) -> str:
        """Get review from Groq"""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are an expert code reviewer."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=4096
        )
        return response.choices[0].message.content
    
    def _parse_ai_response(self, response: str) -> dict:
        """Parse AI response to structured data with robust error handling"""
        try:
            # Try to find JSON in the response
            start = response.find('{')
            end = response.rfind('}') + 1
            
            if start != -1 and end > start:
                json_str = response[start:end]
                
                # Clean up common JSON issues
                # Remove trailing commas before ] or }
                import re
                json_str = re.sub(r',(\s*[}\]])', r'\1', json_str)
                
                # Try parsing
                try:
                    data = json.loads(json_str)
                except json.JSONDecodeError as e:
                    # Try more aggressive cleaning
                    logger.warning("json_parse_retry", error=str(e))
                    
                    # Remove any control characters
                    json_str = ''.join(char for char in json_str if ord(char) >= 32 or char in '\n\r\t')
                    
                    # Try again
                    try:
                        data = json.loads(json_str)
                    except json.JSONDecodeError:
                        # Final fallback: extract what we can
                        logger.warning("json_parse_failed_extracting_manually")
                        return self._extract_review_manually(response)
                
                # Validate and fix the parsed data
                return self._validate_review_data(data, response)
            else:
                # No JSON found, extract manually
                return self._extract_review_manually(response)
                
        except Exception as e:
            logger.exception("parse_ai_response_failed", error=str(e))
            return self._extract_review_manually(response)
    
    def _validate_review_data(self, data: dict, original_response: str) -> dict:
        """Validate and fix review data structure"""
        # Ensure required fields exist
        if "summary" not in data or not data["summary"]:
            data["summary"] = original_response[:500] if original_response else "Review completed"
        
        if "score" not in data:
            data["score"] = 7
        else:
            # Ensure score is a valid number
            try:
                data["score"] = max(0, min(10, int(data["score"])))
            except (ValueError, TypeError):
                data["score"] = 5
        
        if "issues" not in data or not isinstance(data["issues"], list):
            data["issues"] = []
        
        # Validate each issue
        valid_issues = []
        for issue in data["issues"]:
            if isinstance(issue, dict):
                # Ensure required fields
                validated = {
                    "severity": str(issue.get("severity", "info")).lower(),
                    "title": str(issue.get("title", "Issue found")),
                    "description": str(issue.get("description", "")),
                    "category": str(issue.get("category", "general")),
                    "file_path": issue.get("file_path"),
                    "line_number": issue.get("line_number"),
                    "suggestion": issue.get("suggestion"),
                    "code_snippet": issue.get("code_snippet"),
                }
                
                # Validate severity
                valid_severities = ["critical", "high", "medium", "low", "info"]
                if validated["severity"] not in valid_severities:
                    validated["severity"] = "info"
                
                valid_issues.append(validated)
        
        data["issues"] = valid_issues
        
        if "approval_recommended" not in data:
            data["approval_recommended"] = data["score"] >= 7
        
        if "block_merge" not in data:
            data["block_merge"] = any(i["severity"] == "critical" for i in valid_issues)
        
        return data
    
    def _extract_review_manually(self, response: str) -> dict:
        """Extract review data from non-JSON response"""
        logger.info("extracting_review_manually")
        
        # Try to find score
        import re
        score = 7
        score_match = re.search(r'score["\s:]+(\d+)', response.lower())
        if score_match:
            score = max(0, min(10, int(score_match.group(1))))
        
        # Build summary from response
        summary = response[:1000] if response else "Review completed"
        
        # Check for critical keywords
        has_critical = any(word in response.lower() for word in 
                         ["critical", "error", "won't compile", "syntax error", "compilation error"])
        
        return {
            "summary": summary,
            "score": score,
            "issues": [],
            "approval_recommended": score >= 7 and not has_critical,
            "block_merge": has_critical
        }

