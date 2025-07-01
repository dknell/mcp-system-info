"""Tests for resource handlers."""

import json
from unittest.mock import patch

from system_info_mcp.resources import get_system_overview, get_system_processes


class TestSystemOverview:
    """Test system overview resource."""

    @patch("system_info_mcp.resources.get_cpu_info")
    @patch("system_info_mcp.resources.get_memory_info")
    @patch("system_info_mcp.resources.get_disk_info")
    @patch("system_info_mcp.resources.get_network_info")
    @patch("system_info_mcp.resources.get_system_uptime")
    def test_get_system_overview_success(
        self, mock_uptime, mock_network, mock_disk, mock_memory, mock_cpu
    ):
        """Test successful system overview generation."""
        # Mock all the tool responses
        mock_cpu.return_value = {
            "cpu_percent": 45.2,
            "cpu_count_logical": 8,
            "cpu_count_physical": 4,
            "cpu_freq_current": 2400.0,
            "load_average": [1.2, 1.5, 1.8],
        }

        mock_memory.return_value = {
            "virtual_memory": {
                "total_gb": 16.0,
                "used_gb": 8.0,
                "available_gb": 8.0,
                "percent": 50.0,
            },
            "swap_memory": {"total_gb": 2.0, "percent": 0.0},
        }

        mock_disk.return_value = {
            "disks": [
                {
                    "mountpoint": "/",
                    "total_gb": 460.4,
                    "used_gb": 115.0,
                    "free_gb": 345.4,
                    "percent": 25.0,
                }
            ]
        }

        mock_network.return_value = {
            "interfaces": [
                {"name": "en0", "is_up": True},
                {"name": "lo0", "is_up": True},
            ],
            "stats": {"bytes_sent": 1234567890, "bytes_recv": 9876543210},
        }

        mock_uptime.return_value = {
            "boot_time": "2022-01-15T10:30:00+00:00",
            "uptime_formatted": "1 day",
        }

        result = get_system_overview()

        # Parse the JSON result
        overview = json.loads(result)

        # Verify structure and content
        assert "timestamp" in overview
        assert "uptime" in overview
        assert overview["uptime"] == "1 day"

        # Check CPU summary
        cpu_summary = overview["cpu_summary"]
        assert cpu_summary["usage_percent"] == 45.2
        assert cpu_summary["logical_cores"] == 8
        assert cpu_summary["physical_cores"] == 4
        assert cpu_summary["frequency_mhz"] == 2400.0
        assert cpu_summary["load_average"] == [1.2, 1.5, 1.8]

        # Check memory summary
        memory_summary = overview["memory_summary"]
        assert memory_summary["total_gb"] == 16.0
        assert memory_summary["used_gb"] == 8.0
        assert memory_summary["available_gb"] == 8.0
        assert memory_summary["usage_percent"] == 50.0
        assert memory_summary["swap_total_gb"] == 2.0
        assert memory_summary["swap_usage_percent"] == 0.0

        # Check disk summary
        disk_summary = overview["disk_summary"]
        assert disk_summary["total_disks"] == 1
        assert len(disk_summary["disks"]) == 1
        disk = disk_summary["disks"][0]
        assert disk["mountpoint"] == "/"
        assert disk["total_gb"] == 460.4
        assert disk["used_gb"] == 115.0
        assert disk["free_gb"] == 345.4
        assert disk["usage_percent"] == 25.0

        # Check network summary
        network_summary = overview["network_summary"]
        assert network_summary["total_interfaces"] == 2
        assert network_summary["active_interfaces"] == 2
        assert network_summary["bytes_sent"] == 1234567890
        assert network_summary["bytes_received"] == 9876543210

    @patch("system_info_mcp.resources.get_cpu_info")
    def test_get_system_overview_error(self, mock_cpu):
        """Test system overview with error."""
        mock_cpu.side_effect = Exception("Test error")

        result = get_system_overview()

        # Parse the JSON result
        error_response = json.loads(result)
        assert "error" in error_response
        assert "Failed to generate system overview" in error_response["error"]


class TestSystemProcesses:
    """Test system processes resource."""

    @patch("system_info_mcp.resources.get_process_list")
    def test_get_system_processes_success(self, mock_process_list):
        """Test successful system processes generation."""
        mock_process_list.return_value = {
            "processes": [
                {
                    "pid": 1234,
                    "name": "python3",
                    "cpu_percent": 15.2,
                    "memory_percent": 2.1,
                    "memory_rss_mb": 128.0,
                    "username": "user",
                    "status": "running",
                },
                {
                    "pid": 5678,
                    "name": "chrome",
                    "cpu_percent": 8.5,
                    "memory_percent": 4.3,
                    "memory_rss_mb": 256.0,
                    "username": "user",
                    "status": "running",
                },
            ],
            "total_processes": 156,
        }

        result = get_system_processes()

        # Parse the JSON result
        processes_data = json.loads(result)

        # Verify structure
        assert "summary" in processes_data
        assert "processes" in processes_data

        # Check summary
        summary = processes_data["summary"]
        assert summary["total_processes"] == 156
        assert summary["showing_top"] == 2
        assert summary["sorted_by"] == "cpu_usage"

        # Check processes
        processes = processes_data["processes"]
        assert len(processes) == 2

        # Check first process
        proc1 = processes[0]
        assert proc1["pid"] == 1234
        assert proc1["name"] == "python3"
        assert proc1["cpu_percent"] == 15.2
        assert proc1["memory_percent"] == 2.1
        assert proc1["memory_mb"] == 128.0
        assert proc1["username"] == "user"
        assert proc1["status"] == "running"

        # Check second process
        proc2 = processes[1]
        assert proc2["pid"] == 5678
        assert proc2["name"] == "chrome"
        assert proc2["cpu_percent"] == 8.5
        assert proc2["memory_percent"] == 4.3
        assert proc2["memory_mb"] == 256.0
        assert proc2["username"] == "user"
        assert proc2["status"] == "running"

    @patch("system_info_mcp.resources.get_process_list")
    def test_get_system_processes_error(self, mock_process_list):
        """Test system processes with error."""
        mock_process_list.side_effect = Exception("Test error")

        result = get_system_processes()

        # Parse the JSON result
        error_response = json.loads(result)
        assert "error" in error_response
        assert "Failed to generate process list" in error_response["error"]
