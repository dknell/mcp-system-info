"""Main server implementation using FastMCP."""

import logging
from typing import Any, Dict, Optional

from mcp.server.fastmcp import FastMCP

from .config import config
from .tools import (
    get_cpu_info,
    get_memory_info,
    get_disk_info,
    get_network_info,
    get_process_list,
    get_system_uptime,
    get_temperature_info,
)
from .resources import RESOURCE_HANDLERS
from .utils import logger

# Initialize FastMCP app with server settings
app = FastMCP(
    name=config.name, 
    version=config.version, 
    description=config.description,
    host=config.host,
    port=config.port,
    log_level=config.log_level
)

# Configure logging
logging.basicConfig(level=getattr(logging, config.log_level))


@app.tool()
def get_cpu_info_tool(interval: float = 1.0, per_cpu: bool = False) -> Dict[str, Any]:
    """Retrieve CPU usage and information.

    Args:
        interval: Measurement interval in seconds (default: 1.0)
        per_cpu: Include per-CPU core breakdown (default: false)
    """
    return get_cpu_info(interval=interval, per_cpu=per_cpu)


@app.tool()
def get_memory_info_tool() -> Dict[str, Any]:
    """Retrieve memory usage statistics."""
    return get_memory_info()


@app.tool()
def get_disk_info_tool(path: Optional[str] = None) -> Dict[str, Any]:
    """Retrieve disk usage information.

    Args:
        path: Specific path to check (default: all mounted disks)
    """
    return get_disk_info(path=path)


@app.tool()
def get_network_info_tool() -> Dict[str, Any]:
    """Retrieve network interface information and statistics."""
    return get_network_info()


@app.tool()
def get_process_list_tool(
    limit: int = 50, sort_by: str = "cpu", filter_name: Optional[str] = None
) -> Dict[str, Any]:
    """Retrieve list of running processes.

    Args:
        limit: Maximum number of processes to return (default: 50)
        sort_by: Sort criteria - cpu, memory, name, pid (default: cpu)
        filter_name: Filter processes by name pattern
    """
    return get_process_list(limit=limit, sort_by=sort_by, filter_name=filter_name)


@app.tool()
def get_system_uptime_tool() -> Dict[str, Any]:
    """Retrieve system uptime and boot information."""
    return get_system_uptime()


@app.tool()
def get_temperature_info_tool() -> Dict[str, Any]:
    """Retrieve system temperature sensors (when available)."""
    return get_temperature_info()


# Resource handlers
@app.resource("system://overview")
def system_overview() -> str:
    """A comprehensive system overview resource."""
    handler = RESOURCE_HANDLERS["system://overview"]
    return handler()


@app.resource("system://processes")
def system_processes() -> str:
    """Current process list resource."""
    handler = RESOURCE_HANDLERS["system://processes"]
    return handler()


def main() -> None:
    """Main entry point for the server."""
    logger.info(f"Starting {config.name} v{config.version}")
    logger.info(f"Transport: {config.transport}")
    
    if config.transport in ["sse", "streamable-http"]:
        logger.info(f"Host: {config.host}")
        logger.info(f"Port: {config.port}")
        if config.transport == "sse":
            logger.info(f"Mount path: {config.mount_path}")
    
    logger.info(f"Cache TTL: {config.cache_ttl}s")
    logger.info(f"Max processes: {config.max_processes}")
    logger.info(
        f"Temperature sensors: {'enabled' if config.enable_temperatures else 'disabled'}"
    )

    try:
        # Run with configured transport
        if config.transport == "sse":
            app.run(transport="sse", mount_path=config.mount_path)
        elif config.transport == "streamable-http":
            app.run(transport="streamable-http")
        else:
            # Default stdio transport
            app.run(transport="stdio")
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")
        raise


if __name__ == "__main__":
    main()
