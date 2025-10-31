"""
GitHub webhook parser
"""
from typing import Dict, Any
from models import Platform, UnifiedPRData


class GitHubParser:
    """Parse GitHub webhook payloads"""
    
    def is_pull_request_event(self, headers: Dict[str, str], body: Dict[str, Any]) -> bool:
        """Check if this is a PR event"""
        event_type = headers.get('x-github-event', '')
        return event_type == 'pull_request' and body.get('action') in ['opened', 'synchronize', 'reopened']
    
    def parse(self, headers: Dict[str, str], body: Dict[str, Any]) -> UnifiedPRData:
        """Parse GitHub webhook to unified format"""
        pr = body['pull_request']
        repo = body['repository']
        
        return UnifiedPRData(
            platform=Platform.GITHUB,
            pr_url=pr['html_url'],
            pr_id=str(pr['number']),
            repo_full_name=repo['full_name'],
            source_branch=pr['head']['ref'],
            target_branch=pr['base']['ref'],
            title=pr['title'],
            description=pr.get('body', ''),
            author=pr['user']['login'],
            diff=pr['diff_url'],  # URL to diff, will be fetched later
            files_changed=[],  # Will be populated when fetching diff
            additions=pr.get('additions', 0),
            deletions=pr.get('deletions', 0),
            metadata={
                'pr_number': pr['number'],
                'sha': pr['head']['sha'],
                'repo_id': repo['id'],
                'action': body.get('action'),
            }
        )

