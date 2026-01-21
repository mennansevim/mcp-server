"""
Service for formatting and posting review comments
"""
import structlog
from typing import List, Dict
from models import ReviewResult, ReviewIssue, IssueSeverity

logger = structlog.get_logger()


class CommentService:
    """Format review results as comments"""
    
    SEVERITY_EMOJI = {
        IssueSeverity.CRITICAL: "🔴",
        IssueSeverity.HIGH: "🟠",
        IssueSeverity.MEDIUM: "🟡",
        IssueSeverity.LOW: "🔵",
        IssueSeverity.INFO: "ℹ️",
    }
    
    # Issue category to type mapping
    CATEGORY_TYPE_MAP = {
        'security': 'Security',
        'bugs': 'Reliability',
        'bug': 'Reliability',
        'performance': 'Reliability',
        'reliability': 'Reliability',
        'code_quality': 'Maintainability',
        'best_practices': 'Maintainability',
        'maintainability': 'Maintainability',
        'style': 'Maintainability',
        'compilation': 'Reliability',
        'general': 'Maintainability'
    }
    
    @staticmethod
    def _generate_severity_type_table(result: ReviewResult) -> str:
        """
        Generate a simple issue summary table
        
        Args:
            result: ReviewResult
            
        Returns:
            Markdown formatted summary
        """
        if not result.issues:
            return ""
        
        # Count by severity
        severity_counts = {
            'critical': 0,
            'high': 0, 
            'medium': 0,
            'low': 0,
            'info': 0
        }
        
        # Count by category
        category_counts = {}
        
        for issue in result.issues:
            sev = issue.severity.value.lower()
            if sev in severity_counts:
                severity_counts[sev] += 1
            
            cat = issue.category.lower()
            category_counts[cat] = category_counts.get(cat, 0) + 1
        
        lines = []
        
        # Severity summary
        if any(severity_counts.values()):
            lines.append("### 📊 Issue Summary")
            lines.append("")
            lines.append("| Severity | Count |")
            lines.append("|:---------|------:|")
            
            if severity_counts['critical'] > 0:
                lines.append(f"| 🔴 Critical | {severity_counts['critical']} |")
            if severity_counts['high'] > 0:
                lines.append(f"| 🟠 High | {severity_counts['high']} |")
            if severity_counts['medium'] > 0:
                lines.append(f"| 🟡 Medium | {severity_counts['medium']} |")
            if severity_counts['low'] > 0:
                lines.append(f"| 🔵 Low | {severity_counts['low']} |")
            if severity_counts['info'] > 0:
                lines.append(f"| ℹ️ Info | {severity_counts['info']} |")
            
            lines.append("")
        
        # Category summary
        if category_counts:
            lines.append("### 📂 By Category")
            lines.append("")
            lines.append("| Category | Count |")
            lines.append("|:---------|------:|")
            
            for cat, count in sorted(category_counts.items(), key=lambda x: -x[1]):
                lines.append(f"| {cat.title()} | {count} |")
            
            lines.append("")
        
        return "\n".join(lines)
    
    @staticmethod
    def format_summary_comment(result: ReviewResult, show_detailed_table: bool = False) -> str:
        """
        Format review result as a simple, readable comment
        
        Args:
            result: ReviewResult to format
            show_detailed_table: Ignored - kept for compatibility
            
        Returns:
            Markdown formatted comment
        """
        lines = []
        
        # Header with score
        score_icon = '✅' if result.score >= 8 else '⚠️' if result.score >= 6 else '❌'
        lines.append(f"## 🤖 MCP AI Code Review - {result.score}/10 {score_icon}")
        lines.append("")
        
        # Summary
        lines.append("### 📝 Summary")
        lines.append("")
        lines.append(result.summary.strip())
        lines.append("")
        
        # Issues count - simple text
        if result.total_issues > 0:
            lines.append("---")
            lines.append("")
            counts = []
            if result.critical_count > 0:
                counts.append(f"🔴 {result.critical_count} Critical")
            if result.high_count > 0:
                counts.append(f"🟠 {result.high_count} High")
            if result.medium_count > 0:
                counts.append(f"🟡 {result.medium_count} Medium")
            if result.low_count > 0:
                counts.append(f"🔵 {result.low_count} Low")
            
            lines.append(f"**Issues:** {result.total_issues} total ({', '.join(counts)})")
            lines.append("")
        
        # Critical and High issues - simple list
        critical_high = [i for i in result.issues if i.severity in [IssueSeverity.CRITICAL, IssueSeverity.HIGH]]
        if critical_high:
            lines.append("---")
            lines.append("")
            lines.append("### ⚠️ Issues")
            lines.append("")
            
            for issue in critical_high[:10]:
                emoji = CommentService.SEVERITY_EMOJI[issue.severity]
                
                # Simple format
                lines.append(f"**{emoji} {issue.title}**")
                
                if issue.file_path:
                    location = f"`{issue.file_path}`"
                    if issue.line_number:
                        location += f" line {issue.line_number}"
                    lines.append(f"📁 {location}")
                
                lines.append("")
                lines.append(issue.description)
                
                if issue.suggestion:
                    lines.append("")
                    lines.append(f"💡 *{issue.suggestion}*")
                
                lines.append("")
                lines.append("---")
                lines.append("")
        
        # Recommendation
        if result.block_merge:
            lines.append("❌ **Do not merge** - Fix critical issues first.")
        elif result.approval_recommended:
            lines.append("✅ **Approved**")
        else:
            lines.append("⚠️ **Review recommended**")
        
        lines.append("")
        lines.append(f"*MCP AI Code Review | Score: {result.score}/10*")
        
        return "\n".join(lines)
    
    @staticmethod
    def format_inline_comment(issue: ReviewIssue) -> str:
        """
        Format a single issue as an inline comment
        
        Args:
            issue: ReviewIssue to format
            
        Returns:
            Markdown formatted inline comment
        """
        emoji = CommentService.SEVERITY_EMOJI[issue.severity]
        
        lines = [
            f"{emoji} **{issue.severity.value.upper()}: {issue.title}**",
            "",
            issue.description,
        ]
        
        if issue.suggestion:
            lines.extend([
                "",
                "**Suggestion:**",
                f"> {issue.suggestion}"
            ])
        
        lines.extend([
            "",
            f"*Category: {issue.category}*"
        ])
        
        return "\n".join(lines)
    
    @staticmethod
    def format_inline_comments(result: ReviewResult) -> List[dict]:
        """
        Format issues as inline comments with file and line info
        
        Args:
            result: ReviewResult
            
        Returns:
            List of inline comment data
        """
        comments = []
        
        for issue in result.issues:
            if issue.file_path and issue.line_number:
                comments.append({
                    'file_path': issue.file_path,
                    'line': issue.line_number,
                    'body': CommentService.format_inline_comment(issue)
                })
        
        return comments

