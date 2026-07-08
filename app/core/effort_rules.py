from typing import Optional

def calculate_effort_rule(priority: Optional[str], complexity: Optional[str], business_value: Optional[str]) -> dict:
    priority = (priority or "LOW").strip().upper()
    complexity = (complexity or "Low").strip().capitalize()
    business_value = (business_value or "Low").strip().capitalize()
    
    # Normalize defaults just in case
    if priority not in ["LOW", "MEDIUM", "HIGH"]:
        priority = "LOW"
    if complexity not in ["Low", "Medium", "High"]:
        complexity = "Low"
    if business_value not in ["Low", "Medium", "High"]:
        business_value = "Low"
        
    # Matrix mapping
    # Format: matrix[complexity][priority] = (min, max)
    matrix = {
        "Low": {
            "LOW": (1, 2),
            "MEDIUM": (1, 3),
            "HIGH": (2, 4)
        },
        "Medium": {
            "LOW": (3, 5),
            "MEDIUM": (4, 7),
            "HIGH": (5, 9)
        },
        "High": {
            "LOW": (7, 10),
            "MEDIUM": (8, 12),
            "HIGH": (10, 15)
        }
    }
    
    min_days, max_days = matrix[complexity][priority]
    
    # Business value adjustment
    if business_value == "High":
        min_days += 1
        max_days += 1
        
    # Recommended effort (rounded midpoint)
    recommended_days = round((min_days + max_days) / 2.0)
    
    reason = f"Based on {priority} priority, {complexity} complexity, and {business_value} business value."
    if business_value == "High":
        reason += " Added +1 day buffer for high business value review/testing."
        
    return {
        "suggested_effort_min_days": min_days,
        "suggested_effort_max_days": max_days,
        "suggested_effort_recommended_days": recommended_days,
        "reason": reason,
        "warning": "Rule-based estimate only. Final effort should be confirmed by PM/Developer."
    }
