"""Tool implementations for system information."""

import os
import psutil
import time
from typing import Any, Dict, Optional

from .utils import (
    bytes_to_gb,
    bytes_to_mb,
    format_uptime,
    timestamp_to_iso,
    cache_result,
    safe_float,
    safe_int,
    filter_sensitive_cmdline,
    logger,
)
from .config import config


@cache_result("cpu_info", ttl=2)
def get_cpu_info(interval: float = 1.0, per_cpu: bool = False) -> Dict[str, Any]:
    """Retrieve CPU usage and information."""
    try:
        # Validate parameters
        if interval <= 0:
            raise ValueError("Interval must be a positive number")

        # Get CPU percentage (this call blocks for the interval)
        cpu_percent = psutil.cpu_percent(interval=interval)

        # Get per-CPU percentages if requested
        per_cpu_percent = None
        if per_cpu:
            per_cpu_percent = psutil.cpu_percent(interval=0, percpu=True)

        # Get CPU counts
        cpu_count_logical = psutil.cpu_count(logical=True) or 0
        cpu_count_physical = psutil.cpu_count(logical=False) or 0

        # Get CPU frequency
        try:
            cpu_freq = psutil.cpu_freq()
            cpu_freq_current = safe_float(cpu_freq.current if cpu_freq else 0)
            cpu_freq_max = safe_float(cpu_freq.max if cpu_freq else 0)
        except (AttributeError, OSError):
            cpu_freq_current = 0.0
            cpu_freq_max = 0.0

        # Get load average (Unix-like systems only)
        try:
            if hasattr(os, 'getloadavg'):
                load_avg = os.getloadavg()
                load_average = [round(avg, 2) for avg in load_avg]
            else:
                load_average = [0.0, 0.0, 0.0]
        except (AttributeError, OSError):
            load_average = [0.0, 0.0, 0.0]

        result = {
            "cpu_percent": round(cpu_percent, 1),
            "cpu_count_logical": cpu_count_logical,
            "cpu_count_physical": cpu_count_physical,
            "cpu_freq_current": cpu_freq_current,
            "cpu_freq_max": cpu_freq_max,
            "load_average": load_average,
        }

        if per_cpu_percent is not None:
            result["per_cpu_percent"] = [round(p, 1) for p in per_cpu_percent]

        return result

    except Exception as e:
        logger.error(f"Error getting CPU info: {e}")
        raise


@cache_result("memory_info", ttl=1)
def get_memory_info() -> Dict[str, Any]:
    """Retrieve memory usage statistics."""
    try:
        # Get virtual memory info
        virtual_mem = psutil.virtual_memory()

        # Get swap memory info
        swap_mem = psutil.swap_memory()

        return {
            "virtual_memory": {
                "total": virtual_mem.total,
                "available": virtual_mem.available,
                "used": virtual_mem.used,
                "percent": round(virtual_mem.percent, 1),
                "total_gb": bytes_to_gb(virtual_mem.total),
                "available_gb": bytes_to_gb(virtual_mem.available),
                "used_gb": bytes_to_gb(virtual_mem.used),
            },
            "swap_memory": {
                "total": swap_mem.total,
                "used": swap_mem.used,
                "free": swap_mem.free,
                "percent": round(swap_mem.percent, 1),
                "total_gb": bytes_to_gb(swap_mem.total),
            },
        }

    except Exception as e:
        logger.error(f"Error getting memory info: {e}")
        raise


@cache_result("disk_info", ttl=10)
def get_disk_info(path: Optional[str] = None) -> Dict[str, Any]:
    """Retrieve disk usage information."""
    try:
        disks = []

        if path:
            # Get info for specific path
            try:
                usage = psutil.disk_usage(path)
                disks.append(
                    {
                        "mountpoint": path,
                        "device": "N/A",
                        "fstype": "N/A",
                        "total": usage.total,
                        "used": usage.used,
                        "free": usage.free,
                        "percent": round((usage.used / usage.total) * 100, 1),
                        "total_gb": bytes_to_gb(usage.total),
                        "used_gb": bytes_to_gb(usage.used),
                        "free_gb": bytes_to_gb(usage.free),
                    }
                )
            except (OSError, PermissionError) as e:
                logger.warning(f"Could not get disk info for path {path}: {e}")
        else:
            # Get info for all mounted disks
            partitions = psutil.disk_partitions()

            for partition in partitions:
                try:
                    usage = psutil.disk_usage(partition.mountpoint)

                    disks.append(
                        {
                            "mountpoint": partition.mountpoint,
                            "device": partition.device,
                            "fstype": partition.fstype,
                            "total": usage.total,
                            "used": usage.used,
                            "free": usage.free,
                            "percent": (
                                round((usage.used / usage.total) * 100, 1)
                                if usage.total
                                else 0
                            ),
                            "total_gb": bytes_to_gb(usage.total),
                            "used_gb": bytes_to_gb(usage.used),
                            "free_gb": bytes_to_gb(usage.free),
                        }
                    )
                except (OSError, PermissionError) as e:
                    logger.warning(
                        f"Could not get usage for {partition.mountpoint}: {e}"
                    )
                    continue

        return {"disks": disks}

    except Exception as e:
        logger.error(f"Error getting disk info: {e}")
        raise


@cache_result("network_info", ttl=5)
def get_network_info() -> Dict[str, Any]:
    """Retrieve network interface information and statistics."""
    try:
        interfaces = []

        # Get network interfaces
        net_if_addrs = psutil.net_if_addrs()
        net_if_stats = psutil.net_if_stats()

        for interface_name, addresses in net_if_addrs.items():
            interface_info: Dict[str, Any] = {
                "name": interface_name,
                "addresses": [],
                "is_up": False,
                "speed": 0,
                "mtu": 0,
            }

            # Get interface statistics
            if interface_name in net_if_stats:
                stats = net_if_stats[interface_name]
                interface_info.update(
                    {"is_up": stats.isup, "speed": stats.speed, "mtu": stats.mtu}
                )

            # Get addresses
            for addr in addresses:
                addr_info = {"family": str(addr.family), "address": addr.address}
                if addr.netmask:
                    addr_info["netmask"] = addr.netmask
                interface_info["addresses"].append(addr_info)

            interfaces.append(interface_info)

        # Get network I/O statistics
        try:
            net_io = psutil.net_io_counters()
            if net_io:
                io_stats = {
                    "bytes_sent": net_io.bytes_sent,
                    "bytes_recv": net_io.bytes_recv,
                    "packets_sent": net_io.packets_sent,
                    "packets_recv": net_io.packets_recv,
                    "errin": net_io.errin,
                    "errout": net_io.errout,
                    "dropin": net_io.dropin,
                    "dropout": net_io.dropout,
                }
            else:
                io_stats = {
                    "bytes_sent": 0,
                    "bytes_recv": 0,
                    "packets_sent": 0,
                    "packets_recv": 0,
                    "errin": 0,
                    "errout": 0,
                    "dropin": 0,
                    "dropout": 0,
                }
        except Exception as e:
            logger.warning(f"Could not get network I/O stats: {e}")
            io_stats = {
                "bytes_sent": 0,
                "bytes_recv": 0,
                "packets_sent": 0,
                "packets_recv": 0,
                "errin": 0,
                "errout": 0,
                "dropin": 0,
                "dropout": 0,
            }

        return {"interfaces": interfaces, "stats": io_stats}

    except Exception as e:
        logger.error(f"Error getting network info: {e}")
        raise


@cache_result("process_list", ttl=2)
def get_process_list(
    limit: int = 50, sort_by: str = "cpu", filter_name: Optional[str] = None
) -> Dict[str, Any]:
    """Retrieve list of running processes."""
    try:
        # Validate parameters
        if limit <= 0:
            raise ValueError("Limit must be a positive number")

        limit = min(limit, config.max_processes)

        valid_sort_keys = ["cpu", "memory", "name", "pid"]
        if sort_by not in valid_sort_keys:
            raise ValueError(f"sort_by must be one of: {valid_sort_keys}")

        processes = []

        # Get all processes
        for proc in psutil.process_iter(
            [
                "pid",
                "name",
                "username",
                "status",
                "cpu_percent",
                "memory_percent",
                "memory_info",
                "create_time",
                "cmdline",
            ]
        ):
            try:
                proc_info = proc.info

                # Filter by name if specified
                if filter_name and filter_name.lower() not in proc_info["name"].lower():
                    continue

                # Get memory RSS
                memory_rss = 0
                if proc_info.get("memory_info"):
                    memory_rss = proc_info["memory_info"].rss

                # Filter and format command line
                cmdline = filter_sensitive_cmdline(proc_info.get("cmdline") or [])

                process_data = {
                    "pid": proc_info["pid"],
                    "name": proc_info["name"] or "Unknown",
                    "username": proc_info.get("username", "Unknown"),
                    "status": proc_info.get("status", "unknown"),
                    "cpu_percent": round(
                        safe_float(proc_info.get("cpu_percent", 0)), 1
                    ),
                    "memory_percent": round(
                        safe_float(proc_info.get("memory_percent", 0)), 1
                    ),
                    "memory_rss": memory_rss,
                    "memory_rss_mb": bytes_to_mb(memory_rss),
                    "create_time": timestamp_to_iso(proc_info.get("create_time", 0)),
                    "cmdline": cmdline,
                }

                processes.append(process_data)

            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                # Process may have terminated or we don't have permission
                continue

        # Sort processes
        reverse_sort = True  # Most metrics should be sorted in descending order
        if sort_by == "cpu":
            processes.sort(key=lambda p: p["cpu_percent"], reverse=reverse_sort)
        elif sort_by == "memory":
            processes.sort(key=lambda p: p["memory_percent"], reverse=reverse_sort)
        elif sort_by == "name":
            processes.sort(key=lambda p: p["name"].lower(), reverse=False)
        elif sort_by == "pid":
            processes.sort(key=lambda p: p["pid"], reverse=False)

        # Apply limit
        limited_processes = processes[:limit]

        return {"processes": limited_processes, "total_processes": len(processes)}

    except Exception as e:
        logger.error(f"Error getting process list: {e}")
        raise


@cache_result("system_uptime", ttl=30)
def get_system_uptime() -> Dict[str, Any]:
    """Retrieve system uptime and boot information."""
    try:
        boot_time = psutil.boot_time()
        current_time = time.time()
        uptime_seconds = int(current_time - boot_time)

        return {
            "boot_time": timestamp_to_iso(boot_time),
            "uptime_seconds": uptime_seconds,
            "uptime_formatted": format_uptime(uptime_seconds),
        }

    except Exception as e:
        logger.error(f"Error getting system uptime: {e}")
        raise


@cache_result("temperature_info", ttl=10)
def get_temperature_info() -> Dict[str, Any]:
    """Retrieve system temperature sensors (when available)."""
    if not config.enable_temperatures:
        return {"temperatures": [], "fans": []}

    try:
        temperatures = []
        fans = []

        # Try to get temperature sensors
        try:
            if hasattr(psutil, 'sensors_temperatures'):
                sensors_temps = psutil.sensors_temperatures()
                if sensors_temps:
                    for sensor_name, temps in sensors_temps.items():
                        for temp in temps:
                            temp_info = {
                                "name": temp.label or sensor_name,
                                "current": round(temp.current, 1),
                                "unit": "celsius",
                            }
                            if temp.high:
                                temp_info["high"] = round(temp.high, 1)
                            if temp.critical:
                                temp_info["critical"] = round(temp.critical, 1)
                            temperatures.append(temp_info)
        except (AttributeError, OSError) as e:
            logger.debug(f"Temperature sensors not available: {e}")

        # Try to get fan sensors
        try:
            if hasattr(psutil, 'sensors_fans'):
                sensors_fans = psutil.sensors_fans()
                if sensors_fans:
                    for fan_name, fan_list in sensors_fans.items():
                        for fan in fan_list:
                            fan_info = {
                                "name": fan.label or fan_name,
                                "current_speed": safe_int(fan.current),
                                "unit": "rpm",
                            }
                            fans.append(fan_info)
        except (AttributeError, OSError) as e:
            logger.debug(f"Fan sensors not available: {e}")

        return {"temperatures": temperatures, "fans": fans}

    except Exception as e:
        logger.error(f"Error getting temperature info: {e}")
        raise
