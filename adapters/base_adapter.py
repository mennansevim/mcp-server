"""
Base adapter interface for platform integrations
"""
from abc import ABC, abstractmethod
from typing import List
from models import UnifiedPRData


class BasePlatformAdapter(ABC):
    """Abstract base class for platform adapters"""
    
    @abstractmethod
    async def fetch_diff(self, pr_data: UnifiedPRData) -> str:
        """
        Fetch the actual diff content for a PR
        
        Args:
            pr_data: Unified PR data
            
        Returns:
            Diff text in unified format
        """
        pass
    
    @abstractmethod
    async def post_summary_comment(self, pr_data: UnifiedPRData, comment: str) -> bool:
        """
        Post a summary comment on the PR
        
        Args:
            pr_data: Unified PR data
            comment: Markdown formatted comment
            
        Returns:
            True if successful
        """
        pass
    
    @abstractmethod
    async def post_inline_comments(
        self,
        pr_data: UnifiedPRData,
        comments: List[dict]
    ) -> bool:
        """
        Post inline comments on specific lines
        
        Args:
            pr_data: Unified PR data
            comments: List of {file_path, line, body}
            
        Returns:
            True if successful
        """
        pass
    
    @abstractmethod
    async def update_status(
        self,
        pr_data: UnifiedPRData,
        state: str,
        description: str
    ) -> bool:
        """
        Update PR status/check
        
        Args:
            pr_data: Unified PR data
            state: success, failure, pending
            description: Status description
            
        Returns:
            True if successful
        """
        pass

