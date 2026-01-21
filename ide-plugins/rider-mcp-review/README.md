# MCP AI Code Review - Rider Plugin

🤖 AI-powered code review directly in JetBrains Rider.

## Features

- **Review Current File** (`Ctrl+Alt+R`) - Review changes in the current file
- **Review Selection** (`Ctrl+Alt+Shift+R`) - Review selected code
- **Review Staged Changes** - Review all staged git changes
- **Review Uncommitted Changes** - Review all uncommitted changes
- **Tool Window** - View detailed review results with syntax highlighting
- **Inline Highlights** - See issues directly in the editor

## Installation

### From Plugin Marketplace
1. Open Rider → Settings → Plugins
2. Search for "MCP AI Code Review"
3. Install and restart

### Manual Installation
1. Build the plugin: `./gradlew buildPlugin`
2. The plugin zip will be in `build/distributions/`
3. Rider → Settings → Plugins → ⚙️ → Install Plugin from Disk

## Configuration

1. Go to **Settings → Tools → MCP Code Review**
2. Set your MCP Server URL (default: `http://localhost:8000`)
3. Configure options:
   - Auto-review on commit
   - Show inline highlights
   - Minimum severity level
   - Timeout

## Usage

### Review Current File
1. Open a file with changes
2. Press `Ctrl+Alt+R` or use **Tools → MCP Review → Review Current File**
3. View results in the MCP Review tool window

### Review Selection
1. Select code in the editor
2. Right-click → **Review Selection** or press `Ctrl+Alt+Shift+R`
3. View results in the MCP Review tool window

### Review Git Changes
1. Use **Tools → MCP Review → Review Staged Changes** for staged changes
2. Use **Tools → MCP Review → Review Uncommitted Changes** for all changes

## Building from Source

```bash
# Clone the repository
git clone https://github.com/your-repo/mcp-server.git
cd mcp-server/ide-plugins/rider-mcp-review

# Build the plugin
./gradlew buildPlugin

# Run in development mode
./gradlew runIde
```

## Requirements

- JetBrains Rider 2023.3 or later
- MCP Code Review Server running
- Git repository

## Server Setup

Make sure your MCP server is running and accessible:

```bash
cd mcp-server
python server.py
```

The plugin will connect to `http://localhost:8000` by default.

## License

MIT License

