"""
Bitbucket webhook parser
"""
from typing import Dict, Any
from models import Platform, UnifiedPRData


class BitbucketParser:
    """Parse Bitbucket webhook payloads"""
    
    def is_pull_request_event(self, headers: Dict[str, str], body: Dict[str, Any]) -> bool:
        """Check if this is a PR event"""
        # Case-insensitive header lookup (FastAPI headers may vary in casing)
        headers_lower = {k.lower(): v for k, v in headers.items()}
        event_key = headers_lower.get('x-event-key', '')
        return event_key in [
            'pullrequest:created',
            'pullrequest:updated',
            'pullrequest:changes_request_created'
        ]
    
    def parse(self, headers: Dict[str, str], body: Dict[str, Any]) -> UnifiedPRData:
        """Parse Bitbucket webhook to unified format"""
        pr = body['pullrequest']
        repo = body['repository']

        author_obj = pr.get('author') or {}
        author = (
            author_obj.get('username')
            or author_obj.get('display_name')
            or author_obj.get('nickname')
            or author_obj.get('uuid')
            or 'unknown'
        )
        
        return UnifiedPRData(
            platform=Platform.BITBUCKET,
            pr_url=pr['links']['html']['href'],
            pr_id=str(pr['id']),
            repo_full_name=repo['full_name'],
            source_branch=pr['source']['branch']['name'],
            target_branch=pr['destination']['branch']['name'],
            title=pr['title'],
            description=pr.get('description', ''),
            author=author,
            diff='',  # Will be fetched using API
            files_changed=[],
            additions=0,  # Bitbucket doesn't provide this directly
            deletions=0,
            metadata={
                'pr_id': pr['id'],
                'repo_uuid': repo['uuid'],
                'workspace': repo['workspace']['slug'],
                'event_key': headers.get('x-event-key'),
            }
        )

