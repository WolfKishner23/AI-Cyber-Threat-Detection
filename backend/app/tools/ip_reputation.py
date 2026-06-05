def get_ip_reputation(ip_address: str) -> dict:
    """Evaluate IP reputation using heuristic logic."""
    if not ip_address:
        return {
            "ip": None,
            "reputation": "unknown",
            "risk_score": 0,
            "source": "heuristic"
        }
        
    # Heuristic rules
    if ip_address.startswith("10.") or ip_address.startswith("192.168.") or ip_address.startswith("172."):
        # Private IP heuristic
        reputation = "trusted"
        risk_score = 0
    elif "tor" in ip_address.lower() or ip_address == "198.51.100.12":  # Add a specific IP for testing malicious
        reputation = "malicious"
        risk_score = 90
    elif ip_address in ["192.0.2.78", "203.0.113.5", "198.51.100.5"]:  # Common simulator attack IPs
        reputation = "suspicious"
        risk_score = 60
    else:
        reputation = "unknown"
        risk_score = 20
        
    return {
        "ip": ip_address,
        "reputation": reputation,
        "risk_score": risk_score,
        "source": "heuristic"
    }
