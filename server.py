"""
MCP Code Review Server
Platform-agnostic AI-powered code review via webhooks and MCP tools
"""
import os
import yaml
import structlog
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

# MCP SDK
from mcp.server import Server
from mcp.server.sse import SseServerTransport
from mcp.types import Tool, TextContent

# Local imports
from models import Platform, ReviewRequest
from webhook import WebhookHandler
from services import AIReviewer, DiffAnalyzer, CommentService
from adapters import GitHubAdapter, GitLabAdapter, BitbucketAdapter, AzureAdapter
from tools import ReviewTools

# Load environment variables
load_dotenv()

# Configure logging
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()
    ]
)
logger = structlog.get_logger()

# Load configuration
with open("config.yaml", "r") as f:
    config = yaml.safe_load(f)


class CodeReviewServer:
    """Main code review server"""
    
    def __init__(self):
        self.config = config
        self.webhook_handler = WebhookHandler()
        
        # Initialize AI reviewer
        ai_config = config['ai']
        self.ai_reviewer = AIReviewer(
            provider=ai_config['provider'],
            model=ai_config.get('model')
        )
        
        self.diff_analyzer = DiffAnalyzer()
        self.comment_service = CommentService()
        
        # Initialize platform adapters
        self.adapters = {}
        self._init_adapters()
        
        # MCP Tools
        self.review_tools = ReviewTools(self.ai_reviewer, self.diff_analyzer)
        
        logger.info("code_review_server_initialized")
    
    def _init_adapters(self):
        """Initialize enabled platform adapters"""
        platforms_config = self.config['platforms']
        
        if platforms_config.get('github', {}).get('enabled'):
            try:
                self.adapters[Platform.GITHUB] = GitHubAdapter()
            except Exception as e:
                logger.warning("github_adapter_init_failed", error=str(e))
        
        if platforms_config.get('gitlab', {}).get('enabled'):
            try:
                self.adapters[Platform.GITLAB] = GitLabAdapter()
            except Exception as e:
                logger.warning("gitlab_adapter_init_failed", error=str(e))
        
        if platforms_config.get('bitbucket', {}).get('enabled'):
            try:
                self.adapters[Platform.BITBUCKET] = BitbucketAdapter()
            except Exception as e:
                logger.warning("bitbucket_adapter_init_failed", error=str(e))
        
        if platforms_config.get('azure', {}).get('enabled'):
            try:
                self.adapters[Platform.AZURE] = AzureAdapter()
            except Exception as e:
                logger.warning("azure_adapter_init_failed", error=str(e))
    
    async def process_webhook(self, request: Request) -> dict:
        """
        Process incoming webhook from any platform
        
        Args:
            request: FastAPI request
            
        Returns:
            Response dict
        """
        # Parse webhook
        pr_data = await self.webhook_handler.handle(request)
        
        if not pr_data:
            return {"status": "ignored", "message": "Not a PR event or unsupported platform"}
        
        logger.info("processing_webhook", platform=pr_data.platform.value, pr_id=pr_data.pr_id)
        
        # Get platform adapter
        adapter = self.adapters.get(pr_data.platform)
        if not adapter:
            logger.error("no_adapter_available", platform=pr_data.platform.value)
            return {"status": "error", "message": "Platform adapter not available"}
        
        try:
            # Fetch actual diff
            diff = await adapter.fetch_diff(pr_data)
            if not diff:
                logger.warning("no_diff_fetched", pr_id=pr_data.pr_id)
                return {"status": "error", "message": "Failed to fetch diff"}
            
            pr_data.diff = diff
            
            # Analyze diff
            diff_info = self.diff_analyzer.parse_diff(diff)
            pr_data.files_changed = [f['path'] for f in diff_info['files']]
            
            # Perform AI review
            review_config = self.config['review']
            review_result = await self.ai_reviewer.review(
                diff=diff,
                files_changed=pr_data.files_changed,
                focus_areas=review_config.get('focus', [])
            )
            
            # Post comments based on strategy
            strategy = review_config.get('comment_strategy', 'both')
            
            if strategy in ['summary', 'both']:
                summary_comment = self.comment_service.format_summary_comment(review_result)
                await adapter.post_summary_comment(pr_data, summary_comment)
            
            if strategy in ['inline', 'both']:
                inline_comments = self.comment_service.format_inline_comments(review_result)
                if inline_comments:
                    await adapter.post_inline_comments(pr_data, inline_comments)
            
            # Update status
            if review_result.block_merge:
                await adapter.update_status(pr_data, "failure", "Critical issues found")
            elif review_result.score >= 8:
                await adapter.update_status(pr_data, "success", f"Code quality: {review_result.score}/10")
            else:
                await adapter.update_status(pr_data, "success", f"Review complete: {review_result.score}/10")
            
            logger.info(
                "review_completed",
                pr_id=pr_data.pr_id,
                score=review_result.score,
                issues=review_result.total_issues
            )
            
            return {
                "status": "success",
                "pr_id": pr_data.pr_id,
                "platform": pr_data.platform.value,
                "score": review_result.score,
                "issues": review_result.total_issues,
                "critical": review_result.critical_count
            }
            
        except Exception as e:
            logger.exception("webhook_processing_failed", error=str(e))
            return {"status": "error", "message": str(e)}


# Create server instance
review_server = CodeReviewServer()

# FastAPI app
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    logger.info("server_starting")
    yield
    logger.info("server_shutting_down")

app = FastAPI(
    title="MCP Code Review Server",
    description="AI-powered code review with platform integration",
    version="1.0.0",
    lifespan=lifespan
)


@app.get("/")
async def root():
    """Health check"""
    return {
        "name": "MCP Code Review Server",
        "version": "1.0.0",
        "status": "healthy",
        "platforms": list(review_server.adapters.keys())
    }


@app.post("/webhook")
async def webhook_endpoint(request: Request):
    """
    Universal webhook endpoint - automatically detects platform
    """
    try:
        result = await review_server.process_webhook(request)
        return JSONResponse(content=result)
    except Exception as e:
        logger.exception("webhook_error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/mcp/sse")
async def mcp_sse_endpoint(request: Request):
    """
    MCP Server-Sent Events endpoint for MCP clients
    """
    # Create MCP server
    mcp_server = Server("code-review-server")
    
    # Register MCP tools
    @mcp_server.list_tools()
    async def list_tools() -> list[Tool]:
        return review_server.review_tools.get_tools()
    
    @mcp_server.call_tool()
    async def call_tool(name: str, arguments: dict) -> list[TextContent]:
        result = await review_server.review_tools.execute_tool(name, arguments)
        return [TextContent(type="text", text=result)]
    
    # Create SSE transport
    async with SseServerTransport("/mcp/messages") as transport:
        await mcp_server.connect(transport)
        await transport.handle_sse(request)


if __name__ == "__main__":
    import uvicorn
    
    server_config = config['server']
    uvicorn.run(
        app,
        host=server_config.get('host', '0.0.0.0'),
        port=server_config.get('port', 8000),
        log_level="info"
    )

