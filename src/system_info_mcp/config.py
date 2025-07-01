"""Server configuration with environment variable support."""

import os
from dataclasses import dataclass
from typing import Literal


@dataclass
class ServerConfig:
    """Server configuration with environment variable support."""

    name: str = "system-info-server"
    version: str = "1.0.0"
    description: str = "System information MCP server"
    cache_ttl: int = int(os.getenv("SYSINFO_CACHE_TTL", "5"))
    max_processes: int = int(os.getenv("SYSINFO_MAX_PROCESSES", "100"))
    enable_temperatures: bool = (
        os.getenv("SYSINFO_ENABLE_TEMP", "true").lower() == "true"
    )
    log_level: str = os.getenv("SYSINFO_LOG_LEVEL", "INFO")
    
    # Transport configuration
    transport: Literal["stdio", "sse", "streamable-http"] = os.getenv("SYSINFO_TRANSPORT", "stdio")  # type: ignore
    port: int = int(os.getenv("SYSINFO_PORT", "8001"))
    host: str = os.getenv("SYSINFO_HOST", "localhost")
    mount_path: str = os.getenv("SYSINFO_MOUNT_PATH", "/mcp")

    def __post_init__(self) -> None:
        """Validate configuration after initialization."""
        if self.cache_ttl < 0:
            raise ValueError("cache_ttl must be non-negative")
        if self.max_processes <= 0:
            raise ValueError("max_processes must be positive")
        if self.log_level not in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            raise ValueError(f"Invalid log_level: {self.log_level}")
        
        # Validate transport
        valid_transports = ["stdio", "sse", "streamable-http"]
        if self.transport not in valid_transports:
            raise ValueError(f"Invalid transport: {self.transport}. Must be one of {valid_transports}")
        
        # Validate port for HTTP transports
        if self.transport in ["sse", "streamable-http"]:
            if not (1 <= self.port <= 65535):
                raise ValueError("port must be between 1 and 65535")
        
        # Validate mount path
        if self.transport == "sse" and not self.mount_path.startswith("/"):
            raise ValueError("mount_path must start with '/'")


# Global configuration instance
config = ServerConfig()
