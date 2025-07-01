"""Tests for utility functions."""

import time

from system_info_mcp.utils import (
    bytes_to_gb,
    bytes_to_mb,
    format_uptime,
    timestamp_to_iso,
    cache_result,
    clear_cache,
    get_cache_stats,
    safe_float,
    safe_int,
    filter_sensitive_cmdline,
)


class TestDataFormatting:
    """Test data formatting functions."""

    def test_bytes_to_gb(self):
        """Test byte to GB conversion."""
        assert bytes_to_gb(1024**3) == 1.0
        assert bytes_to_gb(1024**3 * 2) == 2.0
        assert bytes_to_gb(1536 * 1024**2) == 1.5  # 1.5 GB
        assert bytes_to_gb(0) == 0.0

    def test_bytes_to_mb(self):
        """Test byte to MB conversion."""
        assert bytes_to_mb(1024**2) == 1.0
        assert bytes_to_mb(1024**2 * 2) == 2.0
        assert bytes_to_mb(1536 * 1024) == 1.5  # 1.5 MB
        assert bytes_to_mb(0) == 0.0

    def test_format_uptime(self):
        """Test uptime formatting."""
        assert format_uptime(0) == "0 minutes"
        assert format_uptime(60) == "1 minute"
        assert format_uptime(120) == "2 minutes"
        assert format_uptime(3600) == "1 hour"
        assert format_uptime(7200) == "2 hours"
        assert format_uptime(86400) == "1 day"
        assert format_uptime(90061) == "1 day, 1 hour, 1 minute"
        assert format_uptime(172800) == "2 days"

    def test_timestamp_to_iso(self):
        """Test timestamp to ISO conversion."""
        timestamp = 1609459200.0  # 2021-01-01 00:00:00 UTC
        iso_string = timestamp_to_iso(timestamp)
        assert iso_string == "2021-01-01T00:00:00+00:00"

    def test_safe_float(self):
        """Test safe float conversion."""
        assert safe_float(1.5) == 1.5
        assert safe_float("1.5") == 1.5
        assert safe_float("invalid") == 0.0
        assert safe_float("invalid", 5.0) == 5.0
        assert safe_float(None) == 0.0

    def test_safe_int(self):
        """Test safe int conversion."""
        assert safe_int(5) == 5
        assert safe_int("5") == 5
        assert safe_int(5.9) == 5
        assert safe_int("invalid") == 0
        assert safe_int("invalid", 10) == 10
        assert safe_int(None) == 0


class TestCaching:
    """Test caching functionality."""

    def setup_method(self):
        """Clear cache before each test."""
        clear_cache()

    def test_cache_decorator_sync(self):
        """Test cache decorator with synchronous function."""
        call_count = 0

        @cache_result("test_sync", ttl=1)
        def test_func(value):
            nonlocal call_count
            call_count += 1
            return value * 2

        # First call should execute function
        result1 = test_func(5)
        assert result1 == 10
        assert call_count == 1

        # Second call should use cache
        result2 = test_func(5)
        assert result2 == 10
        assert call_count == 1  # No additional call

        # Wait for cache to expire
        time.sleep(1.1)
        result3 = test_func(5)
        assert result3 == 10
        assert call_count == 2  # Cache expired, function called again

    def test_cache_clear(self):
        """Test cache clearing."""

        @cache_result("test_clear")
        def test_func():
            return "cached_value"

        # Cache a value
        test_func()
        stats = get_cache_stats()
        assert stats["total_entries"] == 1

        # Clear specific cache
        clear_cache("test_clear")
        stats = get_cache_stats()
        assert stats["total_entries"] == 0

        # Cache again and clear all
        test_func()
        clear_cache()  # Clear all
        stats = get_cache_stats()
        assert stats["total_entries"] == 0

    def test_cache_stats(self):
        """Test cache statistics."""

        @cache_result("test_stats")
        def test_func():
            return "value"

        # No cache initially
        stats = get_cache_stats()
        assert stats["total_entries"] == 0

        # Add cache entry
        test_func()
        stats = get_cache_stats()
        assert stats["total_entries"] == 1
        assert "test_stats" in stats["entries"]
        assert stats["entries"]["test_stats"]["age_seconds"] >= 0
        assert not stats["entries"]["test_stats"]["expired"]


class TestCommandLineFiltering:
    """Test command line argument filtering."""

    def test_filter_sensitive_cmdline(self):
        """Test filtering of sensitive command line arguments."""
        # Test empty command line
        assert filter_sensitive_cmdline([]) == []

        # Test normal arguments
        normal_cmd = ["python", "script.py", "--verbose"]
        assert filter_sensitive_cmdline(normal_cmd) == normal_cmd

        # Test password with equals
        password_cmd = ["mysql", "--password=secret123", "--host=localhost"]
        expected = ["mysql", "--password=[REDACTED]", "--host=localhost"]
        assert filter_sensitive_cmdline(password_cmd) == expected

        # Test password as separate argument
        password_cmd2 = ["mysql", "--password", "secret123", "--host", "localhost"]
        expected2 = ["mysql", "--password", "[REDACTED]", "--host", "localhost"]
        assert filter_sensitive_cmdline(password_cmd2) == expected2

        # Test multiple sensitive arguments
        multi_cmd = ["app", "--token", "abc123", "--secret=def456", "--key", "ghi789"]
        expected_multi = [
            "app",
            "--token",
            "[REDACTED]",
            "--secret=[REDACTED]",
            "--key",
            "[REDACTED]",
        ]
        assert filter_sensitive_cmdline(multi_cmd) == expected_multi

        # Test case insensitive matching
        case_cmd = ["app", "--PASSWORD", "secret", "--Token=token123"]
        expected_case = ["app", "--PASSWORD", "[REDACTED]", "--Token=[REDACTED]"]
        assert filter_sensitive_cmdline(case_cmd) == expected_case
