# 🚀 Quick Start Guide

## 5-Minute Setup

### 1. Install Dependencies

```bash
cd python
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure API Keys

Create `.env` file:

```bash
# Choose AI provider
ANTHROPIC_API_KEY=sk-ant-xxx
# OR
OPENAI_API_KEY=sk-xxx

# Add platform token (at least one)
GITHUB_TOKEN=ghp_xxx
```

### 3. Run Server

```bash
python server.py
```

Server starts at `http://localhost:8000`

### 4. Test Health

```bash
curl http://localhost:8000/
```

Expected response:
```json
{
  "name": "MCP Code Review Server",
  "status": "healthy",
  "platforms": ["github"]
}
```

## 🔗 Connect to Pipeline

### Option 1: Bitbucket Pipelines

Add to `bitbucket-pipelines.yml`:

```yaml
pipelines:
  pull-requests:
    '**':
      - step:
          script:
            - |
              curl -X POST https://your-server.com/webhook \
                -H "Content-Type: application/json" \
                -d '{...webhook payload...}'
```

Set repository variables:
- `REVIEW_SERVER_URL`: Your server URL
- `REVIEW_SERVER_TOKEN`: Authentication token (optional)

### Option 2: GitHub Actions

Add `.github/workflows/review.yml`:

```yaml
name: Code Review
on:
  pull_request:
    types: [opened, synchronize]

jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: AI Review
        run: |
          curl -X POST ${{ secrets.REVIEW_SERVER_URL }}/webhook ...
```

Add secrets:
- `REVIEW_SERVER_URL`
- `REVIEW_SERVER_TOKEN`

## 🎯 Manual Review (Claude Desktop)

1. Install Claude Desktop
2. Configure MCP:

```json
{
  "mcpServers": {
    "code-review": {
      "command": "curl",
      "args": ["http://localhost:8000/mcp/sse"]
    }
  }
}
```

3. Use tools in Claude:
   - "Review this code..."
   - "Analyze security issues in..."
   - "Check this diff..."

## 🐳 Docker Deployment

```bash
# Build
docker build -t mcp-code-review .

# Run
docker run -d \
  -p 8000:8000 \
  -e ANTHROPIC_API_KEY=your_key \
  -e GITHUB_TOKEN=your_token \
  --name code-review \
  mcp-code-review
```

Or use docker-compose:

```bash
docker-compose up -d
```

## ✅ Verify Setup

### Test webhook:

```bash
curl -X POST http://localhost:8000/webhook \
  -H "Content-Type: application/json" \
  -H "X-GitHub-Event: pull_request" \
  -d @test-payload.json
```

### Check logs:

```bash
# Local
tail -f server.log

# Docker
docker logs -f code-review
```

## 🎨 Customize Reviews

Edit `config.yaml`:

```yaml
review:
  comment_strategy: "both"  # summary, inline, both
  report_levels:
    - critical
    - high
    - medium
  focus:
    - security      # Enable/disable
    - performance
    - bugs
```

## 🆘 Troubleshooting

### Server won't start

```bash
# Check Python version (3.11+)
python --version

# Verify dependencies
pip install -r requirements.txt

# Check config
python -c "import yaml; yaml.safe_load(open('config.yaml'))"
```

### No reviews posted

1. Check platform token is valid
2. Verify webhook payload format
3. Check server logs
4. Test platform API manually

### AI errors

```bash
# Test API key
python -c "from anthropic import Anthropic; Anthropic(api_key='your_key').messages.create(...)"

# Check quota/limits
```

## 📚 Next Steps

- [ ] Set up production deployment
- [ ] Configure HTTPS
- [ ] Add monitoring
- [ ] Customize review rules
- [ ] Integrate with CI/CD
- [ ] Test with real PRs

## 🔗 Resources

- [Full README](README.md)
- [Configuration Guide](config.yaml)
- [Pipeline Examples](examples/)
- [API Documentation](#)

---

Need help? Open an issue or check the FAQ!

