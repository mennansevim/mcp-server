# 🤖 MCP Code Review Server

Platform-agnostic AI-powered code review server with webhook support and MCP integration.

## ✨ Features

- 🔌 **Platform Agnostic**: Single webhook endpoint for GitHub, GitLab, Bitbucket, Azure DevOps
- 🤖 **AI-Powered**: Uses Groq (Llama 3.3), Claude, or GPT-4 for intelligent code review
- 💬 **Multiple Comment Styles**: Summary comments, inline comments, or both
- 🎯 **Focused Analysis**: Security, performance, bugs, code quality
- 🔧 **MCP Tools**: Manual code review via Claude Desktop or other MCP clients
- 🚀 **Easy Integration**: Simple pipeline configuration

## 🏗️ Architecture

```
Pipeline Webhook → MCP Server → Platform Detection → AI Review → Post Comments
```

## 📦 Installation

### 1. Clone and Setup

```bash
cd python
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configuration

Copy `.env.example` to `.env` and configure:

```bash
# AI Provider (choose one)
GROQ_API_KEY=your_key
# or
ANTHROPIC_API_KEY=your_key
# or
OPENAI_API_KEY=your_key

# Platform Tokens
GITHUB_TOKEN=your_github_token
GITLAB_TOKEN=your_gitlab_token
BITBUCKET_USERNAME=your_username
BITBUCKET_APP_PASSWORD=your_password
AZURE_DEVOPS_PAT=your_azure_pat
AZURE_DEVOPS_ORG=https://dev.azure.com/your-org
```

Edit `config.yaml` for review preferences:

```yaml
ai:
  provider: "groq"  # or "anthropic" or "openai"
  model: "llama-3.3-70b-versatile"  # Groq models
  # model: "claude-3-5-sonnet-20241022"  # Anthropic
  # model: "gpt-4-turbo-preview"  # OpenAI

review:
  comment_strategy: "both"  # summary, inline, both
  report_levels:
    - critical
    - high
    - medium
  block_on_critical: true
```

### 3. Run Server

```bash
python server.py
```

Server runs on `http://localhost:8000`

## 🔧 Pipeline Integration

### Bitbucket Pipelines

See `examples/bitbucket-pipelines.yml`

```yaml
pipelines:
  pull-requests:
    '**':
      - step:
          script:
            - curl -X POST $REVIEW_SERVER_URL/webhook ...
```

### GitHub Actions

See `examples/github-actions.yml`

```yaml
- name: Trigger AI Review
  run: |
    curl -X POST ${{ secrets.REVIEW_SERVER_URL }}/webhook ...
```

### GitLab CI/CD

See `examples/gitlab-ci.yml`

```yaml
ai-code-review:
  script:
    - curl -X POST $REVIEW_SERVER_URL/webhook ...
```

### Azure Pipelines

See `examples/azure-pipelines.yml`

```yaml
- script: |
    curl -X POST $(REVIEW_SERVER_URL)/webhook ...
```

## 🎯 MCP Tools (Manual Review)

Use from Claude Desktop or any MCP client:

### 1. Review Code

```json
{
  "tool": "review_code",
  "arguments": {
    "code": "def login(username, password):\n    query = f\"SELECT * FROM users WHERE username='{username}'\"",
    "focus": ["security", "bugs"]
  }
}
```

### 2. Analyze Diff

```json
{
  "tool": "analyze_diff",
  "arguments": {
    "diff": "--- a/file.py\n+++ b/file.py\n..."
  }
}
```

### 3. Security Scan

```json
{
  "tool": "security_scan",
  "arguments": {
    "code": "your_code_here",
    "language": "python"
  }
}
```

## 📊 Review Output

### Summary Comment Example

```markdown
## 🤖 AI Code Review

**Score:** 7/10 ⚠️

### 📝 Summary
Good code structure but found some security concerns...

### 📊 Issues Found
- Total: **5**
- 🔴 Critical: **1**
- 🟠 High: **2**
- 🟡 Medium: **2**

### ⚠️ Important Issues

#### 🔴 SQL Injection Vulnerability
**Severity:** CRITICAL
**Location:** `auth.py` (Line 42)

Using string concatenation for SQL queries...

**Suggestion:**
> Use parameterized queries...
```

### Inline Comments

Comments posted directly on the problematic code lines.

## 🔒 Security

- Webhook signature verification
- API token authentication
- Environment-based secrets
- No sensitive data logging

## 🚀 Deployment

### Docker

```bash
docker build -t mcp-code-review .
docker run -p 8000:8000 --env-file .env mcp-code-review
```

### Production

- Use reverse proxy (nginx, traefik)
- Enable HTTPS
- Set up logging and monitoring
- Configure rate limiting

## 🛠️ Development

```bash
# Install dev dependencies
pip install -r requirements.txt

# Run tests
pytest

# Format code
black .
```

## 📝 API Endpoints

- `GET /` - Health check
- `POST /webhook` - Universal webhook endpoint
- `GET /mcp/sse` - MCP Server-Sent Events endpoint

## 🤝 Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Submit a pull request

## 📄 License

MIT License

## 🆘 Support

For issues and questions:
- Open an issue on GitHub
- Check documentation
- Review examples

---

**Made with ❤️ for better code reviews**

