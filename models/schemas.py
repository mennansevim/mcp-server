"""
Unified data models for cross-platform code review
"""
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


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


class SecurityThreat(str, Enum):
    """OWASP-aligned security threat classifications"""
    INJECTION = "injection"
    BROKEN_AUTH = "broken_auth"
    SENSITIVE_DATA = "sensitive_data"
    XXE = "xxe"
    BROKEN_ACCESS = "broken_access"
    MISCONFIG = "misconfig"
    XSS = "xss"
    DESERIALIZATION = "deserialization"
    VULNERABLE_DEPS = "vulnerable_deps"
    INSUFFICIENT_LOGGING = "insufficient_logging"
    SECRET_LEAK = "secret_leak"
    NONE = "none"


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
    category: str = "general"
    owasp_id: Optional[str] = None
    cwe_id: Optional[str] = None
    threat_type: Optional[str] = None


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

    # AI Slop detection
    ai_slop_detected: bool = False
    ai_slop_count: int = 0

    # Security Deep Scan
    security_score: int = Field(default=10, ge=0, le=10, description="Security score 0-10")
    security_issues_count: int = 0
    secret_leak_detected: bool = False
    owasp_categories_hit: List[str] = Field(default_factory=list)
    
    def __init__(self, **data):
        super().__init__(**data)
        self.total_issues = len(self.issues)
        self.critical_count = sum(1 for i in self.issues if i.severity == IssueSeverity.CRITICAL)
        self.high_count = sum(1 for i in self.issues if i.severity == IssueSeverity.HIGH)
        self.medium_count = sum(1 for i in self.issues if i.severity == IssueSeverity.MEDIUM)
        self.low_count = sum(1 for i in self.issues if i.severity == IssueSeverity.LOW)
        self.info_count = sum(1 for i in self.issues if i.severity == IssueSeverity.INFO)
        self.ai_slop_count = sum(1 for i in self.issues if i.category == "ai_slop")
        self.ai_slop_detected = self.ai_slop_count > 0
        # Security auto-calculate
        sec_issues = [i for i in self.issues if i.category == "security"]
        self.security_issues_count = len(sec_issues)
        self.secret_leak_detected = any(
            i.threat_type == "secret_leak" for i in self.issues if i.threat_type
        )
        owasp_hits = {i.owasp_id for i in self.issues if i.owasp_id}
        self.owasp_categories_hit = sorted(owasp_hits)
        if self.security_issues_count > 0:
            penalty = sum(
                {"critical": 4, "high": 2, "medium": 1}.get(i.severity.value, 0)
                for i in sec_issues
            )
            self.security_score = max(0, 10 - penalty)


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

