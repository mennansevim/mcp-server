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

**CRITICAL CHECKS (Must verify):**
1. **COMPILATION/SYNTAX ERRORS**: Will this code compile/run? Check for:
   - Missing/removed keywords (static, const, var, let, etc.)
   - Syntax errors and typos
   - Type mismatches
   - Missing imports/dependencies
   - Breaking changes (removed methods, changed signatures)

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

**If code has compilation/syntax errors or will break the build, mark as CRITICAL and set block_merge=true.**

Provide your review in JSON format:
{{
    "summary": "Brief overview - ALWAYS mention if code won't compile/run",
    "score": 3,
    "issues": [
        {{
            "severity": "critical|high|medium|low|info",
            "title": "Short issue title",
            "description": "Detailed description with impact",
            "file_path": "path/to/file.py",
            "line_number": 42,
            "code_snippet": "problematic code",
            "suggestion": "how to fix with example",
            "category": "compilation|security|performance|bug|style|best_practices"
        }}
    ],
    "approval_recommended": false,
    "block_merge": true
}}

Be specific, constructive, and CRITICAL. Better to flag false positives than miss real issues.
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
        
        logger.info("ai_reviewer_initialized", provider=self.provider, model=self.model)
    
    def _load_rules(self, focus_areas: List[str]) -> str:
        """Load relevant rules based on focus areas"""
        rules_content = []
        loaded_files = set()
        
        for area in focus_areas:
            rule_file = self.RULE_FILES.get(area.lower())
            if rule_file and rule_file not in loaded_files:
                rule_path = RULES_DIR / rule_file
                if rule_path.exists():
                    try:
                        with open(rule_path, 'r') as f:
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
            # Load relevant rules
            rules = self._load_rules(focus_areas)
            
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
            
            # Convert to ReviewResult
            result = ReviewResult(
                summary=review_data.get("summary", "AI review completed"),
                score=review_data.get("score", 7),
                issues=[
                    ReviewIssue(**issue)
                    for issue in review_data.get("issues", [])
                ],
                approval_recommended=review_data.get("approval_recommended", True),
                block_merge=review_data.get("block_merge", False)
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
            # Return a safe default result
            return ReviewResult(
                summary=f"Review failed: {str(e)}",
                score=5,
                issues=[],
                approval_recommended=False
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

