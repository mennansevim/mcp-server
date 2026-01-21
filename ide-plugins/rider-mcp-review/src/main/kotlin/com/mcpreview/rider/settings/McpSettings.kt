package com.mcpreview.rider.settings

import com.intellij.openapi.application.ApplicationManager
import com.intellij.openapi.components.PersistentStateComponent
import com.intellij.openapi.components.State
import com.intellij.openapi.components.Storage

@State(
    name = "McpCodeReviewSettings",
    storages = [Storage("McpCodeReview.xml")]
)
class McpSettings : PersistentStateComponent<McpSettings.State> {
    
    data class State(
        var serverUrl: String = "http://localhost:8000",
        var autoReviewOnCommit: Boolean = false,
        var showInlineHighlights: Boolean = true,
        var minimumSeverity: String = "medium", // critical, high, medium, low, info
        var timeout: Int = 60 // seconds
    )
    
    private var myState = State()
    
    override fun getState(): State = myState
    
    override fun loadState(state: State) {
        myState = state
    }
    
    var serverUrl: String
        get() = myState.serverUrl
        set(value) { myState.serverUrl = value }
    
    var autoReviewOnCommit: Boolean
        get() = myState.autoReviewOnCommit
        set(value) { myState.autoReviewOnCommit = value }
    
    var showInlineHighlights: Boolean
        get() = myState.showInlineHighlights
        set(value) { myState.showInlineHighlights = value }
    
    var minimumSeverity: String
        get() = myState.minimumSeverity
        set(value) { myState.minimumSeverity = value }
    
    var timeout: Int
        get() = myState.timeout
        set(value) { myState.timeout = value }
    
    companion object {
        fun getInstance(): McpSettings {
            return ApplicationManager.getApplication().getService(McpSettings::class.java)
        }
    }
}

