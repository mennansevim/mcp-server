"""
GitLab webhook parser
"""
from typing import Dict, Any
from models import Platform, UnifiedPRData


class GitLabParser:
    """Parse GitLab webhook payloads"""
    
    def is_pull_request_event(self, headers: Dict[str, str], body: Dict[str, Any]) -> bool:
        """Check if this is a merge request event"""
        return (
            body.get('object_kind') == 'merge_request' and
            body.get('object_attributes', {}).get('action') in ['open', 'update', 'reopen']
        )
    
    def parse(self, headers: Dict[str, str], body: Dict[str, Any]) -> UnifiedPRData:
        """Parse GitLab webhook to unified format"""
        mr = body['object_attributes']
        project = body['project']
        
        return UnifiedPRData(
            platform=Platform.GITLAB,
            pr_url=mr['url'],
            pr_id=str(mr['iid']),
            repo_full_name=project['path_with_namespace'],
            source_branch=mr['source_branch'],
            target_branch=mr['target_branch'],
            title=mr['title'],
            description=mr.get('description', ''),
            author=mr['author']['username'],
            diff='',  # Will be fetched using API
            files_changed=[],
            additions=0,  # GitLab doesn't provide this directly
            deletions=0,
            metadata={
                'merge_request_id': mr['id'],
                'iid': mr['iid'],
                'project_id': project['id'],
                'action': mr.get('action'),
                'sha': mr['last_commit']['id'] if mr.get('last_commit') else None,
            }
        )

