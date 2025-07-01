# System Information MCP Server

A Model Context Protocol (MCP) server that provides real-time system information and metrics. This server exposes CPU usage, memory statistics, disk information, network status, and running processes through a standardized MCP interface.

## Features

### 🛠️ Tools Available

- **`get_cpu_info`** - Retrieve CPU usage, core counts, frequency, and load average
- **`get_memory_info`** - Get virtual and swap memory statistics
- **`get_disk_info`** - Disk usage information for all mounts or specific paths
- **`get_network_info`** - Network interface information and I/O statistics
- **`get_process_list`** - Running processes with sorting and filtering options
- **`get_system_uptime`** - System boot time and uptime information
- **`get_temperature_info`** - Temperature sensors and fan speeds (when available)

### 📚 Resources Available

- **`system://overview`** - Comprehensive system overview with all metrics
- **`system://processes`** - Current process list resource

### ⭐ Key Features

- **Real-time metrics** with configurable caching
- **Cross-platform support** (Windows, macOS, Linux)
- **Security-focused** with sensitive data filtering
- **Performance optimized** with intelligent caching
- **Comprehensive error handling**
- **Environment variable configuration**

## Installation

### Using uvx (Recommended)

The easiest way to install and use this MCP server is with [uvx](https://docs.astral.sh/uv/guides/tools/):

```bash
uvx install mcp-system-info
```

Then configure it in your MCP client (like Claude Desktop):

```json
{
  "mcpServers": {
    "system-info": {
      "command": "uvx",
      "args": ["mcp-system-info"]
    }
  }
}
```

### Development Installation

For local development:

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd mcp-system-info
   ```

2. **Install dependencies:**
   ```bash
   uv sync
   ```

3. **Run the server:**
   ```bash
   uv run mcp-system-info
   ```

## Development

### Project Structure

```
mcp-system-info/
├── src/
│   └── system_info_mcp/
│       ├── __init__.py
│       ├── server.py          # Main FastMCP server
│       ├── tools.py           # Tool implementations
│       ├── resources.py       # Resource handlers
│       ├── config.py          # Configuration management
│       └── utils.py           # Utility functions
├── tests/                     # Comprehensive test suite
├── pyproject.toml            # Project configuration
└── README.md
```

### Development Setup

1. **Install development dependencies:**
   ```bash
   uv sync --dev
   ```

2. **Run tests:**
   ```bash
   uv run pytest
   ```

3. **Run tests with coverage:**
   ```bash
   uv run pytest --cov=system_info_mcp --cov-report=term-missing
   ```

4. **Format code:**
   ```bash
   uv run black src/ tests/
   ```

5. **Lint code:**
   ```bash
   uv run ruff check src/ tests/
   ```

6. **Type checking:**
   ```bash
   uv run mypy src/
   ```

### Building and Publishing

#### Build the Package

```bash
# Build distribution files
uv build
```

This creates distribution files in the `dist/` directory:
- `mcp_system_info-*.whl` (wheel file)
- `mcp_system_info-*.tar.gz` (source distribution)

#### Local Testing with uvx

Test the package locally before publishing:

```bash
# Test running the command directly from wheel file
uvx --from ./dist/mcp_system_info-*.whl mcp-system-info

# Test with environment variables
SYSINFO_LOG_LEVEL=DEBUG uvx --from ./dist/mcp_system_info-*.whl mcp-system-info
```

#### Publishing to PyPI

```bash
# Publish to PyPI (requires PyPI account and token)
uv publish

# Or publish to TestPyPI first
uv publish --repository testpypi
```

**Note:** You'll need to:
1. Create a PyPI account at https://pypi.org
2. Generate an API token in your account settings
3. Configure uv with your credentials or use environment variables

### Environment Configuration

The server supports configuration through environment variables:

#### Core Settings
- `SYSINFO_CACHE_TTL` - Cache time-to-live in seconds (default: 5)
- `SYSINFO_MAX_PROCESSES` - Maximum processes to return (default: 100)
- `SYSINFO_ENABLE_TEMP` - Enable temperature sensors (default: true)
- `SYSINFO_LOG_LEVEL` - Logging level (default: INFO)

#### Transport Configuration
- `SYSINFO_TRANSPORT` - Transport protocol: `stdio`, `sse`, or `streamable-http` (default: stdio)
- `SYSINFO_HOST` - Host to bind to for HTTP transports (default: localhost)
- `SYSINFO_PORT` - Port to bind to for HTTP transports (default: 8001)
- `SYSINFO_MOUNT_PATH` - Mount path for SSE transport (default: /mcp)

#### Transport Modes

**1. STDIO (Default)**
```bash
# Uses standard input/output - no network port
uv run mcp-system-info
```

**2. SSE (Server-Sent Events)**
```bash
# HTTP server with real-time streaming
SYSINFO_TRANSPORT=sse SYSINFO_PORT=8001 uv run mcp-system-info
# Server will be available at http://localhost:8001/mcp
```

**3. Streamable HTTP**
```bash  
# HTTP server with request/response
SYSINFO_TRANSPORT=streamable-http SYSINFO_PORT=9000 uv run mcp-system-info
```

#### Complete Example:
```bash
SYSINFO_TRANSPORT=sse \
SYSINFO_HOST=0.0.0.0 \
SYSINFO_PORT=8001 \
SYSINFO_CACHE_TTL=10 \
SYSINFO_LOG_LEVEL=DEBUG \
uv run mcp-system-info
```

## Usage Examples

### Tool Usage

#### Get CPU Information
```python
# Basic CPU info
{
  "name": "get_cpu_info_tool",
  "arguments": {
    "interval": 1.0,
    "per_cpu": false
  }
}
```

#### Get Process List
```python
# Top 10 processes by memory usage
{
  "name": "get_process_list_tool", 
  "arguments": {
    "limit": 10,
    "sort_by": "memory",
    "filter_name": "python"
  }
}
```

#### Get Disk Information
```python
# All disk usage
{
  "name": "get_disk_info_tool",
  "arguments": {}
}

# Specific path
{
  "name": "get_disk_info_tool",
  "arguments": {
    "path": "/home"
  }
}
```

### Resource Usage

#### System Overview
```python
# Request comprehensive system overview
{
  "uri": "system://overview"
}
```

#### Process List Resource
```python
# Get top processes resource
{
  "uri": "system://processes" 
}
```

## Integration with Claude Desktop

### Adding to Claude Desktop

1. **Locate your Claude Desktop config file:**
   - **macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
   - **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

2. **Add the MCP server configuration:**

#### Using uvx (Recommended)
```json
{
  "mcpServers": {
    "system-info": {
      "command": "uvx",
      "args": ["mcp-system-info"],
      "env": {
        "SYSINFO_CACHE_TTL": "10",
        "SYSINFO_LOG_LEVEL": "INFO"
      }
    }
  }
}
```

#### For Local Development
```json
{
  "mcpServers": {
    "system-info": {
      "command": "uv",
      "args": [
        "--directory", 
        "/path/to/mcp-system-info", 
        "run", 
        "mcp-system-info"
      ],
      "env": {
        "SYSINFO_TRANSPORT": "stdio",
        "SYSINFO_CACHE_TTL": "10",
        "SYSINFO_LOG_LEVEL": "INFO"
      }
    }
  }
}
```

#### For HTTP Transport (SSE)
```json
{
  "mcpServers": {
    "system-info-http": {
      "command": "uvx",
      "args": ["mcp-system-info"],
      "env": {
        "SYSINFO_TRANSPORT": "sse",
        "SYSINFO_HOST": "localhost",
        "SYSINFO_PORT": "8001",
        "SYSINFO_MOUNT_PATH": "/mcp"
      }
    }
  }
}
```

3. **Restart Claude Desktop** to load the new server.

### Using with Claude

Once configured, you can ask Claude to:

- "What's my current CPU usage?"
- "Show me the top 10 processes using the most memory"
- "How much disk space is available?"
- "What's my system uptime?"
- "Give me a complete system overview"

## Testing

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with verbose output
uv run pytest -v

# Run specific test file
uv run pytest tests/test_tools.py

# Run with coverage report
uv run pytest --cov=system_info_mcp --cov-report=html
```

### Test Structure

- `tests/test_config.py` - Configuration validation tests
- `tests/test_tools.py` - Tool implementation tests  
- `tests/test_resources.py` - Resource handler tests
- `tests/test_utils.py` - Utility function tests

All tests use mocked dependencies for consistent, fast execution across different environments.

## Performance Considerations

- **Caching:** Intelligent caching reduces system calls and improves response times
- **Configurable intervals:** Adjust cache TTL based on your needs
- **Lazy loading:** Temperature sensors and other optional features load only when needed
- **Async support:** Built on FastMCP for efficient async operations

## Security Features

- **Read-only operations:** No system modification capabilities
- **Sensitive data filtering:** Command-line arguments are filtered for passwords, tokens, etc.
- **Input validation:** All parameters are validated before processing
- **Error isolation:** Failures in one tool don't affect others

## Platform Support

- **macOS** - Full support including temperature sensors on supported hardware
- **Linux** - Full support with hardware-dependent sensor availability  
- **Windows** - Full support with platform-specific optimizations

## Troubleshooting

### Common Issues

1. **Permission errors:** Some system information may require elevated privileges
2. **Missing sensors:** Temperature/fan data availability varies by hardware
3. **Performance impact:** Reduce cache TTL or limit process counts for better performance

### Debug Mode

Enable debug logging for troubleshooting:
```bash
SYSINFO_LOG_LEVEL=DEBUG uv run mcp-system-info
```

### Verifying Installation

Test that tools work correctly:
```bash
uv run python -c "from system_info_mcp.tools import get_cpu_info; print(get_cpu_info())"
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes with tests
4. Run the full test suite
5. Submit a pull request

### Code Standards

- Follow PEP 8 style guidelines
- Add type hints to all functions
- Write tests for new functionality
- Update documentation as needed

## License

[Add your license information here]

## Support

[Add support information here]