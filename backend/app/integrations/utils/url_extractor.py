"""
URL extraction utilities for different tunnel providers
"""
import re
from typing import Optional


def extract_cloudflare_url(logs: str) -> Optional[str]:
    """
    Extract Cloudflare tunnel URL from container logs.
    Format: https://xxxxx.trycloudflare.com
    """
    try:
        for line in logs.split("\n"):
            # Match trycloudflare.com URLs
            pattern = r"https://[a-zA-Z0-9-]+\.trycloudflare\.com"
            matches = re.findall(pattern, line)
            if matches:
                return matches[0]
    except Exception:
        pass
    return None


def extract_ngrok_url(logs: str) -> Optional[str]:
    """
    Extract Ngrok tunnel URL from container logs.
    Format: https://xxxxx.ngrok-free.app or https://xxxxx.ngrok.app
    """
    try:
        for line in logs.split("\n"):
            # Match ngrok URLs (free and paid)
            pattern = r"https://[a-zA-Z0-9-]+\.ngrok(?:-free)?\.app"
            matches = re.findall(pattern, line)
            if matches:
                return matches[0]
            
            # Also try ngrok.io (older format)
            pattern_old = r"https://[a-zA-Z0-9-]+\.ngrok\.io"
            matches = re.findall(pattern_old, line)
            if matches:
                return matches[0]
    except Exception:
        pass
    return None


def extract_pinggy_url(logs: str) -> Optional[str]:
    """
    Extract Pinggy tunnel URL from container logs.
    Format: https://xxxxx-xxx-xxx-xxx-xxx.a.free.pinggy.link
    """
    try:
        for line in logs.split("\n"):
            # Match Pinggy free URLs
            pattern = r"https?://[a-zA-Z0-9-]+\.a\.free\.pinggy\.link"
            matches = re.findall(pattern, line)
            if matches:
                return matches[0]
            
            # Match Pinggy paid URLs
            pattern_pro = r"https?://[a-zA-Z0-9-]+\.a\.pinggy\.link"
            matches = re.findall(pattern_pro, line)
            if matches:
                return matches[0]
            
            # TCP format
            tcp_pattern = r"tcp://[a-zA-Z0-9-]+\.a\.(?:free\.)?pinggy\.link:\d+"
            matches = re.findall(tcp_pattern, line)
            if matches:
                return matches[0]
    except Exception:
        pass
    return None


def extract_url_by_provider(provider: str, logs: str) -> Optional[str]:
    """
    Extract tunnel URL based on provider type.
    
    Args:
        provider: Provider name (cloudflare, ngrok, pinggy)
        logs: Container logs to parse
        
    Returns:
        Extracted URL or None
    """
    provider_lower = provider.lower()
    
    if provider_lower == "cloudflare":
        return extract_cloudflare_url(logs)
    elif provider_lower == "ngrok":
        return extract_ngrok_url(logs)
    elif provider_lower == "pinggy":
        return extract_pinggy_url(logs)
    
    return None
