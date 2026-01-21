package com.mcpreview.rider.service

import com.google.gson.Gson
import com.google.gson.GsonBuilder
import com.intellij.openapi.application.ApplicationManager
import com.intellij.openapi.components.Service
import com.intellij.openapi.diagnostic.Logger
import com.mcpreview.rider.model.ReviewRequest
import com.mcpreview.rider.model.ReviewResponse
import com.mcpreview.rider.model.ReviewResult
import com.mcpreview.rider.settings.McpSettings
import okhttp3.*
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.RequestBody.Companion.toRequestBody
import java.io.IOException
import java.util.concurrent.TimeUnit

@Service
class McpClient {
    
    private val logger = Logger.getInstance(McpClient::class.java)
    private val gson: Gson = GsonBuilder().create()
    
    private fun createHttpClient(): OkHttpClient {
        val settings = McpSettings.getInstance()
        return OkHttpClient.Builder()
            .connectTimeout(settings.timeout.toLong(), TimeUnit.SECONDS)
            .readTimeout(settings.timeout.toLong(), TimeUnit.SECONDS)
            .writeTimeout(settings.timeout.toLong(), TimeUnit.SECONDS)
            .build()
    }
    
    /**
     * Check if MCP server is available
     */
    fun checkHealth(): Boolean {
        val settings = McpSettings.getInstance()
        val client = createHttpClient()
        
        val request = Request.Builder()
            .url("${settings.serverUrl}/")
            .get()
            .build()
        
        return try {
            client.newCall(request).execute().use { response ->
                response.isSuccessful
            }
        } catch (e: Exception) {
            logger.warn("MCP server health check failed", e)
            false
        }
    }
    
    /**
     * Send code for review
     */
    fun reviewCode(
        diff: String,
        files: List<String>,
        focusAreas: List<String> = listOf("compilation", "security", "performance", "bugs", "code_quality"),
        callback: (Result<ReviewResult>) -> Unit
    ) {
        val settings = McpSettings.getInstance()
        val client = createHttpClient()
        
        val reviewRequest = ReviewRequest(diff, files, focusAreas)
        val jsonBody = gson.toJson(reviewRequest)
        
        val requestBody = jsonBody.toRequestBody("application/json".toMediaType())
        
        val request = Request.Builder()
            .url("${settings.serverUrl}/review")
            .post(requestBody)
            .addHeader("Content-Type", "application/json")
            .build()
        
        client.newCall(request).enqueue(object : Callback {
            override fun onFailure(call: Call, e: IOException) {
                logger.error("MCP review request failed", e)
                ApplicationManager.getApplication().invokeLater {
                    callback(Result.failure(e))
                }
            }
            
            override fun onResponse(call: Call, response: Response) {
                response.use {
                    if (!response.isSuccessful) {
                        val error = IOException("Unexpected response: ${response.code}")
                        ApplicationManager.getApplication().invokeLater {
                            callback(Result.failure(error))
                        }
                        return
                    }
                    
                    val body = response.body?.string()
                    if (body == null) {
                        ApplicationManager.getApplication().invokeLater {
                            callback(Result.failure(IOException("Empty response body")))
                        }
                        return
                    }
                    
                    try {
                        val reviewResponse = gson.fromJson(body, ReviewResponse::class.java)
                        
                        if (reviewResponse.status == "success" && reviewResponse.review != null) {
                            ApplicationManager.getApplication().invokeLater {
                                callback(Result.success(reviewResponse.review))
                            }
                        } else {
                            ApplicationManager.getApplication().invokeLater {
                                callback(Result.failure(IOException(reviewResponse.message ?: "Review failed")))
                            }
                        }
                    } catch (e: Exception) {
                        logger.error("Failed to parse review response", e)
                        ApplicationManager.getApplication().invokeLater {
                            callback(Result.failure(e))
                        }
                    }
                }
            }
        })
    }
    
    /**
     * Send diff via webhook (compatible with existing server)
     */
    fun reviewViaWebhook(
        diff: String,
        files: List<String>,
        callback: (Result<String>) -> Unit
    ) {
        val settings = McpSettings.getInstance()
        val client = createHttpClient()
        
        // Create a minimal webhook payload
        val payload = mapOf(
            "action" to "ide_review",
            "diff" to diff,
            "files" to files,
            "source" to "rider-plugin"
        )
        
        val jsonBody = gson.toJson(payload)
        val requestBody = jsonBody.toRequestBody("application/json".toMediaType())
        
        val request = Request.Builder()
            .url("${settings.serverUrl}/ide/review")
            .post(requestBody)
            .addHeader("Content-Type", "application/json")
            .addHeader("X-IDE-Client", "Rider")
            .build()
        
        client.newCall(request).enqueue(object : Callback {
            override fun onFailure(call: Call, e: IOException) {
                logger.error("MCP webhook request failed", e)
                ApplicationManager.getApplication().invokeLater {
                    callback(Result.failure(e))
                }
            }
            
            override fun onResponse(call: Call, response: Response) {
                response.use {
                    val body = response.body?.string() ?: ""
                    ApplicationManager.getApplication().invokeLater {
                        if (response.isSuccessful) {
                            callback(Result.success(body))
                        } else {
                            callback(Result.failure(IOException("Server error: ${response.code} - $body")))
                        }
                    }
                }
            }
        })
    }
    
    companion object {
        fun getInstance(): McpClient {
            return ApplicationManager.getApplication().getService(McpClient::class.java)
        }
    }
}

