"""
Platform-agnostic webhook handler with automatic platform detection
"""
import structlog
from typing import Dict, Any, Optional
from fastapi import Request

from models import Platform, UnifiedPRData
from .parsers import (
    GitHubParser,
    GitLabParser,
    BitbucketParser,
    AzureParser,
)

logger = structlog.get_logger()


class WebhookHandler:
    """Handles incoming webhooks from any platform"""
    
    # Platform detection signatures
    PLATFORM_HEADERS = {
        'x-github-event': Platform.GITHUB,
        'x-gitlab-event': Platform.GITLAB,
        'x-event-key': Platform.BITBUCKET,
        'x-vss-activityid': Platform.AZURE,
    }
    
    def __init__(self):
        self.parsers = {
            Platform.GITHUB: GitHubParser(),
            Platform.GITLAB: GitLabParser(),
            Platform.BITBUCKET: BitbucketParser(),
            Platform.AZURE: AzureParser(),
        }
    
    async def handle(self, request: Request) -> Optional[UnifiedPRData]:
        """
        Process webhook request and return unified PR data
        
        Args:
            request: FastAPI request object
            
        Returns:
            UnifiedPRData or None if not a PR event
        """
        headers = dict(request.headers)
        body = await request.json()
        
        # Detect platform
        platform = self._detect_platform(headers, body)
        
        if platform == Platform.UNKNOWN:
            logger.warning("unknown_platform", headers=list(headers.keys()))
            return None
        
        logger.info("webhook_received", platform=platform.value)
        
        # Get appropriate parser
        parser = self.parsers.get(platform)
        if not parser:
            logger.error("no_parser_found", platform=platform.value)
            return None
        
        # Check if this is a PR event
        if not parser.is_pull_request_event(headers, body):
            logger.info("not_pr_event", platform=platform.value)
            return None
        
        # Parse to unified format
        try:
            pr_data = parser.parse(headers, body)
            logger.info(
                "webhook_parsed",
                platform=platform.value,
                pr_id=pr_data.pr_id,
                repo=pr_data.repo_full_name
            )
            return pr_data
        except Exception as e:
            logger.exception("parse_error", platform=platform.value, error=str(e))
            return None
    
    def _detect_platform(self, headers: Dict[str, str], body: Dict[str, Any]) -> Platform:
        """
        Detect platform from headers or payload structure
        
        Args:
            headers: Request headers
            body: Request body
            
        Returns:
            Detected platform
        """
        # Convert headers to lowercase for case-insensitive matching
        headers_lower = {k.lower(): v for k, v in headers.items()}
        
        # Check headers first (most reliable)
        for header, platform in self.PLATFORM_HEADERS.items():
            if header in headers_lower:
                return platform
        
        # Fallback: check payload structure
        if 'pull_request' in body and 'repository' in body:
            # GitHub structure
            if 'html_url' in body.get('repository', {}) and 'github.com' in str(body['repository'].get('html_url', '')):
                return Platform.GITHUB
        
        if 'object_kind' in body and body.get('object_kind') == 'merge_request':
            return Platform.GITLAB
        
        if 'pullrequest' in body and 'bitbucket' in str(body).lower():
            return Platform.BITBUCKET
        
        if 'resource' in body and 'pullRequestId' in body.get('resource', {}):
            return Platform.AZURE
        
        return Platform.UNKNOWN

