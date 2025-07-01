"""Tests for tool implementations."""

import pytest
from unittest.mock import patch, MagicMock

from system_info_mcp.tools import (
    get_cpu_info,
    get_memory_info,
    get_disk_info,
    get_network_info,
    get_process_list,
    get_system_uptime,
    get_temperature_info,
)
from system_info_mcp.utils import clear_cache


class TestCpuInfo:
    """Test CPU information tool."""

    def setup_method(self):
        """Clear cache before each test."""
        clear_cache()

    @patch("system_info_mcp.tools.psutil.cpu_percent")
    @patch("system_info_mcp.tools.psutil.cpu_count")
    @patch("system_info_mcp.tools.psutil.cpu_freq")
    @patch("system_info_mcp.tools.os.getloadavg")
    def test_get_cpu_info_basic(
        self, mock_loadavg, mock_freq, mock_count, mock_percent
    ):
        """Test basic CPU info retrieval."""
        # Mock psutil responses
        mock_percent.return_value = 45.2
        mock_count.side_effect = lambda logical=True: 8 if logical else 4
        mock_freq.return_value = MagicMock(current=2400.0, max=3400.0)
        mock_loadavg.return_value = (1.2, 1.5, 1.8)

        result = get_cpu_info(interval=0.1)

        assert result["cpu_percent"] == 45.2
        assert result["cpu_count_logical"] == 8
        assert result["cpu_count_physical"] == 4
        assert result["cpu_freq_current"] == 2400.0
        assert result["cpu_freq_max"] == 3400.0
        assert result["load_average"] == [1.2, 1.5, 1.8]
        assert "per_cpu_percent" not in result

    @patch("system_info_mcp.tools.psutil.cpu_percent")
    @patch("system_info_mcp.tools.psutil.cpu_count")
    @patch("system_info_mcp.tools.psutil.cpu_freq")
    @patch("system_info_mcp.tools.os.getloadavg")
    def test_get_cpu_info_per_cpu(
        self, mock_loadavg, mock_freq, mock_count, mock_percent
    ):
        """Test CPU info with per-CPU breakdown."""
        # First call is for overall CPU, second call is for per-CPU
        mock_percent.side_effect = [45.2, [42.1, 48.3, 44.7, 46.9]]
        mock_count.side_effect = lambda logical=True: 4 if logical else 2
        mock_freq.return_value = MagicMock(current=2400.0, max=3400.0)
        mock_loadavg.return_value = (1.0, 1.0, 1.0)

        result = get_cpu_info(interval=0.1, per_cpu=True)

        assert result["per_cpu_percent"] == [42.1, 48.3, 44.7, 46.9]

    @patch("system_info_mcp.tools.psutil.cpu_percent")
    @patch("system_info_mcp.tools.psutil.cpu_count")
    @patch("system_info_mcp.tools.psutil.cpu_freq")
    @patch("system_info_mcp.tools.os.getloadavg")
    def test_get_cpu_info_invalid_interval(self, mock_loadavg, mock_freq, mock_count, mock_percent):
        """Test CPU info with invalid interval."""
        clear_cache()  # Clear cache for clean test
        with pytest.raises(ValueError, match="Interval must be a positive number"):
            get_cpu_info(interval=-1.0)

        with pytest.raises(ValueError, match="Interval must be a positive number"):
            get_cpu_info(interval=0.0)


class TestMemoryInfo:
    """Test memory information tool."""

    def setup_method(self):
        """Clear cache before each test."""
        clear_cache()

    @patch("system_info_mcp.tools.psutil.virtual_memory")
    @patch("system_info_mcp.tools.psutil.swap_memory")
    def test_get_memory_info(self, mock_swap, mock_virtual):
        """Test memory info retrieval."""
        # Mock virtual memory
        mock_virtual.return_value = MagicMock(
            total=17179869184,  # 16 GB
            available=8589934592,  # 8 GB
            used=8589934592,  # 8 GB
            percent=50.0,
        )

        # Mock swap memory
        mock_swap.return_value = MagicMock(
            total=2147483648, used=0, free=2147483648, percent=0.0  # 2 GB
        )

        result = get_memory_info()

        assert result["virtual_memory"]["total"] == 17179869184
        assert result["virtual_memory"]["available"] == 8589934592
        assert result["virtual_memory"]["used"] == 8589934592
        assert result["virtual_memory"]["percent"] == 50.0
        assert result["virtual_memory"]["total_gb"] == 16.0
        assert result["virtual_memory"]["available_gb"] == 8.0
        assert result["virtual_memory"]["used_gb"] == 8.0

        assert result["swap_memory"]["total"] == 2147483648
        assert result["swap_memory"]["used"] == 0
        assert result["swap_memory"]["free"] == 2147483648
        assert result["swap_memory"]["percent"] == 0.0
        assert result["swap_memory"]["total_gb"] == 2.0


class TestDiskInfo:
    """Test disk information tool."""

    def setup_method(self):
        """Clear cache before each test."""
        clear_cache()

    @patch("system_info_mcp.tools.psutil.disk_partitions")
    @patch("system_info_mcp.tools.psutil.disk_usage")
    def test_get_disk_info_all_disks(self, mock_usage, mock_partitions):
        """Test disk info for all disks."""
        # Mock partitions
        mock_partitions.return_value = [
            MagicMock(mountpoint="/", device="/dev/disk1s1", fstype="apfs")
        ]

        # Mock disk usage
        mock_usage.return_value = MagicMock(
            total=494384795648,  # ~460 GB
            used=123456789012,  # ~115 GB
            free=370927006636,  # ~345 GB
        )

        result = get_disk_info()

        assert len(result["disks"]) == 1
        disk = result["disks"][0]
        assert disk["mountpoint"] == "/"
        assert disk["device"] == "/dev/disk1s1"
        assert disk["fstype"] == "apfs"
        assert disk["total"] == 494384795648
        assert disk["used"] == 123456789012
        assert disk["free"] == 370927006636
        assert disk["percent"] == 25.0

    @patch("system_info_mcp.tools.psutil.disk_usage")
    def test_get_disk_info_specific_path(self, mock_usage):
        """Test disk info for specific path."""
        mock_usage.return_value = MagicMock(
            total=1000000000, used=500000000, free=500000000
        )

        result = get_disk_info(path="/home")

        assert len(result["disks"]) == 1
        disk = result["disks"][0]
        assert disk["mountpoint"] == "/home"
        assert disk["device"] == "N/A"
        assert disk["fstype"] == "N/A"
        assert disk["percent"] == 50.0


class TestNetworkInfo:
    """Test network information tool."""

    def setup_method(self):
        """Clear cache before each test."""
        clear_cache()

    @patch("system_info_mcp.tools.psutil.net_if_addrs")
    @patch("system_info_mcp.tools.psutil.net_if_stats")
    @patch("system_info_mcp.tools.psutil.net_io_counters")
    def test_get_network_info(self, mock_io, mock_stats, mock_addrs):
        """Test network info retrieval."""
        # Mock network interfaces
        mock_addrs.return_value = {
            "en0": [
                MagicMock(
                    family=2,  # AF_INET
                    address="192.168.1.100",
                    netmask="255.255.255.0",
                )
            ]
        }

        mock_stats.return_value = {"en0": MagicMock(isup=True, speed=1000, mtu=1500)}

        mock_io.return_value = MagicMock(
            bytes_sent=1234567890,
            bytes_recv=9876543210,
            packets_sent=123456,
            packets_recv=654321,
            errin=0,
            errout=0,
            dropin=0,
            dropout=0,
        )

        result = get_network_info()

        assert len(result["interfaces"]) == 1
        interface = result["interfaces"][0]
        assert interface["name"] == "en0"
        assert interface["is_up"] is True
        assert interface["speed"] == 1000
        assert interface["mtu"] == 1500
        assert len(interface["addresses"]) == 1
        assert interface["addresses"][0]["address"] == "192.168.1.100"

        stats = result["stats"]
        assert stats["bytes_sent"] == 1234567890
        assert stats["bytes_recv"] == 9876543210
        assert stats["packets_sent"] == 123456
        assert stats["packets_recv"] == 654321


class TestProcessList:
    """Test process list tool."""

    def setup_method(self):
        """Clear cache before each test."""
        clear_cache()

    @patch("system_info_mcp.tools.psutil.process_iter")
    def test_get_process_list_basic(self, mock_iter):
        """Test basic process list retrieval."""
        # Mock process data
        mock_process = MagicMock()
        mock_process.info = {
            "pid": 1234,
            "name": "python3",
            "username": "user",
            "status": "running",
            "cpu_percent": 15.2,
            "memory_percent": 2.1,
            "memory_info": MagicMock(rss=134217728),  # 128 MB
            "create_time": 1642252200.0,
            "cmdline": ["python3", "app.py"],
        }
        mock_iter.return_value = [mock_process]

        result = get_process_list(limit=10)

        assert len(result["processes"]) == 1
        assert result["total_processes"] == 1

        process = result["processes"][0]
        assert process["pid"] == 1234
        assert process["name"] == "python3"
        assert process["username"] == "user"
        assert process["status"] == "running"
        assert process["cpu_percent"] == 15.2
        assert process["memory_percent"] == 2.1
        assert process["memory_rss"] == 134217728
        assert process["memory_rss_mb"] == 128.0
        assert process["cmdline"] == ["python3", "app.py"]

    def test_get_process_list_invalid_parameters(self):
        """Test process list with invalid parameters."""
        clear_cache()  # Clear cache for clean test
        with pytest.raises(ValueError, match="Limit must be a positive number"):
            get_process_list(limit=-1)

        with pytest.raises(ValueError, match="sort_by must be one of"):
            get_process_list(sort_by="invalid")


class TestSystemUptime:
    """Test system uptime tool."""

    def setup_method(self):
        """Clear cache before each test."""
        clear_cache()

    @patch("system_info_mcp.tools.psutil.boot_time")
    @patch("system_info_mcp.tools.time.time")
    def test_get_system_uptime(self, mock_time, mock_boot):
        """Test system uptime retrieval."""
        mock_boot.return_value = 1609459200.0  # 2021-01-01 00:00:00 UTC
        mock_time.return_value = (
            1609545600.0  # 2021-01-02 00:00:00 UTC (24 hours later)
        )

        result = get_system_uptime()

        assert result["boot_time"] == "2021-01-01T00:00:00+00:00"
        assert result["uptime_seconds"] == 86400  # 24 hours
        assert result["uptime_formatted"] == "1 day"


class TestTemperatureInfo:
    """Test temperature information tool."""

    def setup_method(self):
        """Clear cache before each test."""
        clear_cache()

    @patch("system_info_mcp.tools.psutil.sensors_temperatures", create=True)
    @patch("system_info_mcp.tools.psutil.sensors_fans", create=True)
    def test_get_temperature_info_available(self, mock_fans, mock_temps):
        """Test temperature info when sensors are available."""
        # Mock temperature sensors
        mock_temps.return_value = {
            "cpu_thermal": [
                MagicMock(label="CPU Package", current=45.0, high=100.0, critical=105.0)
            ]
        }

        # Mock fan sensors
        mock_fans.return_value = {"cpu_fan": [MagicMock(label="CPU Fan", current=1200)]}

        result = get_temperature_info()

        assert len(result["temperatures"]) == 1
        temp = result["temperatures"][0]
        assert temp["name"] == "CPU Package"
        assert temp["current"] == 45.0
        assert temp["high"] == 100.0
        assert temp["critical"] == 105.0
        assert temp["unit"] == "celsius"

        assert len(result["fans"]) == 1
        fan = result["fans"][0]
        assert fan["name"] == "CPU Fan"
        assert fan["current_speed"] == 1200
        assert fan["unit"] == "rpm"

    @patch("system_info_mcp.tools.psutil.sensors_temperatures", create=True)
    @patch("system_info_mcp.tools.psutil.sensors_fans", create=True)
    def test_get_temperature_info_unavailable(self, mock_fans, mock_temps):
        """Test temperature info when sensors are unavailable."""
        mock_temps.side_effect = AttributeError("Not supported")
        mock_fans.side_effect = AttributeError("Not supported")

        result = get_temperature_info()

        assert result["temperatures"] == []
        assert result["fans"] == []
