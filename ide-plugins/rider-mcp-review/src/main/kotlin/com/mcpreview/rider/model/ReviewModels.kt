package com.mcpreview.rider.model

import com.google.gson.annotations.SerializedName

/**
 * Request model for code review
 */
data class ReviewRequest(
    val diff: String,
    val files: List<String>,
    @SerializedName("focus_areas")
    val focusAreas: List<String> = listOf("compilation", "security", "performance", "bugs", "code_quality")
)

/**
 * Response model from MCP server
 */
data class ReviewResponse(
    val status: String,
    val message: String? = null,
    val review: ReviewResult? = null
)

/**
 * Review result containing all findings
 */
data class ReviewResult(
    val summary: String,
    val score: Int,
    val issues: List<ReviewIssue>,
    @SerializedName("approval_recommended")
    val approvalRecommended: Boolean,
    @SerializedName("block_merge")
    val blockMerge: Boolean
)

/**
 * Individual review issue
 */
data class ReviewIssue(
    val severity: String,
    val title: String,
    val description: String,
    val category: String,
    @SerializedName("file_path")
    val filePath: String? = null,
    @SerializedName("line_number")
    val lineNumber: Int? = null,
    val suggestion: String? = null,
    @SerializedName("code_snippet")
    val codeSnippet: String? = null
) {
    val severityLevel: IssueSeverity
        get() = IssueSeverity.fromString(severity)
}

/**
 * Issue severity levels
 */
enum class IssueSeverity(val level: Int, val emoji: String, val color: String) {
    CRITICAL(5, "🔴", "#FF0000"),
    HIGH(4, "🟠", "#FFA500"),
    MEDIUM(3, "🟡", "#FFD700"),
    LOW(2, "🔵", "#0000FF"),
    INFO(1, "ℹ️", "#808080");
    
    companion object {
        fun fromString(value: String): IssueSeverity {
            return when (value.lowercase()) {
                "critical" -> CRITICAL
                "high" -> HIGH
                "medium" -> MEDIUM
                "low" -> LOW
                else -> INFO
            }
        }
    }
}

