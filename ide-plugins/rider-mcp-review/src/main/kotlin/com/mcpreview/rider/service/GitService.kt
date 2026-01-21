package com.mcpreview.rider.service

import com.intellij.openapi.project.Project
import com.intellij.openapi.vcs.changes.ChangeListManager
import com.intellij.openapi.vfs.VirtualFile
import git4idea.GitUtil
import git4idea.commands.Git
import git4idea.commands.GitCommand
import git4idea.commands.GitLineHandler
import git4idea.repo.GitRepository

/**
 * Service for Git operations
 */
class GitService(private val project: Project) {
    
    /**
     * Get the git repository for the project
     */
    fun getRepository(): GitRepository? {
        val repositories = GitUtil.getRepositoryManager(project).repositories
        return repositories.firstOrNull()
    }
    
    /**
     * Get diff for staged changes
     */
    fun getStagedDiff(): String {
        val repo = getRepository() ?: return ""
        val root = repo.root
        
        val handler = GitLineHandler(project, root, GitCommand.DIFF)
        handler.addParameters("--cached", "--no-color")
        
        val result = Git.getInstance().runCommand(handler)
        return if (result.success()) result.output.joinToString("\n") else ""
    }
    
    /**
     * Get diff for unstaged changes
     */
    fun getUnstagedDiff(): String {
        val repo = getRepository() ?: return ""
        val root = repo.root
        
        val handler = GitLineHandler(project, root, GitCommand.DIFF)
        handler.addParameters("--no-color")
        
        val result = Git.getInstance().runCommand(handler)
        return if (result.success()) result.output.joinToString("\n") else ""
    }
    
    /**
     * Get diff for all uncommitted changes (staged + unstaged)
     */
    fun getUncommittedDiff(): String {
        val repo = getRepository() ?: return ""
        val root = repo.root
        
        val handler = GitLineHandler(project, root, GitCommand.DIFF)
        handler.addParameters("HEAD", "--no-color")
        
        val result = Git.getInstance().runCommand(handler)
        return if (result.success()) result.output.joinToString("\n") else ""
    }
    
    /**
     * Get diff for a specific file
     */
    fun getFileDiff(file: VirtualFile): String {
        val repo = getRepository() ?: return ""
        val root = repo.root
        
        val handler = GitLineHandler(project, root, GitCommand.DIFF)
        handler.addParameters("HEAD", "--no-color", "--", file.path)
        
        val result = Git.getInstance().runCommand(handler)
        return if (result.success()) result.output.joinToString("\n") else ""
    }
    
    /**
     * Get list of changed files
     */
    fun getChangedFiles(): List<String> {
        val changeListManager = ChangeListManager.getInstance(project)
        return changeListManager.allChanges.mapNotNull { change ->
            change.virtualFile?.path ?: change.afterRevision?.file?.path
        }
    }
    
    /**
     * Get list of staged files
     */
    fun getStagedFiles(): List<String> {
        val repo = getRepository() ?: return emptyList()
        val root = repo.root
        
        val handler = GitLineHandler(project, root, GitCommand.DIFF)
        handler.addParameters("--cached", "--name-only")
        
        val result = Git.getInstance().runCommand(handler)
        return if (result.success()) {
            result.output.filter { it.isNotBlank() }
        } else {
            emptyList()
        }
    }
}

