"""
MCP Code Review Server
Platform-agnostic AI-powered code review via webhooks and MCP tools
"""
import os
import yaml
import structlog
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
        print("\n" + "="*80)
        print("🔔 WEBHOOK RECEIVED")
        print("="*80)
        
        # Parse webhook
        pr_data = await self.webhook_handler.handle(request)
        
        if not pr_data:
            print("⚠️  Ignored: Not a PR event or unsupported platform")
            print("="*80 + "\n")
            return {"status": "ignored", "message": "Not a PR event or unsupported platform"}
        
        print(f"📦 Platform: {pr_data.platform.value.upper()}")
        print(f"🔗 PR #{pr_data.pr_id}: {pr_data.title}")
        print(f"👤 Author: {pr_data.author}")
        print(f"🌿 {pr_data.source_branch} → {pr_data.target_branch}")
        print("-"*80)
        
        logger.info("processing_webhook", platform=pr_data.platform.value, pr_id=pr_data.pr_id)
        
        # Get platform adapter
        adapter = self.adapters.get(pr_data.platform)
        if not adapter:
            print(f"❌ ERROR: No adapter available for {pr_data.platform.value}")
            print("="*80 + "\n")
            logger.error("no_adapter_available", platform=pr_data.platform.value)
            return {"status": "error", "message": "Platform adapter not available"}
        
        try:
            # Fetch actual diff
            print("📥 Step 1/5: Fetching diff from platform...")
            diff = await adapter.fetch_diff(pr_data)
            if not diff:
                print("❌ Failed to fetch diff")
                print("="*80 + "\n")
                logger.warning("no_diff_fetched", pr_id=pr_data.pr_id)
                return {"status": "error", "message": "Failed to fetch diff"}
            print(f"✅ Diff fetched successfully ({len(diff)} bytes)")
            print()
            
            pr_data.diff = diff
            
            # Analyze diff
            print("🔍 Step 2/5: Analyzing diff...")
            diff_info = self.diff_analyzer.parse_diff(diff)
            pr_data.files_changed = [f['path'] for f in diff_info['files']]
            print(f"✅ Found {len(pr_data.files_changed)} changed file(s):")
            for file in pr_data.files_changed[:5]:  # Show first 5
                print(f"   📄 {file}")
            if len(pr_data.files_changed) > 5:
                print(f"   ... and {len(pr_data.files_changed) - 5} more")
            print()
            
            # Perform AI review
            print("🤖 Step 3/5: Starting AI code review...")
            review_config = self.config['review']
            print(f"   Provider: {self.config['ai']['provider'].upper()}")
            print(f"   Model: {self.config['ai']['model']}")
            print(f"   Focus areas: {', '.join(review_config.get('focus', []))}")
            print()
            
            review_result = await self.ai_reviewer.review(
                diff=diff,
                files_changed=pr_data.files_changed,
                focus_areas=review_config.get('focus', [])
            )
            
            print(f"✅ AI Review completed!")
            print(f"   Score: {review_result.score}/10")
            print(f"   Issues: {review_result.total_issues} total")
            if review_result.critical_count > 0:
                print(f"   🔴 Critical: {review_result.critical_count}")
            if review_result.high_count > 0:
                print(f"   🟠 High: {review_result.high_count}")
            if review_result.medium_count > 0:
                print(f"   🟡 Medium: {review_result.medium_count}")
            print()
            
            # Post comments based on strategy
            print("💬 Step 4/5: Posting review comments...")
            strategy = review_config.get('comment_strategy', 'both')
            print(f"   Strategy: {strategy}")
            
            # Check if detailed table should be shown for this branch
            detailed_branches = review_config.get('detailed_analysis_branches', [])
            show_detailed_table = pr_data.target_branch in detailed_branches
            
            if show_detailed_table:
                print(f"   📊 Detailed analysis table enabled for target branch: {pr_data.target_branch}")
            
            if strategy in ['summary', 'both']:
                print("   📝 Posting summary comment...")
                summary_comment = self.comment_service.format_summary_comment(
                    review_result, 
                    show_detailed_table=show_detailed_table
                )
                await adapter.post_summary_comment(pr_data, summary_comment)
                print("   ✅ Summary comment posted")
            
            if strategy in ['inline', 'both']:
                inline_comments = self.comment_service.format_inline_comments(review_result)
                if inline_comments:
                    print(f"   💭 Posting {len(inline_comments)} inline comment(s)...")
                    await adapter.post_inline_comments(pr_data, inline_comments)
                    print(f"   ✅ Inline comments posted")
            print()
            
            # Update status
            print("📊 Step 5/5: Updating PR status...")
            if review_result.block_merge:
                status_msg = "Critical issues found - merge blocked"
                print(f"   ❌ Status: FAILURE")
                print(f"   Message: {status_msg}")
                await adapter.update_status(pr_data, "failure", status_msg)
            elif review_result.score >= 8:
                status_msg = f"Code quality: {review_result.score}/10"
                print(f"   ✅ Status: SUCCESS")
                print(f"   Message: {status_msg}")
                await adapter.update_status(pr_data, "success", status_msg)
            else:
                status_msg = f"Review complete: {review_result.score}/10"
                print(f"   ✅ Status: SUCCESS")
                print(f"   Message: {status_msg}")
                await adapter.update_status(pr_data, "success", status_msg)
            print()
            
            logger.info(
                "review_completed",
                pr_id=pr_data.pr_id,
                score=review_result.score,
                issues=review_result.total_issues
            )
            
            print("🎉 REVIEW COMPLETED SUCCESSFULLY")
            print(f"   PR: #{pr_data.pr_id}")
            print(f"   Score: {review_result.score}/10")
            print(f"   Issues: {review_result.total_issues}")
            print(f"   Status: {'BLOCKED' if review_result.block_merge else 'APPROVED' if review_result.score >= 8 else 'REVIEW NEEDED'}")
            print("="*80 + "\n")
            
            return {
                "status": "success",
                "pr_id": pr_data.pr_id,
                "platform": pr_data.platform.value,
                "score": review_result.score,
                "issues": review_result.total_issues,
                "critical": review_result.critical_count
            }
            
        except Exception as e:
            print(f"❌ ERROR during review process:")
            print(f"   {str(e)}")
            print("="*80 + "\n")
            logger.exception("webhook_processing_failed", error=str(e))
            return {"status": "error", "message": str(e)}


# Create server instance
review_server = CodeReviewServer()

# FastAPI app
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    print("\n" + "="*80)
    print("🚀 MCP CODE REVIEW SERVER STARTING")
    print("="*80)
    print(f"📊 Version: 1.0.0")
    print(f"🤖 AI Provider: {config['ai']['provider'].upper()}")
    print(f"🧠 Model: {config['ai']['model']}")
    print(f"🔌 Platforms: {', '.join([p.value for p in review_server.adapters.keys()])}")
    print(f"💬 Comment Strategy: {config['review']['comment_strategy']}")
    print(f"🔍 Focus Areas: {', '.join(config['review']['focus'])}")
    print("="*80)
    print("✅ Server ready to receive webhooks!")
    print("="*80 + "\n")
    logger.info("server_starting")
    yield
    print("\n" + "="*80)
    print("🛑 SERVER SHUTTING DOWN")
    print("="*80 + "\n")
    logger.info("server_shutting_down")

app = FastAPI(
    title="MCP Code Review Server By Mennano",
    description="AI-powered code review with platform integration",
    version="1.0.0",
    lifespan=lifespan
)


@app.get("/")
async def root():
    """Health check"""
    return {
        "name": "MCP Code Review Server By Mennano",
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
        print("\n" + "="*80)
        print("❌ WEBHOOK ERROR")
        print("="*80)
        print(f"Error: {str(e)}")
        print("="*80 + "\n")
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

