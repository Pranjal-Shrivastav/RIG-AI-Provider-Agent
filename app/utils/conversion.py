"""
Utility functions for unit conversions and human-readable string formatting.
"""

from typing import Union


def bytes_to_gb(bytes_val: Union[int, float]) -> float:
    """Convert bytes to Gigabytes (GB)."""
    return round(float(bytes_val) / (1024 ** 3), 2)


def bytes_to_mb(bytes_val: Union[int, float]) -> float:
    """Convert bytes to Megabytes (MB)."""
    return round(float(bytes_val) / (1024 ** 2), 2)


def bytes_to_human(bytes_val: Union[int, float]) -> str:
    """Convert bytes to human-readable string (B, KB, MB, GB, TB)."""
    val = float(bytes_val)
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if abs(val) < 1024.0:
            return f"{val:.2f} {unit}"
        val /= 1024.0
    return f"{val:.2f} PB"


def bps_to_mbps(bps_val: Union[int, float]) -> float:
    """Convert bytes per second to Megabits per second (Mbps)."""
    return round((float(bps_val) * 8.0) / (1000 * 1000), 2)


def format_uptime(seconds: Union[int, float]) -> str:
    """Format seconds into human-readable uptime (e.g., 2d 4h 12m)."""
    total_seconds = int(seconds)
    days, remainder = divmod(total_seconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, secs = divmod(remainder, 60)
    
    parts = []
    if days > 0:
        parts.append(f"{days}d")
    if hours > 0 or days > 0:
        parts.append(f"{hours}h")
    if minutes > 0 or hours > 0 or days > 0:
        parts.append(f"{minutes}m")
    parts.append(f"{secs}s")
    
    return " ".join(parts)
