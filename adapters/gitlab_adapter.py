"""
GitLab API adapter
"""
import os
import structlog
from typing import List
import gitlab
from gitlab.exceptions import GitlabError

from models import UnifiedPRData
from .base_adapter import BasePlatformAdapter

logger = structlog.get_logger()


class GitLabAdapter(BasePlatformAdapter):
    """GitLab API client"""
    
    def __init__(self):
        token = os.getenv("GITLAB_TOKEN")
        url = os.getenv("GITLAB_URL", "https://gitlab.com")
        
        if not token:
            raise ValueError("GITLAB_TOKEN environment variable required")
        
        self.client = gitlab.Gitlab(url, private_token=token)
        logger.info("gitlab_adapter_initialized")
    
    async def fetch_diff(self, pr_data: UnifiedPRData) -> str:
        """Fetch MR diff from GitLab"""
        try:
            project = self.client.projects.get(pr_data.metadata['project_id'])
            mr = project.mergerequests.get(int(pr_data.pr_id))
            
            # Get diff
            diffs = mr.diffs.list()
            diff_parts = []
            
            for diff in diffs:
                diff_parts.append(diff.diff)
            
            return "\n".join(diff_parts)
            
        except GitlabError as e:
            logger.exception("gitlab_fetch_diff_failed", error=str(e))
            return ""
    
    async def post_summary_comment(self, pr_data: UnifiedPRData, comment: str) -> bool:
        """Post note on GitLab MR"""
        try:
            project = self.client.projects.get(pr_data.metadata['project_id'])
            mr = project.mergerequests.get(int(pr_data.pr_id))
            mr.notes.create({'body': comment})
            
            logger.info("gitlab_comment_posted", mr_id=pr_data.pr_id)
            return True
            
        except GitlabError as e:
            logger.exception("gitlab_post_comment_failed", error=str(e))
            return False
    
    async def post_inline_comments(
        self,
        pr_data: UnifiedPRData,
        comments: List[dict]
    ) -> bool:
        """Post inline discussions on GitLab MR"""
        try:
            project = self.client.projects.get(pr_data.metadata['project_id'])
            mr = project.mergerequests.get(int(pr_data.pr_id))
            
            for comment_data in comments:
                # GitLab uses discussions for inline comments
                mr.discussions.create({
                    'body': comment_data['body'],
                    'position': {
                        'position_type': 'text',
                        'new_path': comment_data['file_path'],
                        'new_line': comment_data['line'],
                        'base_sha': mr.diff_refs['base_sha'],
                        'start_sha': mr.diff_refs['start_sha'],
                        'head_sha': mr.diff_refs['head_sha']
                    }
                })
            
            logger.info("gitlab_inline_comments_posted", count=len(comments))
            return True
            
        except GitlabError as e:
            logger.exception("gitlab_post_inline_failed", error=str(e))
            return False
    
    async def update_status(
        self,
        pr_data: UnifiedPRData,
        state: str,
        description: str
    ) -> bool:
        """Update GitLab commit status"""
        try:
            project = self.client.projects.get(pr_data.metadata['project_id'])
            sha = pr_data.metadata.get('sha')
            
            if not sha:
                return False
            
            # Map state names
            gitlab_state = {
                'success': 'success',
                'failure': 'failed',
                'pending': 'pending'
            }.get(state, 'pending')
            
            project.commits.get(sha).statuses.create({
                'state': gitlab_state,
                'description': description,
                'name': 'AI Code Review'
            })
            
            logger.info("gitlab_status_updated", state=gitlab_state)
            return True
            
        except GitlabError as e:
            logger.exception("gitlab_update_status_failed", error=str(e))
            return False

