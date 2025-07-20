# compliance_engine.py  — Nxera Compliance Rules v2.0 (Extended Ruleset)
from __future__ import annotations
from dataclasses import dataclass
from typing import List, Dict, Callable
import pandas as pd
import re
import json
import os

@dataclass
class Rule:
    id: str
    standard: str
    clause: str
    description: str
    severity: str
    check: Callable[[pd.DataFrame], bool]
    sample: Callable[[pd.DataFrame], pd.DataFrame]

def build_catalogue() -> List[Rule]:
    rules: List[Rule] = []

    # ───────── IFRS Rules ─────────

    rules.append(Rule(
        id="IFRS15_NEGREV",
        standard="IFRS‑15",
        clause="9",
        description="Revenue recorded as negative",
        severity="High",
        check=lambda df: bool((df[df.amount > 0]["amount"] < 0).any()),
        sample=lambda d: pd.DataFrame(d[(d.amount > 0) & (d.amount < 0)])
    ))

    rules.append(Rule(
        id="IFRS16_LEASE_DESC",
        standard="IFRS‑16",
        clause="24",
        description="Potential lease expenses found",
        severity="Med",
        check=lambda df: bool(df.description.str.contains("lease", case=False, na=False).any()),
        sample=lambda d: pd.DataFrame(d[d.description.str.contains("lease", case=False, na=False)])
    ))

    # ───────── GAAP Rules ─────────

    rules.append(Rule(
        id="ASC606_UNEARNED",
        standard="US‑GAAP ASC‑606",
        clause="45‑1",
        description="Line item indicates unearned revenue",
        severity="Med",
        check=lambda df: bool(df.description.str.contains("unearned", flags=re.I, na=False).any()),
        sample=lambda df: pd.DataFrame(df[df.description.str.contains("unearned", flags=re.I, na=False)])
    ))

    rules.append(Rule(
        id="GAAP_RND_NUMBERS",
        standard="US‑GAAP",
        clause="240",
        description="Rounded amounts indicating potential fraud",
        severity="High",
        check=lambda df: bool(((df.amount % 1000 == 0) & (abs(df.amount) > 20000)).any()),
        sample=lambda df: pd.DataFrame(df[(df.amount % 1000 == 0) & (abs(df.amount) > 20000)])
    ))

    # ───────── ISA Rules ─────────

    rules.append(Rule(
        id="ISA240_ROUNDED",
        standard="ISA‑240",
        clause="32(a)",
        description="Rounded cash withdrawals > 20,000",
        severity="High",
        check=lambda d: bool(((d.amount < 0) & (abs(d.amount) % 1000 == 0) & (abs(d.amount) > 20000)).any()),
        sample=lambda d: pd.DataFrame(d[(d.amount < 0) & (abs(d.amount) % 1000 == 0) & (abs(d.amount) > 20000)])
    ))

    rules.append(Rule(
        id="ISA500_MISSING_DESC",
        standard="ISA‑500",
        clause="A12",
        description="Transactions missing descriptions",
        severity="High",
        check=lambda d: bool(d.description.isna().any() or (d.description == "").any()),
        sample=lambda d: pd.DataFrame(d[d.description.isna() | (d.description == "")])
    ))

    rules.append(Rule(
        id="ISA530_SAME_AMOUNT_DUPES",
        standard="ISA‑530",
        clause="B9",
        description="Duplicate amounts with same description",
        severity="Med",
        check=lambda d: bool(d.duplicated(subset=["amount", "description"], keep=False).any()),
        sample=lambda d: pd.DataFrame(d[d.duplicated(subset=["amount", "description"], keep=False)])
    ))

    # ───────── Local Rules (Pakistan FBR) ─────────

    rules.append(Rule(
        id="PK_FBR_500K",
        standard="Pakistan FBR",
        clause="SRO‑586(2017)",
        description="Single payment > 500,000 must be documented",
        severity="Med",
        check=lambda d: bool((abs(d["amount"]) > 500000).any()),
        sample=lambda d: pd.DataFrame(d[abs(d["amount"]) > 500000])
    ))

    rules.append(Rule(
        id="PK_FBR_WEEKEND_TXNS",
        standard="Pakistan FBR",
        clause="2022 Circular",
        description="Transactions recorded on weekends",
        severity="Low",
        check=lambda d: bool(pd.to_datetime(d.date).dt.dayofweek.isin([5,6]).any()),
        sample=lambda d: pd.DataFrame(d[pd.to_datetime(d.date).dt.dayofweek.isin([5,6])])
    ))

    # ───────── Materiality & Common Audit Rules ─────────

    rules.append(Rule(
        id="MAT_EXP_5PCT",
        standard="ISA‑320",
        clause="10",
        description="Single expense >5 % of total revenue",
        severity="Low",
        check=lambda df: bool(not df[(df.amount < 0) & (abs(df.amount) > 0.05 * df[df.amount > 0]["amount"].sum())].empty),
        sample=lambda d: pd.DataFrame(d[(d.amount < 0) & (abs(d.amount) > 0.05 * d[d.amount > 0]["amount"].sum())])
    ))

    return rules

# Load compliance rules knowledge base
RULES_JSON_PATH = os.path.join(os.path.dirname(__file__), 'compliance_rules.json')
with open(RULES_JSON_PATH, 'r', encoding='utf-8') as f:
    LAW_KB = {entry['id']: entry for entry in json.load(f)}

def get_referenced_standards(jurisdiction=None):
    """
    Return all standards for a given jurisdiction (or all if None).
    """
    if jurisdiction:
        return [v for v in LAW_KB.values() if jurisdiction.lower() in v['jurisdiction'].lower()]
    return list(LAW_KB.values())


def evaluate(df: pd.DataFrame) -> List[Dict[str, str]]:
    catalogue = build_catalogue()
    findings: List[Dict[str, str]] = []
    referenced_standards = set()
    for rule in catalogue:
        kb = LAW_KB.get(rule.id)
        try:
            if rule.check(df):
                rows = rule.sample(df)
                finding = {
                    "Rule": rule.id,
                    "Standard": rule.standard,
                    "Clause": rule.clause,
                    "Severity": rule.severity,
                    "Detail": f"{len(rows)} offending rows" if not rows.empty else "Breach detected"
                }
                if kb:
                    finding.update({
                        "LawStandard": kb.get("law_standard"),
                        "Jurisdiction": kb.get("jurisdiction"),
                        "LawDescription": kb.get("description"),
                        "Applicability": kb.get("applicability")
                    })
                findings.append(finding)
        except Exception as e:
            finding = {
                "Rule": rule.id,
                "Standard": rule.standard,
                "Clause": rule.clause,
                "Severity": rule.severity,
                "Detail": f"[Engine Error] {str(e)}"
            }
            if kb:
                finding.update({
                    "LawStandard": kb.get("law_standard"),
                    "Jurisdiction": kb.get("jurisdiction"),
                    "LawDescription": kb.get("description"),
                    "Applicability": kb.get("applicability")
                })
            findings.append(finding)
        # Track referenced standards for reporting
        if kb and not kb.get('automatable', True):
            referenced_standards.add(rule.id)
    # Optionally, return referenced standards for reporting
    return findings
