# audit_logic.py  — Phase 7: Full Statements + Rule‑Based Compliance Engine + Deep Opinion
from __future__ import annotations
import pandas as pd, subprocess
from typing import List, Tuple, Dict
from compliance_engine import evaluate as compliance_checks
from fraud_model import score_transactions

def add_fraud_scores(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["Fraud\u202fRisk\u202f%"] = score_transactions(df)
    return df


# ───── Normalise ───────────────────────────────────────────
def normalise_df(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [c.lower().strip() for c in df.columns]
    alias = {
        "transaction_date": "date", "trans_date": "date",
             "details": "description", "desc": "description",
        "value": "amount", "amt": "amount", "amount": "amount"
    }
    df.rename(columns={k: v for k, v in alias.items() if k in df.columns}, inplace=True)
    # Remove duplicate columns, keep first
    df = df.loc[:, ~df.columns.duplicated()]
    if not {"date", "description", "amount"}.issubset(df.columns):
        raise ValueError(f"Your data must have columns for date, description, and amount. Found: {df.columns.tolist()}")
    # Ensure each column is a Series, not DataFrame
    for col in ["date", "description", "amount"]:
        if isinstance(df[col], pd.DataFrame):
            df[col] = df[col].iloc[:, 0]
    df = pd.DataFrame(df[["date", "description", "amount"]])
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce")
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df.dropna(subset=["date", "amount"], inplace=True)
    df = df.sort_values("date").reset_index(drop=True)
    return df


# ───── Core Audit & Red‑Flags ──────────────────────────────
def run_audit(df: pd.DataFrame) -> Tuple[str, List[pd.DataFrame]]:
    issues: List[pd.DataFrame] = []
    dup = df[df.duplicated(subset=["date", "description", "amount"], keep=False)]
    if not dup.empty:
        if isinstance(dup, pd.Series):
            dup = dup.to_frame().T
        issues.append(dup)
    df_sorted = df.sort_values("date")
    gaps = df_sorted[df_sorted["date"].diff().dt.days > 30]
    if not gaps.empty:
        if isinstance(gaps, pd.Series):
            gaps = gaps.to_frame().T
        issues.append(gaps)
    mu, sd = df["amount"].mean(), df["amount"].std()
    out = df[(df["amount"] > mu + 3*sd) | (df["amount"] < mu - 3*sd)]
    if not out.empty:
        if isinstance(out, pd.Series):
            out = out.to_frame().T
        issues.append(out)
    summary = (f"Txns {len(df)}, Rev {df[df.amount>0]['amount'].sum():,.0f}, "
               f"Exp {df[df.amount<0]['amount'].sum():,.0f}, Issues {len(issues)}")
    return summary, issues


def detect_red_flags(df: pd.DataFrame) -> List[pd.DataFrame]:
    flags: List[pd.DataFrame] = []
    d = df.copy(); d["date"] = pd.to_datetime(d["date"])
    wknd = d[d.date.dt.dayofweek >= 5]
    if not wknd.empty:
        if isinstance(wknd, pd.Series):
            wknd = wknd.to_frame().T
        wknd = wknd.copy()
        wknd["Flag"] = "Weekend"
        flags.append(wknd)
    rounded = d[(d.amount < 0) & (d.amount % 1000 == 0) & (abs(d.amount) > 20000)]
    if not rounded.empty:
        if isinstance(rounded, pd.Series):
            rounded = rounded.to_frame().T
        rounded = rounded.copy()
        rounded["Flag"] = "Rounded cash"
        flags.append(rounded)
    blank = d[d.description.isna() | (d.description.str.strip()=="")]
    if not blank.empty:
        if isinstance(blank, pd.Series):
            blank = blank.to_frame().T
        blank = blank.copy()
        blank["Flag"] = "Missing desc"
        flags.append(blank)
    return flags


# ───── Financial Statements ───────────────────────────────
def _month(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy(); df["date"] = pd.to_datetime(df["date"])
    df["month"] = df.date.dt.to_period("M"); return df

def income_statement(df: pd.DataFrame) -> pd.DataFrame:
    d = _month(df)
    d["bucket"] = d.amount.apply(lambda x:"Revenue" if x>0 else "Expense")
    tbl = d.groupby(["month","bucket"])["amount"].sum().unstack(fill_value=0)
    revenue = tbl["Revenue"] if "Revenue" in tbl.columns else pd.Series(0.0, index=tbl.index)
    expense = tbl["Expense"] if "Expense" in tbl.columns else pd.Series(0.0, index=tbl.index)
    tbl["Net Profit"] = revenue + expense
    gross_margin = tbl["Net Profit"] / revenue
    if not isinstance(gross_margin, pd.Series):
        gross_margin = pd.Series(gross_margin, index=tbl.index)
    gross_margin = gross_margin.apply(lambda x: 0.0 if pd.isna(x) or x in [float("inf"), -float("inf")] else x)
    tbl["Gross Margin %"] = gross_margin
    return tbl.reset_index().astype({"month": str}).round(2)

def cash_flow(df: pd.DataFrame) -> pd.DataFrame:
    d=_month(df)
    inflow=d[d.amount>0].groupby("month")["amount"].sum()
    out=d[d.amount<0].groupby("month")["amount"].sum()
    cf=pd.DataFrame({"Inflow":inflow,"Outflow":out}).fillna(0.0)
    cf["Net"] = cf["Inflow"] + cf["Outflow"]
    return cf.reset_index().astype({"month":str}).round(2)

def balance_sheet(df: pd.DataFrame) -> pd.DataFrame:
    rev = df[df.amount>0]["amount"].sum()
    exp = abs(df[df.amount<0]["amount"].sum())
    cash = df["amount"].sum()
    equity = rev - exp
    return pd.DataFrame({"Metric":["Revenue","Expense","Cash","Equity"],
                         "Value":[rev,exp,cash,equity]}).round(2)


# ───── Deep LLM Opinion (risks + actions) ────────────────
def llm_opinion(summary:str, ratios:Dict[str,float], compliance:List[Dict[str,str]], region:str="US (GAAP)") -> str:
    # Add law/standard context to the compliance string
    comp = "; ".join(f"{c['Rule']} ({c['LawStandard']})" if c.get('LawStandard') else f"{c['Rule']}" for c in compliance) or "None"
    prompt = ("You are a senior CPA. Based on this summary, ratios and compliance flags, "
              f"write an executive audit opinion with 3 risks and 3 actionable suggestions.\n"
              f"SUMMARY: {summary}\n RATIOS: {ratios}\n COMPLIANCE: {comp}\n"
              f"REGION: {region}. Please ensure your opinion and suggestions are tailored to the selected region's standards and reference relevant laws/standards where appropriate.")
    try:
        res=subprocess.run(["ollama","run","mistral",prompt],capture_output=True,text=True,timeout=20)
        return res.stdout.strip()
    except Exception as e:
        return f"[LLM error] {e}"

def get_advisory_messages(df: pd.DataFrame, region: str = "US (GAAP)") -> list:
    """
    Return a list of advisory messages based on accounting rules and internal control checks, region-aware.
    """
    messages = []
    # Example: Revenue recognition policy
    if (df["amount"] > 0).sum() > 0 and (df["amount"] < 0).sum() > 0:
        if region == "Pakistan (FBR)":
            messages.append("[FBR] Ensure revenue and expenses are matched as per FBR standards.")
        elif region == "UK (IFRS)":
            messages.append("[IFRS] Review your revenue recognition policy for compliance with IFRS 15.")
        else:
            messages.append("[GAAP] You may need to update your revenue recognition policy if revenue and expenses are not matched in the same period.")
    # Example: Repeated weekend entries
    if "date" in df.columns:
        weekend_count = pd.to_datetime(df["date"]).dt.dayofweek.isin([5,6]).sum()
        if weekend_count > 3:
            messages.append("Repeated weekend entries suggest poor internal controls.")
    # Add more region-specific rules as needed
    if not messages:
        messages.append("No major advisory issues detected.")
    return messages
