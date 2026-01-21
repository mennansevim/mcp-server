"""
Bitbucket API adapter (Updated for API Tokens)
"""
import os
import structlog
import requests
from typing import List

from models import UnifiedPRData
from .base_adapter import BasePlatformAdapter

logger = structlog.get_logger()


class BitbucketAdapter(BasePlatformAdapter):
    """Bitbucket API client - supports multiple auth methods"""
    
    def __init__(self):
        # Auth method priority:
        # 1. Repository Access Token (BITBUCKET_REPO_TOKEN) - works with 2FA
        # 2. User API Token (BITBUCKET_API_TOKEN) - may have 2FA issues
        # 3. App Password (BITBUCKET_USERNAME + BITBUCKET_APP_PASSWORD) - legacy
        
        self.repo_token = os.getenv("BITBUCKET_REPO_TOKEN")
        self.api_token = os.getenv("BITBUCKET_API_TOKEN")
        self.username = os.getenv("BITBUCKET_USERNAME")
        self.app_password = os.getenv("BITBUCKET_APP_PASSWORD")
        
        # Determine auth type
        if self.repo_token:
            self.auth_type = "repo_token"
        elif self.api_token:
            self.auth_type = "api_token"
        elif self.username and self.app_password:
            self.auth_type = "basic"
        else:
            raise ValueError(
                "Bitbucket auth required: BITBUCKET_REPO_TOKEN, BITBUCKET_API_TOKEN, "
                "or (BITBUCKET_USERNAME + BITBUCKET_APP_PASSWORD)"
            )
        
        self.api_base = "https://api.bitbucket.org/2.0"
        logger.info("bitbucket_adapter_initialized", auth_type=self.auth_type)
    
    def _get_headers(self) -> dict:
        """Get authentication headers"""
        if self.auth_type == "repo_token":
            # Repository Access Token uses Bearer auth
            return {
                "Authorization": f"Bearer {self.repo_token}",
                "Accept": "application/json"
            }
        elif self.auth_type == "api_token":
            return {
                "Authorization": f"Bearer {self.api_token}",
                "Accept": "application/json"
            }
        else:
            # basic auth uses requests.auth
            return {"Accept": "application/json"}
    
    def _get_auth(self):
        """Get authentication for requests"""
        if self.auth_type == "basic":
            from requests.auth import HTTPBasicAuth
            return HTTPBasicAuth(self.username, self.app_password)
        return None  # repo_token and api_token use headers
    
    async def fetch_diff(self, pr_data: UnifiedPRData) -> str:
        """Fetch PR diff from Bitbucket"""
        try:
            workspace = pr_data.metadata['workspace']
            repo_slug = pr_data.repo_full_name.split('/')[-1]
            pr_id = pr_data.pr_id
            
            # Construct API URL
            url = f"{self.api_base}/repositories/{workspace}/{repo_slug}/pullrequests/{pr_id}/diff"
            
            # Make request
            response = requests.get(
                url,
                headers=self._get_headers(),
                auth=self._get_auth()
            )
            response.raise_for_status()
            
            return response.text
            
        except Exception as e:
            logger.exception("bitbucket_fetch_diff_failed", error=str(e))
            return ""
    
    async def post_summary_comment(self, pr_data: UnifiedPRData, comment: str) -> bool:
        """Post comment on Bitbucket PR"""
        try:
            workspace = pr_data.metadata['workspace']
            repo_slug = pr_data.repo_full_name.split('/')[-1]
            pr_id = pr_data.pr_id
            
            # Construct API URL
            url = f"{self.api_base}/repositories/{workspace}/{repo_slug}/pullrequests/{pr_id}/comments"
            
            # Make request
            response = requests.post(
                url,
                headers=self._get_headers(),
                auth=self._get_auth(),
                json={"content": {"raw": comment}}
            )
            response.raise_for_status()
            
            logger.info("bitbucket_comment_posted", pr_id=pr_data.pr_id)
            return True
            
        except Exception as e:
            logger.exception("bitbucket_post_comment_failed", error=str(e))
            return False
    
    async def post_inline_comments(
        self,
        pr_data: UnifiedPRData,
        comments: List[dict]
    ) -> bool:
        """Post inline comments on Bitbucket PR"""
        try:
            workspace = pr_data.metadata['workspace']
            repo_slug = pr_data.repo_full_name.split('/')[-1]
            pr_id = pr_data.pr_id
            
            url = f"{self.api_base}/repositories/{workspace}/{repo_slug}/pullrequests/{pr_id}/comments"
            
            for comment_data in comments:
                # Bitbucket inline comments require specific structure
                payload = {
                    "content": {"raw": comment_data['body']},
                    "inline": {
                        "path": comment_data['file_path'],
                        "to": comment_data['line']
                    }
                }
                
                response = requests.post(
                    url,
                    headers=self._get_headers(),
                    auth=self._get_auth(),
                    json=payload
                )
                response.raise_for_status()
            
            logger.info("bitbucket_inline_comments_posted", count=len(comments))
            return True
            
        except Exception as e:
            logger.exception("bitbucket_post_inline_failed", error=str(e))
            return False
    
    async def update_status(
        self,
        pr_data: UnifiedPRData,
        state: str,
        description: str
    ) -> bool:
        """Update Bitbucket commit status"""
        try:
            workspace = pr_data.metadata['workspace']
            repo_slug = pr_data.repo_full_name.split('/')[-1]
            sha = pr_data.metadata.get('sha')
            
            if not sha:
                return False
            
            # Map state names
            bitbucket_state = {
                'success': 'SUCCESSFUL',
                'failure': 'FAILED',
                'pending': 'INPROGRESS'
            }.get(state, 'INPROGRESS')
            
            url = f"{self.api_base}/repositories/{workspace}/{repo_slug}/commit/{sha}/statuses/build"
            
            payload = {
                "key": "ai-code-review",
                "state": bitbucket_state,
                "description": description,
                "name": "AI Code Review"
            }
            
            response = requests.post(
                url,
                headers=self._get_headers(),
                auth=self._get_auth(),
                json=payload
            )
            response.raise_for_status()
            
            logger.info("bitbucket_status_updated", state=bitbucket_state)
            return True
            
        except Exception as e:
            logger.exception("bitbucket_update_status_failed", error=str(e))
            return False

