"""
AI-powered code review using OpenAI, Anthropic, or Groq
"""
import os
import json
import structlog
from typing import List, Optional
from anthropic import Anthropic
from openai import OpenAI
from groq import Groq

from models import ReviewResult, ReviewIssue, IssueSeverity

logger = structlog.get_logger()


class AIReviewer:
    """AI-powered code reviewer"""
    
    REVIEW_PROMPT = """You are an expert code reviewer. Analyze the following code changes and provide detailed feedback.

Focus areas: {focus_areas}

Code diff:
{diff}

Files changed:
{files}

Provide your review in JSON format with the following structure:
{{
    "summary": "Brief overview of the changes and overall quality",
    "score": 8,
    "issues": [
        {{
            "severity": "critical|high|medium|low|info",
            "title": "Short issue title",
            "description": "Detailed description",
            "file_path": "path/to/file.py",
            "line_number": 42,
            "code_snippet": "problematic code",
            "suggestion": "how to fix",
            "category": "security|performance|bug|style|best_practices"
        }}
    ],
    "approval_recommended": true,
    "block_merge": false
}}

Be specific, constructive, and focus on:
- Security vulnerabilities
- Performance issues
- Bugs and logic errors
- Code quality and best practices
- Potential edge cases
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
            prompt = self.REVIEW_PROMPT.format(
                focus_areas=", ".join(focus_areas),
                diff=diff[:10000],  # Limit diff size
                files="\n".join(files_changed)
            )
            
            logger.info("requesting_ai_review", provider=self.provider, files_count=len(files_changed))
            
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

