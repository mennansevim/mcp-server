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
import com.mcpreview.rider.service.GitService
import com.mcpreview.rider.service.McpClient
import com.mcpreview.rider.ui.McpToolWindowFactory

class ReviewCurrentFileAction : AnAction() {
    
    override fun actionPerformed(e: AnActionEvent) {
        val project = e.project ?: return
        val file = e.getData(CommonDataKeys.VIRTUAL_FILE) ?: return
        
        val gitService = GitService(project)
        val mcpClient = McpClient.getInstance()
        
        ProgressManager.getInstance().run(object : Task.Backgroundable(project, "MCP AI Code Review", true) {
            override fun run(indicator: ProgressIndicator) {
                indicator.text = "Getting file diff..."
                indicator.fraction = 0.2
                
                val diff = gitService.getFileDiff(file)
                
                if (diff.isBlank()) {
                    showNotification(project, "No changes detected in ${file.name}", NotificationType.WARNING)
                    return
                }
                
                indicator.text = "Sending to MCP server..."
                indicator.fraction = 0.4
                
                mcpClient.reviewViaWebhook(diff, listOf(file.path)) { result ->
                    result.fold(
                        onSuccess = { response ->
                            indicator.fraction = 1.0
                            showNotification(project, "Review completed for ${file.name}", NotificationType.INFORMATION)
                            
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
        val file = e.getData(CommonDataKeys.VIRTUAL_FILE)
        e.presentation.isEnabled = file != null && !file.isDirectory
    }
    
    private fun showNotification(project: com.intellij.openapi.project.Project, content: String, type: NotificationType) {
        NotificationGroupManager.getInstance()
            .getNotificationGroup("MCP Code Review")
            .createNotification(content, type)
            .notify(project)
    }
}

