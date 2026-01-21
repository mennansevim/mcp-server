package com.mcpreview.rider.actions

import com.intellij.notification.NotificationGroupManager
import com.intellij.notification.NotificationType
import com.intellij.openapi.actionSystem.AnAction
import com.intellij.openapi.actionSystem.AnActionEvent
import com.intellij.openapi.progress.ProgressIndicator
import com.intellij.openapi.progress.ProgressManager
import com.intellij.openapi.progress.Task
import com.intellij.openapi.wm.ToolWindowManager
import com.mcpreview.rider.service.GitService
import com.mcpreview.rider.service.McpClient
import com.mcpreview.rider.ui.McpToolWindowFactory

class ReviewUncommittedChangesAction : AnAction() {
    
    override fun actionPerformed(e: AnActionEvent) {
        val project = e.project ?: return
        
        val gitService = GitService(project)
        val mcpClient = McpClient.getInstance()
        
        ProgressManager.getInstance().run(object : Task.Backgroundable(project, "MCP AI Code Review - All Changes", true) {
            override fun run(indicator: ProgressIndicator) {
                indicator.text = "Getting uncommitted changes..."
                indicator.fraction = 0.2
                
                val diff = gitService.getUncommittedDiff()
                val files = gitService.getChangedFiles()
                
                if (diff.isBlank()) {
                    showNotification(project, "No uncommitted changes found", NotificationType.WARNING)
                    return
                }
                
                indicator.text = "Reviewing ${files.size} changed file(s)..."
                indicator.fraction = 0.4
                
                mcpClient.reviewViaWebhook(diff, files) { result ->
                    result.fold(
                        onSuccess = { response ->
                            indicator.fraction = 1.0
                            showNotification(project, "Review completed for ${files.size} file(s)", NotificationType.INFORMATION)
                            
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
        e.presentation.isEnabled = e.project != null
    }
    
    private fun showNotification(project: com.intellij.openapi.project.Project, content: String, type: NotificationType) {
        NotificationGroupManager.getInstance()
            .getNotificationGroup("MCP Code Review")
            .createNotification(content, type)
            .notify(project)
    }
}

