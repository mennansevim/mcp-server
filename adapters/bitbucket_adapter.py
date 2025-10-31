"""
Bitbucket API adapter
"""
import os
import structlog
from typing import List
from atlassian.bitbucket import Cloud as BitbucketCloud

from models import UnifiedPRData
from .base_adapter import BasePlatformAdapter

logger = structlog.get_logger()


class BitbucketAdapter(BasePlatformAdapter):
    """Bitbucket API client"""
    
    def __init__(self):
        username = os.getenv("BITBUCKET_USERNAME")
        password = os.getenv("BITBUCKET_APP_PASSWORD")
        
        if not username or not password:
            raise ValueError("BITBUCKET_USERNAME and BITBUCKET_APP_PASSWORD required")
        
        self.client = BitbucketCloud(
            username=username,
            password=password,
            cloud=True
        )
        logger.info("bitbucket_adapter_initialized")
    
    async def fetch_diff(self, pr_data: UnifiedPRData) -> str:
        """Fetch PR diff from Bitbucket"""
        try:
            workspace = pr_data.metadata['workspace']
            repo_slug = pr_data.repo_full_name.split('/')[-1]
            pr_id = pr_data.pr_id
            
            # Get diff
            diff = self.client.workspaces.get(workspace).repositories.get(
                repo_slug
            ).pullrequests.get(pr_id).diff()
            
            return diff
            
        except Exception as e:
            logger.exception("bitbucket_fetch_diff_failed", error=str(e))
            return ""
    
    async def post_summary_comment(self, pr_data: UnifiedPRData, comment: str) -> bool:
        """Post comment on Bitbucket PR"""
        try:
            workspace = pr_data.metadata['workspace']
            repo_slug = pr_data.repo_full_name.split('/')[-1]
            pr_id = pr_data.pr_id
            
            self.client.workspaces.get(workspace).repositories.get(
                repo_slug
            ).pullrequests.get(pr_id).comment(comment)
            
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
            
            pr = self.client.workspaces.get(workspace).repositories.get(
                repo_slug
            ).pullrequests.get(pr_id)
            
            for comment_data in comments:
                # Bitbucket inline comments require specific structure
                pr.comment(
                    content=comment_data['body'],
                    inline={
                        'path': comment_data['file_path'],
                        'to': comment_data['line']
                    }
                )
            
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
            
            self.client.workspaces.get(workspace).repositories.get(
                repo_slug
            ).commit(sha).statuses.post(
                key='ai-code-review',
                state=bitbucket_state,
                description=description,
                name='AI Code Review'
            )
            
            logger.info("bitbucket_status_updated", state=bitbucket_state)
            return True
            
        except Exception as e:
            logger.exception("bitbucket_update_status_failed", error=str(e))
            return False

