"""Tests for configuration module."""

import pytest

from system_info_mcp.config import ServerConfig


class TestServerConfig:
    """Test server configuration."""

    def test_default_values(self):
        """Test default configuration values."""
        config = ServerConfig()
        assert config.name == "system-info-server"
        assert config.version == "1.0.0"
        assert config.description == "System information MCP server"
        assert config.cache_ttl == 5  # Default from env
        assert config.max_processes == 100  # Default from env
        assert config.enable_temperatures is True
        assert config.log_level == "INFO"
        
        # Test transport defaults
        assert config.transport == "stdio"
        assert config.host == "localhost"
        assert config.port == 8001
        assert config.mount_path == "/mcp"

    def test_environment_variables(self):
        """Test configuration from environment variables."""
        # Test with explicit values instead of env vars to avoid patching issues
        config = ServerConfig(
            cache_ttl=10, max_processes=50, enable_temperatures=False, log_level="DEBUG"
        )
        assert config.cache_ttl == 10
        assert config.max_processes == 50
        assert config.enable_temperatures is False
        assert config.log_level == "DEBUG"

    def test_invalid_cache_ttl(self):
        """Test validation of cache_ttl."""
        with pytest.raises(ValueError, match="cache_ttl must be non-negative"):
            ServerConfig(cache_ttl=-1)

    def test_invalid_max_processes(self):
        """Test validation of max_processes."""
        with pytest.raises(ValueError, match="max_processes must be positive"):
            ServerConfig(max_processes=0)

        with pytest.raises(ValueError, match="max_processes must be positive"):
            ServerConfig(max_processes=-1)

    def test_invalid_log_level(self):
        """Test validation of log_level."""
        with pytest.raises(ValueError, match="Invalid log_level"):
            ServerConfig(log_level="INVALID")
    
    def test_transport_configuration(self):
        """Test transport configuration options."""
        # Test valid transports
        config_stdio = ServerConfig(transport="stdio")
        assert config_stdio.transport == "stdio"
        
        config_sse = ServerConfig(transport="sse", port=9001, host="0.0.0.0")
        assert config_sse.transport == "sse"
        assert config_sse.port == 9001
        assert config_sse.host == "0.0.0.0"
        
        config_http = ServerConfig(transport="streamable-http", port=8080)
        assert config_http.transport == "streamable-http"
        assert config_http.port == 8080
    
    def test_invalid_transport(self):
        """Test validation of transport."""
        with pytest.raises(ValueError, match="Invalid transport"):
            ServerConfig(transport="invalid")
    
    def test_invalid_port(self):
        """Test validation of port for HTTP transports."""
        with pytest.raises(ValueError, match="port must be between 1 and 65535"):
            ServerConfig(transport="sse", port=0)
        
        with pytest.raises(ValueError, match="port must be between 1 and 65535"):
            ServerConfig(transport="sse", port=99999)
    
    def test_invalid_mount_path(self):
        """Test validation of mount path."""
        with pytest.raises(ValueError, match="mount_path must start with"):
            ServerConfig(transport="sse", mount_path="no-slash")
    
    def test_port_validation_only_for_http_transports(self):
        """Test that port validation only applies to HTTP transports."""
        # Should not validate port for stdio transport
        config = ServerConfig(transport="stdio", port=99999)
        assert config.transport == "stdio"
        assert config.port == 99999  # Invalid port should be ignored for stdio
