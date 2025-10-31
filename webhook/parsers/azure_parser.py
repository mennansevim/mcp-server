"""
Azure DevOps webhook parser
"""
from typing import Dict, Any
from models import Platform, UnifiedPRData


class AzureParser:
    """Parse Azure DevOps webhook payloads"""
    
    def is_pull_request_event(self, headers: Dict[str, str], body: Dict[str, Any]) -> bool:
        """Check if this is a PR event"""
        return (
            body.get('eventType') == 'git.pullrequest.created' or
            body.get('eventType') == 'git.pullrequest.updated'
        )
    
    def parse(self, headers: Dict[str, str], body: Dict[str, Any]) -> UnifiedPRData:
        """Parse Azure DevOps webhook to unified format"""
        resource = body['resource']
        repo = resource['repository']
        
        return UnifiedPRData(
            platform=Platform.AZURE,
            pr_url=resource.get('url', ''),
            pr_id=str(resource['pullRequestId']),
            repo_full_name=f"{repo['project']['name']}/{repo['name']}",
            source_branch=resource['sourceRefName'].replace('refs/heads/', ''),
            target_branch=resource['targetRefName'].replace('refs/heads/', ''),
            title=resource['title'],
            description=resource.get('description', ''),
            author=resource['createdBy']['uniqueName'],
            diff='',  # Will be fetched using API
            files_changed=[],
            additions=0,
            deletions=0,
            metadata={
                'pull_request_id': resource['pullRequestId'],
                'repository_id': repo['id'],
                'project_id': repo['project']['id'],
                'event_type': body.get('eventType'),
            }
        )

