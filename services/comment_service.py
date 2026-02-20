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
        Generate detailed severity x type table with file-level breakdown
        
        Args:
            result: ReviewResult
            
        Returns:
            Markdown table string
        """
        # Initialize overall counters
        overall = {
            'Security': {'CRITICAL': 0, 'HIGH': 0, 'MEDIUM': 0},
            'Maintainability': {'CRITICAL': 0, 'HIGH': 0, 'MEDIUM': 0},
            'Reliability': {'CRITICAL': 0, 'HIGH': 0, 'MEDIUM': 0}
        }
        
        # Initialize file-level counters
        files = {}
        
        # Count issues by severity and type
        for issue in result.issues:
            if issue.severity not in [IssueSeverity.CRITICAL, IssueSeverity.HIGH, IssueSeverity.MEDIUM]:
                continue
            
            issue_type = CommentService.CATEGORY_TYPE_MAP.get(
                issue.category.lower(), 
                'Maintainability'
            )
            severity_upper = issue.severity.value.upper()
            
            # Update overall counts
            if severity_upper in overall[issue_type]:
                overall[issue_type][severity_upper] += 1
            
            # Update file-level counts
            if issue.file_path:
                if issue.file_path not in files:
                    files[issue.file_path] = {
                        'Security': {'CRITICAL': 0, 'HIGH': 0, 'MEDIUM': 0},
                        'Maintainability': {'CRITICAL': 0, 'HIGH': 0, 'MEDIUM': 0},
                        'Reliability': {'CRITICAL': 0, 'HIGH': 0, 'MEDIUM': 0}
                    }
                files[issue.file_path][issue_type][severity_upper] += 1
        
        # Build table header
        lines = [
            "### 📊 Detaylı Analiz Özeti (Severity × Type)",
            "",
            "| Scope / File Path | 🔴 Critical<br/>Security | 🔴 Critical<br/>Maintainability | 🔴 Critical<br/>Reliability | 🟠 Major<br/>Security | 🟠 Major<br/>Maintainability | 🟠 Major<br/>Reliability | 🟡 Minor<br/>Security | 🟡 Minor<br/>Maintainability | 🟡 Minor<br/>Reliability |",
            "|:------------------|:----------:|:---------------:|:-------------:|:--------:|:---------------:|:-------------:|:--------:|:---------------:|:-------------:|",
        ]
        
        # Add overall row
        overall_row = f"| **Overall** | {overall['Security']['CRITICAL']} | {overall['Maintainability']['CRITICAL']} | {overall['Reliability']['CRITICAL']} | {overall['Security']['HIGH']} | {overall['Maintainability']['HIGH']} | {overall['Reliability']['HIGH']} | {overall['Security']['MEDIUM']} | {overall['Maintainability']['MEDIUM']} | {overall['Reliability']['MEDIUM']} |"
        lines.append(overall_row)
        
        # Add file rows (sorted by total issues descending)
        sorted_files = sorted(
            files.items(),
            key=lambda x: sum(sum(severity.values()) for severity in x[1].values()),
            reverse=True
        )
        
        for file_path, matrix in sorted_files[:10]:  # Limit to top 10 files
            file_row = f"| `{file_path}` | {matrix['Security']['CRITICAL']} | {matrix['Maintainability']['CRITICAL']} | {matrix['Reliability']['CRITICAL']} | {matrix['Security']['HIGH']} | {matrix['Maintainability']['HIGH']} | {matrix['Reliability']['HIGH']} | {matrix['Security']['MEDIUM']} | {matrix['Maintainability']['MEDIUM']} | {matrix['Reliability']['MEDIUM']} |"
            lines.append(file_row)
        
        if len(files) > 10:
            lines.append(f"| *... ve {len(files) - 10} dosya daha* | - | - | - | - | - | - | - | - | - |")
        
        lines.append("")
        
        return "\n".join(lines)
    
    @staticmethod
    def format_summary_comment(result: ReviewResult, show_detailed_table: bool = False) -> str:
        """
        Format review result as a summary comment
        
        Args:
            result: ReviewResult to format
            show_detailed_table: Whether to show detailed severity x type table
            
        Returns:
            Markdown formatted comment
        """
        # Header
        lines = [
            "## MCP AI Code Review",
            "",
            f"**Score:** {result.score}/10 {'✅' if result.score >= 8 else '⚠️' if result.score >= 6 else '❌'}",
            "",
        ]
        
        # Add detailed table if requested
        if show_detailed_table:
            lines.append(CommentService._generate_severity_type_table(result))
        
        # Summary
        lines.extend([
            "### 📝 Summary",
            result.summary,
            "",
        ])
        
        # Statistics
        if result.total_issues > 0:
            lines.extend([
                "### 📊 Issues Found",
                f"- Total: **{result.total_issues}**",
            ])
            
            if result.critical_count > 0:
                lines.append(f"- {CommentService.SEVERITY_EMOJI[IssueSeverity.CRITICAL]} Critical: **{result.critical_count}**")
            if result.high_count > 0:
                lines.append(f"- {CommentService.SEVERITY_EMOJI[IssueSeverity.HIGH]} High: **{result.high_count}**")
            if result.medium_count > 0:
                lines.append(f"- {CommentService.SEVERITY_EMOJI[IssueSeverity.MEDIUM]} Medium: **{result.medium_count}**")
            if result.low_count > 0:
                lines.append(f"- {CommentService.SEVERITY_EMOJI[IssueSeverity.LOW]} Low: **{result.low_count}**")
            if result.info_count > 0:
                lines.append(f"- {CommentService.SEVERITY_EMOJI[IssueSeverity.INFO]} Info: **{result.info_count}**")
            
            lines.append("")
        
        # Critical and High issues detail
        critical_high = [i for i in result.issues if i.severity in [IssueSeverity.CRITICAL, IssueSeverity.HIGH]]
        if critical_high:
            lines.extend([
                "### ⚠️ Important Issues",
                "",
            ])
            
            for issue in critical_high[:10]:  # Limit to 10
                emoji = CommentService.SEVERITY_EMOJI[issue.severity]
                lines.extend([
                    f"#### {emoji} {issue.title}",
                    f"**Severity:** {issue.severity.value.upper()}  ",
                    f"**Category:** {issue.category}  ",
                ])
                
                if issue.file_path:
                    location = f"`{issue.file_path}`"
                    if issue.line_number:
                        location += f" (Line {issue.line_number})"
                    lines.append(f"**Location:** {location}  ")
                
                lines.extend([
                    "",
                    issue.description,
                    "",
                ])
                
                if issue.suggestion:
                    lines.extend([
                        "**Suggestion:**",
                        f"> {issue.suggestion}",
                        "",
                    ])
        
        # Recommendation
        lines.extend([
            "### 🎯 Recommendation",
            "",
        ])
        
        if result.block_merge:
            lines.append("❌ **Do not merge** - Critical issues must be fixed first.")
        elif result.approval_recommended:
            lines.append("✅ **Approved** - Code looks good!")
        else:
            lines.append("⚠️ **Review recommended** - Please address the issues above.")
        
        lines.extend([
            "",
            "---",
            "*Generated by MCP AI Code Review Server*",
            f"*Review Score: {result.score}/10*"
        ])
        
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

