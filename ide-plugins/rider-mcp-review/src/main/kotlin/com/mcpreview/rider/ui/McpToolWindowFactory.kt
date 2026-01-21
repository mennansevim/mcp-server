package com.mcpreview.rider.ui

import com.intellij.openapi.project.Project
import com.intellij.openapi.wm.ToolWindow
import com.intellij.openapi.wm.ToolWindowFactory
import com.intellij.ui.components.JBScrollPane
import com.intellij.ui.content.ContentFactory
import java.awt.BorderLayout
import javax.swing.JPanel
import javax.swing.JEditorPane
import javax.swing.text.html.HTMLEditorKit

class McpToolWindowFactory : ToolWindowFactory {
    
    override fun createToolWindowContent(project: Project, toolWindow: ToolWindow) {
        val panel = McpReviewPanel()
        val content = ContentFactory.getInstance().createContent(panel, "Review Results", false)
        toolWindow.contentManager.addContent(content)
        
        // Store panel reference for updates
        panelMap[project] = panel
        
        // Check if there's pending content to show
        pendingContent[project]?.let { response ->
            panel.updateContent(response)
            pendingContent.remove(project)
        }
    }
    
    companion object {
        private val panelMap = mutableMapOf<Project, McpReviewPanel>()
        private val pendingContent = mutableMapOf<Project, String>()
        
        fun updateContent(project: Project, response: String) {
            val panel = panelMap[project]
            if (panel != null) {
                // Panel exists, update directly
                com.intellij.openapi.application.ApplicationManager.getApplication().invokeLater {
                    panel.updateContent(response)
                }
            } else {
                // Panel not created yet, store for later
                pendingContent[project] = response
            }
        }
        
        fun clearContent(project: Project) {
            panelMap[project]?.clearContent()
        }
    }
}

class McpReviewPanel : JPanel(BorderLayout()) {
    
    private val editorPane: JEditorPane = JEditorPane().apply {
        isEditable = false
        contentType = "text/html"
        editorKit = HTMLEditorKit().apply {
            styleSheet.addRule("""
                body { 
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
                    font-size: 13px; 
                    padding: 16px;
                    background-color: #2b2b2b;
                    color: #a9b7c6;
                }
                h1 { color: #6897bb; font-size: 18px; margin-bottom: 8px; }
                h2 { color: #6897bb; font-size: 16px; margin-top: 16px; margin-bottom: 8px; }
                h3 { color: #6897bb; font-size: 14px; margin-top: 12px; margin-bottom: 6px; }
                .score { font-size: 24px; font-weight: bold; }
                .score-good { color: #6a8759; }
                .score-warning { color: #bbb529; }
                .score-bad { color: #cc7832; }
                .critical { background-color: #3c2828; border-left: 4px solid #cc0000; padding: 8px; margin: 8px 0; }
                .high { background-color: #3c3528; border-left: 4px solid #cc7832; padding: 8px; margin: 8px 0; }
                .medium { background-color: #3c3c28; border-left: 4px solid #bbb529; padding: 8px; margin: 8px 0; }
                .low { background-color: #283c3c; border-left: 4px solid #6897bb; padding: 8px; margin: 8px 0; }
                .info { background-color: #2b2b2b; border-left: 4px solid #808080; padding: 8px; margin: 8px 0; }
                .file-path { color: #9876aa; font-family: monospace; font-size: 12px; }
                .suggestion { background-color: #2d3c28; padding: 8px; margin: 8px 0; border-radius: 4px; }
                code { 
                    background-color: #3c3f41; 
                    padding: 2px 6px; 
                    border-radius: 3px; 
                    font-family: 'JetBrains Mono', Consolas, monospace;
                    font-size: 12px;
                }
                pre {
                    background-color: #3c3f41;
                    padding: 12px;
                    border-radius: 4px;
                    overflow-x: auto;
                    font-family: 'JetBrains Mono', Consolas, monospace;
                    font-size: 12px;
                }
                table { border-collapse: collapse; width: 100%; margin: 8px 0; }
                th, td { padding: 8px; text-align: left; border-bottom: 1px solid #3c3f41; }
                th { background-color: #3c3f41; color: #6897bb; }
                .emoji { font-size: 16px; }
                hr { border: none; border-top: 1px solid #3c3f41; margin: 16px 0; }
            """.trimIndent())
        }
    }
    
    init {
        add(JBScrollPane(editorPane), BorderLayout.CENTER)
        showWelcome()
    }
    
    private fun showWelcome() {
        editorPane.text = """
            <html>
            <body>
                <h1>🤖 MCP AI Code Review</h1>
                <p>Welcome! Use the following commands to review your code:</p>
                <ul>
                    <li><strong>Ctrl+Alt+R</strong> - Review current file</li>
                    <li><strong>Ctrl+Alt+Shift+R</strong> - Review selection</li>
                    <li><strong>Tools → MCP Review → Review Staged Changes</strong></li>
                    <li><strong>Tools → MCP Review → Review Uncommitted Changes</strong></li>
                </ul>
                <hr/>
                <p><em>Configure your MCP Server URL in Settings → Tools → MCP Code Review</em></p>
            </body>
            </html>
        """.trimIndent()
    }
    
    fun updateContent(response: String) {
        // Parse JSON response and format as HTML
        val html = formatResponseAsHtml(response)
        editorPane.text = html
        editorPane.caretPosition = 0
    }
    
    fun clearContent() {
        showWelcome()
    }
    
    private fun formatResponseAsHtml(response: String): String {
        // Try to parse as JSON, otherwise show raw
        return try {
            val gson = com.google.gson.Gson()
            val result = gson.fromJson(response, Map::class.java)
            
            buildString {
                append("<html><body>")
                append("<h1>🤖 MCP AI Code Review</h1>")
                
                // Score
                val score = (result["score"] as? Number)?.toInt() ?: 0
                val scoreClass = when {
                    score >= 8 -> "score-good"
                    score >= 6 -> "score-warning"
                    else -> "score-bad"
                }
                append("<p class='score $scoreClass'>Score: $score/10</p>")
                
                // Summary
                val summary = result["summary"] as? String ?: "No summary available"
                append("<h2>📝 Summary</h2>")
                append("<p>${summary.replace("\n", "<br/>")}</p>")
                
                // Issues
                @Suppress("UNCHECKED_CAST")
                val issues = result["issues"] as? List<Map<String, Any>> ?: emptyList()
                
                if (issues.isNotEmpty()) {
                    append("<h2>⚠️ Issues Found (${issues.size})</h2>")
                    
                    for (issue in issues) {
                        val severity = (issue["severity"] as? String)?.lowercase() ?: "info"
                        val title = issue["title"] as? String ?: "Issue"
                        val description = issue["description"] as? String ?: ""
                        val filePath = issue["file_path"] as? String
                        val lineNumber = (issue["line_number"] as? Number)?.toInt()
                        val suggestion = issue["suggestion"] as? String
                        
                        append("<div class='$severity'>")
                        append("<h3>${getSeverityEmoji(severity)} $title</h3>")
                        
                        if (filePath != null) {
                            append("<p class='file-path'>📁 $filePath")
                            if (lineNumber != null) {
                                append(" (Line $lineNumber)")
                            }
                            append("</p>")
                        }
                        
                        append("<p>${description.replace("\n", "<br/>")}</p>")
                        
                        if (suggestion != null) {
                            append("<div class='suggestion'>")
                            append("<strong>💡 Suggestion:</strong><br/>")
                            append(suggestion.replace("\n", "<br/>"))
                            append("</div>")
                        }
                        
                        append("</div>")
                    }
                } else {
                    append("<h2>✅ No Issues Found</h2>")
                    append("<p>Great job! Your code looks good.</p>")
                }
                
                // Recommendation
                append("<hr/>")
                val blockMerge = result["block_merge"] as? Boolean ?: false
                val approved = result["approval_recommended"] as? Boolean ?: true
                
                if (blockMerge) {
                    append("<p>❌ <strong>Do not merge</strong> - Critical issues must be fixed first.</p>")
                } else if (approved) {
                    append("<p>✅ <strong>Approved</strong> - Code looks good!</p>")
                } else {
                    append("<p>⚠️ <strong>Review recommended</strong> - Please address the issues above.</p>")
                }
                
                append("</body></html>")
            }
        } catch (e: Exception) {
            // If parsing fails, show raw response
            """
            <html>
            <body>
                <h1>🤖 MCP AI Code Review</h1>
                <h2>Response</h2>
                <pre>${response.replace("<", "&lt;").replace(">", "&gt;")}</pre>
            </body>
            </html>
            """.trimIndent()
        }
    }
    
    private fun getSeverityEmoji(severity: String): String {
        return when (severity) {
            "critical" -> "🔴"
            "high" -> "🟠"
            "medium" -> "🟡"
            "low" -> "🔵"
            else -> "ℹ️"
        }
    }
}

