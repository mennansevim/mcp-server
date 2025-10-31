"""
Unified data models for cross-platform code review
"""
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, HttpUrl


class Platform(str, Enum):
    """Supported platforms"""
    GITHUB = "github"
    GITLAB = "gitlab"
    BITBUCKET = "bitbucket"
    AZURE = "azure"
    UNKNOWN = "unknown"


class IssueSeverity(str, Enum):
    """Issue severity levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class UnifiedPRData(BaseModel):
    """Unified pull request data across platforms"""
    platform: Platform
    pr_url: str
    pr_id: str
    repo_full_name: str
    source_branch: str
    target_branch: str
    title: str
    description: Optional[str] = None
    author: str
    diff: str
    files_changed: List[str] = Field(default_factory=list)
    additions: int = 0
    deletions: int = 0
    
    # Platform-specific metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ReviewIssue(BaseModel):
    """Single review issue/finding"""
    severity: IssueSeverity
    title: str
    description: str
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    line_end: Optional[int] = None
    code_snippet: Optional[str] = None
    suggestion: Optional[str] = None
    category: str = "general"  # security, performance, bug, style, etc.


class ReviewResult(BaseModel):
    """Complete review result"""
    summary: str
    score: int = Field(ge=0, le=10, description="Code quality score 0-10")
    issues: List[ReviewIssue] = Field(default_factory=list)
    
    # Statistics
    total_issues: int = 0
    critical_count: int = 0
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0
    info_count: int = 0
    
    # Recommendations
    approval_recommended: bool = True
    block_merge: bool = False
    
    def __init__(self, **data):
        super().__init__(**data)
        # Auto-calculate statistics
        self.total_issues = len(self.issues)
        self.critical_count = sum(1 for i in self.issues if i.severity == IssueSeverity.CRITICAL)
        self.high_count = sum(1 for i in self.issues if i.severity == IssueSeverity.HIGH)
        self.medium_count = sum(1 for i in self.issues if i.severity == IssueSeverity.MEDIUM)
        self.low_count = sum(1 for i in self.issues if i.severity == IssueSeverity.LOW)
        self.info_count = sum(1 for i in self.issues if i.severity == IssueSeverity.INFO)


class ReviewRequest(BaseModel):
    """Request to review code"""
    pr_data: UnifiedPRData
    focus_areas: List[str] = Field(
        default_factory=lambda: ["security", "bugs", "performance", "best_practices"]
    )


class WebhookPayload(BaseModel):
    """Generic webhook payload"""
    headers: Dict[str, str]
    body: Dict[str, Any]
    raw_body: Optional[str] = None

