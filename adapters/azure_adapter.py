"""
Azure DevOps API adapter
"""
import os
import structlog
from typing import List
from azure.devops.connection import Connection
from msrest.authentication import BasicAuthentication

from models import UnifiedPRData
from .base_adapter import BasePlatformAdapter

logger = structlog.get_logger()


class AzureAdapter(BasePlatformAdapter):
    """Azure DevOps API client"""
    
    def __init__(self):
        pat = os.getenv("AZURE_DEVOPS_PAT")
        org_url = os.getenv("AZURE_DEVOPS_ORG")
        
        if not pat or not org_url:
            raise ValueError("AZURE_DEVOPS_PAT and AZURE_DEVOPS_ORG required")
        
        credentials = BasicAuthentication('', pat)
        self.connection = Connection(base_url=org_url, creds=credentials)
        self.git_client = self.connection.clients.get_git_client()
        
        logger.info("azure_adapter_initialized")
    
    async def fetch_diff(self, pr_data: UnifiedPRData) -> str:
        """Fetch PR diff from Azure DevOps"""
        try:
            project_id = pr_data.metadata['project_id']
            repo_id = pr_data.metadata['repository_id']
            pr_id = int(pr_data.pr_id)
            
            # Get PR iterations (commits)
            iterations = self.git_client.get_pull_request_iterations(
                repository_id=repo_id,
                pull_request_id=pr_id,
                project=project_id
            )
            
            if not iterations:
                return ""
            
            # Get changes from latest iteration
            changes = self.git_client.get_pull_request_iteration_changes(
                repository_id=repo_id,
                pull_request_id=pr_id,
                iteration_id=iterations[-1].id,
                project=project_id
            )
            
            # Build diff from changes
            diff_parts = []
            for change in changes.change_entries:
                if hasattr(change, 'item') and change.item:
                    diff_parts.append(f"--- a/{change.item.path}")
                    diff_parts.append(f"+++ b/{change.item.path}")
            
            return "\n".join(diff_parts)
            
        except Exception as e:
            logger.exception("azure_fetch_diff_failed", error=str(e))
            return ""
    
    async def post_summary_comment(self, pr_data: UnifiedPRData, comment: str) -> bool:
        """Post comment on Azure DevOps PR"""
        try:
            project_id = pr_data.metadata['project_id']
            repo_id = pr_data.metadata['repository_id']
            pr_id = int(pr_data.pr_id)
            
            thread = {
                'comments': [{'content': comment}],
                'status': 1  # Active
            }
            
            self.git_client.create_thread(
                comment_thread=thread,
                repository_id=repo_id,
                pull_request_id=pr_id,
                project=project_id
            )
            
            logger.info("azure_comment_posted", pr_id=pr_data.pr_id)
            return True
            
        except Exception as e:
            logger.exception("azure_post_comment_failed", error=str(e))
            return False
    
    async def post_inline_comments(
        self,
        pr_data: UnifiedPRData,
        comments: List[dict]
    ) -> bool:
        """Post inline comments on Azure DevOps PR"""
        try:
            project_id = pr_data.metadata['project_id']
            repo_id = pr_data.metadata['repository_id']
            pr_id = int(pr_data.pr_id)
            
            for comment_data in comments:
                thread = {
                    'comments': [{'content': comment_data['body']}],
                    'status': 1,
                    'thread_context': {
                        'file_path': comment_data['file_path'],
                        'right_file_start': {
                            'line': comment_data['line'],
                            'offset': 1
                        },
                        'right_file_end': {
                            'line': comment_data['line'],
                            'offset': 1
                        }
                    }
                }
                
                self.git_client.create_thread(
                    comment_thread=thread,
                    repository_id=repo_id,
                    pull_request_id=pr_id,
                    project=project_id
                )
            
            logger.info("azure_inline_comments_posted", count=len(comments))
            return True
            
        except Exception as e:
            logger.exception("azure_post_inline_failed", error=str(e))
            return False
    
    async def update_status(
        self,
        pr_data: UnifiedPRData,
        state: str,
        description: str
    ) -> bool:
        """Update Azure DevOps PR status"""
        try:
            # Azure DevOps uses pull request statuses differently
            # This would typically update the PR vote/status
            logger.info("azure_status_update_not_implemented")
            return True
            
        except Exception as e:
            logger.exception("azure_update_status_failed", error=str(e))
            return False

