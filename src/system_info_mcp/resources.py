"""Resource handlers for system information."""

import json

from .tools import (
    get_cpu_info,
    get_memory_info,
    get_disk_info,
    get_network_info,
    get_process_list,
    get_system_uptime,
)
from .utils import logger


def get_system_overview() -> str:
    """Get comprehensive system overview resource."""
    try:
        # Gather all system information
        cpu_info = get_cpu_info(interval=0.1, per_cpu=False)  # Quick snapshot
        memory_info = get_memory_info()
        disk_info = get_disk_info()
        network_info = get_network_info()
        uptime_info = get_system_uptime()

        # Create overview summary
        overview = {
            "timestamp": uptime_info.get("boot_time", "unknown"),
            "uptime": uptime_info.get("uptime_formatted", "unknown"),
            "cpu_summary": {
                "usage_percent": cpu_info.get("cpu_percent", 0),
                "logical_cores": cpu_info.get("cpu_count_logical", 0),
                "physical_cores": cpu_info.get("cpu_count_physical", 0),
                "frequency_mhz": cpu_info.get("cpu_freq_current", 0),
                "load_average": cpu_info.get("load_average", [0, 0, 0]),
            },
            "memory_summary": {
                "total_gb": memory_info.get("virtual_memory", {}).get("total_gb", 0),
                "used_gb": memory_info.get("virtual_memory", {}).get("used_gb", 0),
                "available_gb": memory_info.get("virtual_memory", {}).get(
                    "available_gb", 0
                ),
                "usage_percent": memory_info.get("virtual_memory", {}).get(
                    "percent", 0
                ),
                "swap_total_gb": memory_info.get("swap_memory", {}).get("total_gb", 0),
                "swap_usage_percent": memory_info.get("swap_memory", {}).get(
                    "percent", 0
                ),
            },
            "disk_summary": {
                "total_disks": len(disk_info.get("disks", [])),
                "disks": [
                    {
                        "mountpoint": disk["mountpoint"],
                        "total_gb": disk["total_gb"],
                        "used_gb": disk["used_gb"],
                        "free_gb": disk["free_gb"],
                        "usage_percent": disk["percent"],
                    }
                    for disk in disk_info.get("disks", [])
                ],
            },
            "network_summary": {
                "total_interfaces": len(network_info.get("interfaces", [])),
                "active_interfaces": len(
                    [
                        iface
                        for iface in network_info.get("interfaces", [])
                        if iface.get("is_up", False)
                    ]
                ),
                "bytes_sent": network_info.get("stats", {}).get("bytes_sent", 0),
                "bytes_received": network_info.get("stats", {}).get("bytes_recv", 0),
            },
        }

        return json.dumps(overview, indent=2)

    except Exception as e:
        logger.error(f"Error generating system overview: {e}")
        return json.dumps(
            {"error": f"Failed to generate system overview: {str(e)}"}, indent=2
        )


def get_system_processes() -> str:
    """Get current process list resource."""
    try:
        # Get process list with reasonable defaults for resource
        process_info = get_process_list(limit=25, sort_by="cpu")

        # Format for resource consumption
        processes_data = {
            "summary": {
                "total_processes": process_info.get("total_processes", 0),
                "showing_top": len(process_info.get("processes", [])),
                "sorted_by": "cpu_usage",
            },
            "processes": [
                {
                    "pid": proc["pid"],
                    "name": proc["name"],
                    "cpu_percent": proc["cpu_percent"],
                    "memory_percent": proc["memory_percent"],
                    "memory_mb": proc["memory_rss_mb"],
                    "username": proc["username"],
                    "status": proc["status"],
                }
                for proc in process_info.get("processes", [])
            ],
        }

        return json.dumps(processes_data, indent=2)

    except Exception as e:
        logger.error(f"Error generating process list resource: {e}")
        return json.dumps(
            {"error": f"Failed to generate process list: {str(e)}"}, indent=2
        )


# Resource URI mapping
RESOURCE_HANDLERS = {
    "system://overview": get_system_overview,
    "/system/overview": get_system_overview,
    "system://processes": get_system_processes,
    "/system/processes": get_system_processes,
}
