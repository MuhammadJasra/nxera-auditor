import pandas as pd
from typing import List, Dict, Callable

class AuditRule:
    def __init__(self, region: str, description: str, severity: str, check: Callable[[pd.DataFrame], bool], suggestion: str = ""):
        self.region = region
        self.description = description
        self.severity = severity
        self.check = check
        self.suggestion = suggestion

# Example rules (expand as needed)
rules = [
    # Revenue recognition (all regions)
    AuditRule(
        region="ALL",
        description="Revenue and expenses should be matched in the same period (matching principle)",
        severity="High",
        check=lambda df: not ((df["amount"] > 0).sum() > 0 and (df["amount"] < 0).sum() > 0),
        suggestion="Review your revenue recognition and expense matching policies."
    ),
    # Segregation of duties (all regions)
    AuditRule(
        region="ALL",
        description="No single user should control all aspects of a transaction (segregation of duties)",
        severity="High",
        check=lambda df: True,  # Placeholder: needs user/role data
        suggestion="Implement segregation of duties in your accounting system."
    ),
    # Authorization controls (all regions)
    AuditRule(
        region="ALL",
        description="All transactions should be properly authorized",
        severity="Medium",
        check=lambda df: True,  # Placeholder: needs authorization data
        suggestion="Ensure all transactions are authorized by appropriate personnel."
    ),
    # Weekend entries (internal control)
    AuditRule(
        region="ALL",
        description="Unusual number of weekend entries detected",
        severity="Medium",
        check=lambda df: pd.to_datetime(df["date"]).dt.dayofweek.isin([5,6]).sum() <= 3,
        suggestion="Investigate repeated weekend entries for possible control weaknesses."
    ),
    # Rounded amounts (fraud red flag)
    AuditRule(
        region="ALL",
        description="Unusual number of round-amount transactions detected",
        severity="Medium",
        check=lambda df: (df["amount"] % 1000 == 0).sum() <= 2,
        suggestion="Review round-amount transactions for possible manipulation."
    ),
    # Region-specific: FBR (Pakistan)
    AuditRule(
        region="Pakistan (FBR)",
        description="Ensure compliance with FBR withholding tax rules",
        severity="High",
        check=lambda df: True,  # Placeholder: needs tax data
        suggestion="Verify withholding tax compliance as per FBR regulations."
    ),
    # Region-specific: US GAAP
    AuditRule(
        region="US (GAAP)",
        description="ASC 606: Revenue from Contracts with Customers",
        severity="High",
        check=lambda df: True,  # Placeholder: needs contract data
        suggestion="Ensure revenue recognition follows ASC 606."
    ),
    # Region-specific: UK IFRS
    AuditRule(
        region="UK (IFRS)",
        description="IFRS 15: Revenue from Contracts with Customers",
        severity="High",
        check=lambda df: True,  # Placeholder: needs contract data
        suggestion="Ensure revenue recognition follows IFRS 15."
    ),
]

def evaluate_rules(df: pd.DataFrame, region: str) -> List[Dict]:
    results = []
    for rule in rules:
        if rule.region == "ALL" or rule.region == region:
            passed = rule.check(df)
            results.append({
                "Region": rule.region,
                "Description": rule.description,
                "Severity": rule.severity,
                "Passed": passed,
                "Suggestion": rule.suggestion if not passed else ""
            })
    return results 