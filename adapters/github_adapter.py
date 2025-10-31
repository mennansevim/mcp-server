"""
GitHub API adapter
"""
import os
import structlog
from typing import List
from github import Github, GithubException

from models import UnifiedPRData
from .base_adapter import BasePlatformAdapter

logger = structlog.get_logger()


class GitHubAdapter(BasePlatformAdapter):
    """GitHub API client"""
    
    def __init__(self):
        token = os.getenv("GITHUB_TOKEN")
        if not token:
            raise ValueError("GITHUB_TOKEN environment variable required")
        
        self.client = Github(token)
        logger.info("github_adapter_initialized")
    
    async def fetch_diff(self, pr_data: UnifiedPRData) -> str:
        """Fetch PR diff from GitHub"""
        try:
            repo = self.client.get_repo(pr_data.repo_full_name)
            pr = repo.get_pull(int(pr_data.pr_id))
            
            # Get diff
            files = pr.get_files()
            diff_parts = []
            
            for file in files:
                if file.patch:
                    diff_parts.append(f"--- a/{file.filename}")
                    diff_parts.append(f"+++ b/{file.filename}")
                    diff_parts.append(file.patch)
            
            return "\n".join(diff_parts)
            
        except GithubException as e:
            logger.exception("github_fetch_diff_failed", error=str(e))
            return ""
    
    async def post_summary_comment(self, pr_data: UnifiedPRData, comment: str) -> bool:
        """Post summary comment on GitHub PR"""
        try:
            repo = self.client.get_repo(pr_data.repo_full_name)
            pr = repo.get_pull(int(pr_data.pr_id))
            pr.create_issue_comment(comment)
            
            logger.info("github_comment_posted", pr_id=pr_data.pr_id)
            return True
            
        except GithubException as e:
            logger.exception("github_post_comment_failed", error=str(e))
            return False
    
    async def post_inline_comments(
        self,
        pr_data: UnifiedPRData,
        comments: List[dict]
    ) -> bool:
        """Post inline comments on GitHub PR"""
        try:
            repo = self.client.get_repo(pr_data.repo_full_name)
            pr = repo.get_pull(int(pr_data.pr_id))
            commit = pr.get_commits().reversed[0]  # Latest commit
            
            for comment_data in comments:
                pr.create_review_comment(
                    body=comment_data['body'],
                    commit=commit,
                    path=comment_data['file_path'],
                    line=comment_data['line']
                )
            
            logger.info("github_inline_comments_posted", count=len(comments))
            return True
            
        except GithubException as e:
            logger.exception("github_post_inline_failed", error=str(e))
            return False
    
    async def update_status(
        self,
        pr_data: UnifiedPRData,
        state: str,
        description: str
    ) -> bool:
        """Update GitHub commit status"""
        try:
            repo = self.client.get_repo(pr_data.repo_full_name)
            sha = pr_data.metadata.get('sha')
            
            if not sha:
                return False
            
            commit = repo.get_commit(sha)
            commit.create_status(
                state=state,
                description=description,
                context="AI Code Review"
            )
            
            logger.info("github_status_updated", state=state)
            return True
            
        except GithubException as e:
            logger.exception("github_update_status_failed", error=str(e))
            return False

