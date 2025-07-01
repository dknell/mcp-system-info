# System Information MCP Server

## Overview

A Model Context Protocol (MCP) server that exposes system information and metrics through a standardized interface. This server provides real-time access to CPU usage, memory statistics, disk information, network status, and running processes.

## Architecture

### Core Components

**MCP Server Implementation**
- Built using `mcp` Python library
- Async/await pattern for non-blocking operations
- Error handling with proper MCP error types
- Structured logging for debugging

**System Metrics Provider**
- Utilizes `psutil` library for cross-platform system information
- Caches frequently accessed data to reduce system calls
- Implements refresh intervals for real-time metrics

**Data Serialization**
- JSON output format for all responses
- Consistent data structures across all tools
- Human-readable formatting with units

## Tools Specification

### `get_cpu_info`
**Description**: Retrieves CPU usage and information
**Parameters**: 
- `interval` (optional, float): Measurement interval in seconds (default: 1.0)
- `per_cpu` (optional, bool): Include per-CPU core breakdown (default: false)

**Response Format**:
```json
{
  "cpu_percent": 45.2,
  "cpu_count_logical": 8,
  "cpu_count_physical": 4,
  "cpu_freq_current": 2400.0,
  "cpu_freq_max": 3400.0,
  "load_average": [1.2, 1.5, 1.8],
  "per_cpu_percent": [42.1, 48.3, 44.7, 46.9, 43.2, 47.1, 45.8, 44.6]
}
```

### `get_memory_info`
**Description**: Retrieves memory usage statistics
**Parameters**: None

**Response Format**:
```json
{
  "virtual_memory": {
    "total": 17179869184,
    "available": 8589934592,
    "used": 8589934592,
    "percent": 50.0,
    "total_gb": 16.0,
    "available_gb": 8.0,
    "used_gb": 8.0
  },
  "swap_memory": {
    "total": 2147483648,
    "used": 0,
    "free": 2147483648,
    "percent": 0.0,
    "total_gb": 2.0
  }
}
```

### `get_disk_info`
**Description**: Retrieves disk usage information
**Parameters**:
- `path` (optional, string): Specific path to check (default: all mounted disks)

**Response Format**:
```json
{
  "disks": [
    {
      "mountpoint": "/",
      "device": "/dev/disk1s1",
      "fstype": "apfs",
      "total": 494384795648,
      "used": 123456789012,
      "free": 370927006636,
      "percent": 25.0,
      "total_gb": 460.4,
      "used_gb": 115.0,
      "free_gb": 345.4
    }
  ]
}
```

### `get_network_info`
**Description**: Retrieves network interface information and statistics
**Parameters**: None

**Response Format**:
```json
{
  "interfaces": [
    {
      "name": "en0",
      "addresses": [
        {"family": "AF_INET", "address": "192.168.1.100", "netmask": "255.255.255.0"},
        {"family": "AF_INET6", "address": "fe80::1%en0", "netmask": "ffff:ffff:ffff:ffff::"}
      ],
      "is_up": true,
      "speed": 1000,
      "mtu": 1500
    }
  ],
  "stats": {
    "bytes_sent": 1234567890,
    "bytes_recv": 9876543210,
    "packets_sent": 123456,
    "packets_recv": 654321,
    "errin": 0,
    "errout": 0,
    "dropin": 0,
    "dropout": 0
  }
}
```

### `get_process_list`
**Description**: Retrieves list of running processes
**Parameters**:
- `limit` (optional, int): Maximum number of processes to return (default: 50)
- `sort_by` (optional, string): Sort criteria - cpu, memory, name, pid (default: cpu)
- `filter_name` (optional, string): Filter processes by name pattern

**Response Format**:
```json
{
  "processes": [
    {
      "pid": 1234,
      "name": "python3",
      "username": "user",
      "status": "running",
      "cpu_percent": 15.2,
      "memory_percent": 2.1,
      "memory_rss": 134217728,
      "memory_rss_mb": 128.0,
      "create_time": "2024-01-15T10:30:00",
      "cmdline": ["python3", "app.py"]
    }
  ],
  "total_processes": 156
}
```

### `get_system_uptime`
**Description**: Retrieves system uptime and boot information
**Parameters**: None

**Response Format**:
```json
{
  "boot_time": "2024-01-15T08:00:00Z",
  "uptime_seconds": 86400,
  "uptime_formatted": "1 day, 0 hours, 0 minutes"
}
```

### `get_temperature_info`
**Description**: Retrieves system temperature sensors (when available)
**Parameters**: None

**Response Format**:
```json
{
  "temperatures": [
    {
      "name": "CPU Package",
      "current": 45.0,
      "high": 100.0,
      "critical": 105.0,
      "unit": "celsius"
    }
  ],
  "fans": [
    {
      "name": "CPU Fan",
      "current_speed": 1200,
      "unit": "rpm"
    }
  ]
}
```

## Resources Specification

### `/system/overview`
**Description**: A comprehensive system overview resource
**MIME Type**: `application/json`
**Content**: Aggregated system information including CPU, memory, disk, and network summaries

### `/system/processes`
**Description**: Current process list resource
**MIME Type**: `application/json`
**Content**: Real-time process information with basic filtering

## Error Handling

### Standard Error Types
- `InvalidArgument`: Invalid parameter values or types
- `ResourceNotFound`: Requested system resource not available
- `InternalError`: System call failures or permission issues
- `NotSupported`: Feature not available on current platform

### Error Response Format
```json
{
  "error": {
    "code": "InvalidArgument",
    "message": "Interval must be a positive number",
    "details": {
      "parameter": "interval",
      "provided_value": -1.0
    }
  }
}
```

## Project Setup

### Prerequisites
- Python 3.10+ (Python 3.12+ recommended)
- [uv](https://docs.astral.sh/uv/) package manager

### Initialize Project
```bash
# Create new uv-managed project
uv init system-info-mcp
cd system-info-mcp

# Add dependencies
uv add mcp psutil

# Optional: Add development dependencies
uv add --dev pytest pytest-asyncio black ruff mypy
```

### Project Structure
```
system-info-mcp/
├── src/
│   └── system_info_mcp/
│       ├── __init__.py
│       ├── server.py          # Main server implementation
│       ├── tools.py           # Tool implementations
│       ├── resources.py       # Resource handlers
│       └── utils.py           # Utility functions
├── tests/
│   ├── __init__.py
│   ├── test_tools.py
│   └── test_resources.py
├── pyproject.toml             # Project configuration
├── README.md
└── .gitignore
```

## Implementation Details

### Dependencies (pyproject.toml)
```toml
[project]
name = "system-info-mcp"
version = "0.1.0"
description = "System Information MCP Server"
authors = [
    {name = "Your Name", email = "your.email@example.com"}
]
readme = "README.md"
requires-python = ">=3.10"
dependencies = [
    "mcp>=1.0.0",
    "psutil>=5.9.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-asyncio>=0.21.0",
    "black>=23.0.0",
    "ruff>=0.1.0",
    "mypy>=1.0.0",
]

[project.scripts]
system-info-mcp = "system_info_mcp.server:main"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.ruff]
line-length = 88
target-version = "py310"

[tool.black]
line-length = 88
target-version = ["py310"]

[tool.mypy]
python_version = "3.10"
strict = true
```

### Performance Considerations
- Implement caching for expensive operations (process lists, disk info)
- Use configurable refresh intervals to balance accuracy vs performance
- Lazy loading for temperature/sensor data that may not be available
- Async/await for all I/O operations

### Cross-Platform Support
- Handle platform-specific differences in psutil
- Graceful degradation when features unavailable (temperatures on some systems)
- Consistent JSON schema regardless of underlying OS differences

### Security Considerations
- No sensitive process information exposure (command line arguments filtered)
- Read-only operations only
- No system modification capabilities
- Input validation for all parameters

## Configuration

### Environment Variables
- `SYSINFO_CACHE_TTL`: Cache time-to-live in seconds (default: 5)
- `SYSINFO_MAX_PROCESSES`: Maximum processes to return (default: 100)
- `SYSINFO_LOG_LEVEL`: Logging level (default: INFO)

### Server Configuration
```python
# src/system_info_mcp/config.py
import os
from dataclasses import dataclass
from typing import List

@dataclass
class ServerConfig:
    """Server configuration with environment variable support."""
    name: str = "system-info-server"
    version: str = "1.0.0"
    description: str = "System information MCP server"
    cache_ttl: int = int(os.getenv("SYSINFO_CACHE_TTL", "5"))
    max_processes: int = int(os.getenv("SYSINFO_MAX_PROCESSES", "100"))
    enable_temperatures: bool = os.getenv("SYSINFO_ENABLE_TEMP", "true").lower() == "true"
    log_level: str = os.getenv("SYSINFO_LOG_LEVEL", "INFO")

# Example usage in server.py
from mcp.server.fastmcp import FastMCP
from .config import ServerConfig

config = ServerConfig()
app = FastMCP(
    config.name,
    dependencies=["psutil>=5.9.0"]
)
```

## Usage Examples

### Basic CPU Monitoring
```python
# Tool call
{
    "name": "get_cpu_info",
    "arguments": {
        "interval": 2.0,
        "per_cpu": true
    }
}
```

### Process Monitoring
```python
# Tool call
{
    "name": "get_process_list",
    "arguments": {
        "limit": 10,
        "sort_by": "memory",
        "filter_name": "python"
    }
}
```

### Resource Access
```python
# Resource request
{
    "uri": "system://overview"
}
```

## Testing Strategy

### Unit Tests
- Mock psutil calls for consistent testing
- Test error handling for invalid parameters
- Validate JSON schema compliance
- Cross-platform compatibility tests

### Integration Tests
- Full MCP protocol compliance
- Real system metrics validation
- Performance benchmarking
- Memory leak detection

### Test Coverage Requirements
- Minimum 90% code coverage
- All error paths tested
- Platform-specific code branches covered
- Performance regression tests

## Development Workflow

### Running the Server
```bash
# Development mode
uv run src/system_info_mcp/server.py

# Or using the installed script
uv run system-info-mcp

# With environment variables
SYSINFO_CACHE_TTL=10 uv run system-info-mcp
```

### Testing
```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=system_info_mcp

# Run specific test file
uv run pytest tests/test_tools.py
```

### Code Quality
```bash
# Format code
uv run black src/ tests/

# Lint code
uv run ruff check src/ tests/

# Type checking
uv run mypy src/
```

## Deployment

### Local Installation
```bash
# Install in development mode
uv pip install -e .

# Install from PyPI (when published)
uv add system-info-mcp
```

### Docker Support
```dockerfile
FROM python:3.12-slim

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

# Set working directory
WORKDIR /app

# Copy project files
COPY pyproject.toml uv.lock ./
COPY src/ ./src/

# Install dependencies
RUN uv sync --frozen

# Run server
CMD ["uv", "run", "system-info-mcp"]
```

### MCP Client Configuration

#### Claude Desktop
```json
{
  "mcpServers": {
    "system-info": {
      "command": "uv",
      "args": [
        "--directory", 
        "/path/to/system-info-mcp", 
        "run", 
        "system-info-mcp"
      ],
      "env": {
        "SYSINFO_CACHE_TTL": "10"
      }
    }
  }
}
```

#### Development Configuration
```json
{
  "mcpServers": {
    "system-info-dev": {
      "command": "uv",
      "args": [
        "--directory",
        "/path/to/system-info-mcp",
        "run",
        "src/system_info_mcp/server.py"
      ],
      "env": {
        "SYSINFO_LOG_LEVEL": "DEBUG"
      }
    }
  }
}
```

#### Global Installation (uvx)
```bash
# Install globally with uvx
uvx install system-info-mcp

# Claude Desktop config for global install
{
  "mcpServers": {
    "system-info": {
      "command": "uvx",
      "args": ["system-info-mcp"]
    }
  }
}
```