import re

def estimate_strength(password: str) -> dict:
    score = 0
    if len(password) >= 12: score += 20
    if re.search(r"[a-z]", password): score += 15
    if re.search(r"[A-Z]", password): score += 15
    if re.search(r"\d", password): score += 15
    if re.search(r"[!@#$%^&*()_+\-=\[\]{};':\"\\|,.<>\/?]", password): score += 15
    if len(set(password)) >= 8: score += 20
    
    if score >= 90: label = "Very Strong"
    elif score >= 70: label = "Strong"
    elif score >= 50: label = "Medium"
    elif score >= 30: label = "Weak"
    else: label = "Very Weak"
    
    return {"score": min(score, 100), "label": label}

def is_weak_password(password: str) -> bool:
    return estimate_strength(password)["score"] < 50