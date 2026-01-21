package com.mcpreview.rider.settings

import com.intellij.openapi.options.Configurable
import com.intellij.ui.components.JBCheckBox
import com.intellij.ui.components.JBLabel
import com.intellij.ui.components.JBTextField
import com.intellij.util.ui.FormBuilder
import javax.swing.JComponent
import javax.swing.JPanel
import javax.swing.JComboBox

class McpSettingsConfigurable : Configurable {
    
    private var settingsPanel: JPanel? = null
    private var serverUrlField: JBTextField? = null
    private var autoReviewCheckbox: JBCheckBox? = null
    private var inlineHighlightsCheckbox: JBCheckBox? = null
    private var severityCombo: JComboBox<String>? = null
    private var timeoutField: JBTextField? = null
    
    override fun getDisplayName(): String = "MCP Code Review"
    
    override fun createComponent(): JComponent {
        serverUrlField = JBTextField()
        autoReviewCheckbox = JBCheckBox("Auto-review on commit")
        inlineHighlightsCheckbox = JBCheckBox("Show inline highlights in editor")
        severityCombo = JComboBox(arrayOf("critical", "high", "medium", "low", "info"))
        timeoutField = JBTextField()
        
        settingsPanel = FormBuilder.createFormBuilder()
            .addLabeledComponent(JBLabel("MCP Server URL:"), serverUrlField!!, 1, false)
            .addComponent(autoReviewCheckbox!!, 1)
            .addComponent(inlineHighlightsCheckbox!!, 1)
            .addLabeledComponent(JBLabel("Minimum severity to show:"), severityCombo!!, 1, false)
            .addLabeledComponent(JBLabel("Timeout (seconds):"), timeoutField!!, 1, false)
            .addComponentFillVertically(JPanel(), 0)
            .panel
        
        return settingsPanel!!
    }
    
    override fun isModified(): Boolean {
        val settings = McpSettings.getInstance()
        return serverUrlField?.text != settings.serverUrl ||
               autoReviewCheckbox?.isSelected != settings.autoReviewOnCommit ||
               inlineHighlightsCheckbox?.isSelected != settings.showInlineHighlights ||
               severityCombo?.selectedItem != settings.minimumSeverity ||
               timeoutField?.text != settings.timeout.toString()
    }
    
    override fun apply() {
        val settings = McpSettings.getInstance()
        settings.serverUrl = serverUrlField?.text ?: "http://localhost:8000"
        settings.autoReviewOnCommit = autoReviewCheckbox?.isSelected ?: false
        settings.showInlineHighlights = inlineHighlightsCheckbox?.isSelected ?: true
        settings.minimumSeverity = severityCombo?.selectedItem as? String ?: "medium"
        settings.timeout = timeoutField?.text?.toIntOrNull() ?: 60
    }
    
    override fun reset() {
        val settings = McpSettings.getInstance()
        serverUrlField?.text = settings.serverUrl
        autoReviewCheckbox?.isSelected = settings.autoReviewOnCommit
        inlineHighlightsCheckbox?.isSelected = settings.showInlineHighlights
        severityCombo?.selectedItem = settings.minimumSeverity
        timeoutField?.text = settings.timeout.toString()
    }
}

