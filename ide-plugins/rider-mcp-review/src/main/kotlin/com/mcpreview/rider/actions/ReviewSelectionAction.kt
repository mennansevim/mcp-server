package com.mcpreview.rider.actions

import com.intellij.notification.NotificationGroupManager
import com.intellij.notification.NotificationType
import com.intellij.openapi.actionSystem.AnAction
import com.intellij.openapi.actionSystem.AnActionEvent
import com.intellij.openapi.actionSystem.CommonDataKeys
import com.intellij.openapi.progress.ProgressIndicator
import com.intellij.openapi.progress.ProgressManager
import com.intellij.openapi.progress.Task
import com.intellij.openapi.wm.ToolWindowManager
import com.mcpreview.rider.service.McpClient
import com.mcpreview.rider.ui.McpToolWindowFactory

class ReviewSelectionAction : AnAction() {
    
    override fun actionPerformed(e: AnActionEvent) {
        val project = e.project ?: return
        val editor = e.getData(CommonDataKeys.EDITOR) ?: return
        val file = e.getData(CommonDataKeys.VIRTUAL_FILE) ?: return
        
        val selectionModel = editor.selectionModel
        val selectedText = selectionModel.selectedText
        
        if (selectedText.isNullOrBlank()) {
            showNotification(project, "No code selected", NotificationType.WARNING)
            return
        }
        
        val mcpClient = McpClient.getInstance()
        
        // Create a pseudo-diff for the selection
        val startLine = editor.document.getLineNumber(selectionModel.selectionStart) + 1
        val diff = buildString {
            appendLine("--- a/${file.name}")
            appendLine("+++ b/${file.name}")
            appendLine("@@ -$startLine,${selectedText.lines().size} +$startLine,${selectedText.lines().size} @@")
            selectedText.lines().forEach { line ->
                appendLine("+$line")
            }
        }
        
        ProgressManager.getInstance().run(object : Task.Backgroundable(project, "MCP AI Code Review", true) {
            override fun run(indicator: ProgressIndicator) {
                indicator.text = "Reviewing selected code..."
                indicator.fraction = 0.3
                
                mcpClient.reviewViaWebhook(diff, listOf(file.path)) { result ->
                    result.fold(
                        onSuccess = { response ->
                            indicator.fraction = 1.0
                            showNotification(project, "Review completed", NotificationType.INFORMATION)
                            
                            // Open tool window with results
                            val toolWindow = ToolWindowManager.getInstance(project).getToolWindow("MCP Review")
                            toolWindow?.show {
                                McpToolWindowFactory.updateContent(project, response)
                            }
                        },
                        onFailure = { error ->
                            showNotification(project, "Review failed: ${error.message}", NotificationType.ERROR)
                        }
                    )
                }
            }
        })
    }
    
    override fun update(e: AnActionEvent) {
        val editor = e.getData(CommonDataKeys.EDITOR)
        e.presentation.isEnabled = editor?.selectionModel?.hasSelection() == true
    }
    
    private fun showNotification(project: com.intellij.openapi.project.Project, content: String, type: NotificationType) {
        NotificationGroupManager.getInstance()
            .getNotificationGroup("MCP Code Review")
            .createNotification(content, type)
            .notify(project)
    }
}

