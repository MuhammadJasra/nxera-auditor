# app.py — Nxera AI Auditor v4.2 (with ML Fraud Detection)

import streamlit as st
import pandas as pd
import subprocess
import difflib

from audit_logic import (
    normalise_df,
    run_audit,
    detect_red_flags,
    income_statement,
    cash_flow,
    balance_sheet,
    compliance_checks,
    llm_opinion,
    add_fraud_scores,
    get_advisory_messages  # ← NEW
)
from report_generator import generate_pdf_report
from fraud_model import shap_explain, shap_natural_language_explanation
from audit_rules import evaluate_rules

st.set_page_config(page_title="Nxera AI Auditor", page_icon="🧾", layout="centered")

# Initialize chat session
if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = []
if "chat_open" not in st.session_state:
    st.session_state.chat_open = False

# Sidebar: Branding, region selection, and info
with st.sidebar:
    st.image("https://em-content.zobj.net/source/microsoft-teams/363/receipt_1f9fe.png", width=64)
    st.markdown("# Nxera AI Auditor")
    st.markdown("Empowering transparency, automation & trust in financial systems.")
    region = st.selectbox(
        "Select Country / Region for Audit Standards",
        ["Pakistan (FBR)", "US (GAAP)", "UK (IFRS)"]
    )
    st.markdown("---")
    st.markdown("**How to use:**\n1. Upload your financial file.\n2. Review the automated audit.\n3. Download the PDF report.\n4. Ask the AI any audit question!")
    st.markdown("---")
    st.markdown("[View on GitHub](https://github.com/your-org/ai_auditor)")

# Floating chatbot button
col1, col2, col3, col4, col5 = st.columns([1, 1, 1, 1, 1])
with col5:
    if st.button("💬", help="Chat with AI Auditor", key="chat_button"):
        st.session_state.chat_open = not st.session_state.chat_open
        st.rerun()

st.title("🧾 Nxera — AI Auditor Agent")

def generate_ai_response(user_message):
    """Generate AI response based on user message and audit context"""
    user_message = user_message.lower()
    context = st.session_state.get('audit_context', {})
    
    if "help" in user_message:
        return "I can help you with:\n• Understanding audit results\n• Explaining compliance findings\n• Financial ratio analysis\n• Fraud risk assessment\n\nWhat would you like to know?"
    
    elif "compliance" in user_message:
        if context.get('compliance_count', 0) > 0:
            return f"You have {context['compliance_count']} compliance findings. I can help you understand each one and suggest corrective actions. Would you like me to explain the specific issues?"
        else:
            return "Great news! No compliance issues were detected in your audit. Your financial records appear to meet the standards for your selected region."
    
    elif "fraud" in user_message:
        return "I can help you understand fraud risk indicators in your data. The AI model analyzes transaction patterns, amounts, timing, and descriptions to identify potential fraud. Would you like me to explain the specific risk factors?"
    
    elif "improve" in user_message or "suggest" in user_message:
        return "Based on your audit results, here are some suggestions:\n• Review transactions with missing descriptions\n• Investigate weekend transactions\n• Consider implementing automated controls\n• Regular reconciliation of accounts\n\nWould you like me to elaborate on any of these?"
    
    elif "ratio" in user_message or "financial" in user_message:
        return "I can help you understand your financial ratios and what they mean for your business. The key ratios include:\n• Revenue to Expense ratio\n• Cash flow analysis\n• Profitability metrics\n\nWhat specific aspect would you like me to explain?"
    
    else:
        return "I'm here to help with your audit questions! I can explain findings, suggest improvements, and answer questions about financial reporting standards. What would you like to know?"

def try_read_csv(file):
    import io
    # Try default
    try:
        return pd.read_csv(file)
    except Exception:
        file.seek(0)
    # Try utf-8-sig
    try:
        return pd.read_csv(file, encoding='utf-8-sig')
    except Exception:
        file.seek(0)
    # Try semicolon delimiter
    try:
        return pd.read_csv(file, delimiter=';')
    except Exception:
        file.seek(0)
    # Try tab delimiter
    try:
        return pd.read_csv(file, delimiter='\t')
    except Exception:
        file.seek(0)
    # If all fail, show first few lines for debugging
    try:
        file.seek(0)
        lines = file.read(500)
        return None, lines
    except Exception:
        return None, None

def risk_badge(risk):
    if risk >= 90:
        color = '#d9534f'  # red
        label = 'Critical'
    elif risk >= 70:
        color = '#f0ad4e'  # orange
        label = 'High'
    elif risk >= 40:
        color = '#ffd700'  # yellow
        label = 'Medium'
    else:
        color = '#5cb85c'  # green
        label = 'Low'
    return f"<span style='background:{color};color:white;padding:2px 8px;border-radius:8px;font-size:0.9em'>{label}</span>"

# Multi-file upload for a single audit
uploaded_files = st.file_uploader("Upload one or more financial files (CSV or Excel) for this audit", type=["csv", "xlsx"], accept_multiple_files=True)
if uploaded_files:
    try:
        dfs = []
        file_names = []
        for file in uploaded_files:
            try:
                if file.name.lower().endswith(".csv"):
                    result = try_read_csv(file)
                    if isinstance(result, tuple):
                        df_raw, debug_lines = result
                    else:
                        df_raw, debug_lines = result, None
                else:
                    df_raw = pd.read_excel(file)
                    debug_lines = None
                if df_raw is not None and not df_raw.empty and len(df_raw.columns) > 0:
                    dfs.append(df_raw)
                    file_names.append(file.name)
            except Exception as e:
                st.warning(f"{file.name} could not be read: {e}")
        if not dfs:
            st.error("No valid files uploaded.")
            st.stop()
        # Combine all files into one DataFrame
        df_raw = pd.concat(dfs, ignore_index=True)
        st.info(f"Combined files: {', '.join(file_names)}")
        if df_raw is None or df_raw.empty or len(df_raw.columns) == 0:
            st.error("The uploaded files have no valid transactions.")
            st.stop()
        # Step 2: Data Preview & Smart Column Detection
        st.markdown("## 2️⃣ Preview & Validate Data")
        st.dataframe(df_raw, use_container_width=True)
        # Smart column detection
        possible_amount_cols = [c for c in df_raw.columns if difflib.get_close_matches(c.lower(), ["amount", "value", "amt", "debit", "credit"], n=1, cutoff=0.6)]
        amount_col = None
        if possible_amount_cols:
            amount_col = possible_amount_cols[0]
        else:
            amount_col = st.selectbox("Select the column representing transaction amount:", df_raw.columns, key="amount_col_select")
        st.info(f"Detected amount column: {amount_col}")
        # If both debit and credit columns exist, offer to combine
        debit_col = next((c for c in df_raw.columns if "debit" in c.lower()), None)
        credit_col = next((c for c in df_raw.columns if "credit" in c.lower()), None)
        if debit_col and credit_col:
            st.info(f"Detected debit column: {debit_col}, credit column: {credit_col}. Combining into single 'amount' column (credit - debit).")
            df_raw["amount"] = df_raw[credit_col].fillna(0) - df_raw[debit_col].fillna(0)
        elif amount_col != "amount":
            df_raw["amount"] = df_raw[amount_col]
        # Always coerce amount to numeric
        df_raw["amount"] = pd.to_numeric(df_raw["amount"], errors="coerce")
        # Ask user to confirm which sign means expense
        if (df_raw["amount"] < 0).sum() == 0 or (df_raw["amount"] > 0).sum() == 0:
            sign_convention = st.radio("How are expenses represented?", ["Negative numbers (e.g., -1000)", "Positive numbers (e.g., 1000)", "There is a separate column for type"], key="expense_sign_radio")
            if sign_convention == "Positive numbers (e.g., 1000)":
                df_raw["amount"] = -df_raw["amount"].abs()
            elif sign_convention == "There is a separate column for type":
                type_col = st.selectbox("Select the column indicating transaction type (expense/revenue):", df_raw.columns, key="type_col_select")
                expense_val = st.text_input("Value in that column that means 'expense':", value="expense", key="expense_val_input")
                df_raw.loc[df_raw[type_col].astype(str).str.lower() == expense_val.lower(), "amount"] = -df_raw["amount"].abs()
        df = normalise_df(df_raw)
        st.dataframe(df, use_container_width=True)
        if (df["amount"] < 0).sum() == 0:
            st.warning("No expenses detected! Please ensure expenses are negative values in your data. If your data uses a different convention, please adjust it above.")
        st.markdown("---")
        # Step 3: Audit Summary & Key Insights
        summary, issues = run_audit(df)
        red_flags = detect_red_flags(df)
        ratios = {
            "Total Revenue": df[df["amount"] > 0]["amount"].sum(),
            "Total Expenses": abs(df[df["amount"] < 0]["amount"].sum()),
            "Net Profit": df["amount"].sum(),
        }
        # Filter compliance findings by region
        all_compliance = compliance_checks(df)
        region_map = {
            "Pakistan (FBR)": "Pakistan FBR",
            "US (GAAP)": "US‑GAAP",
            "UK (IFRS)": "IFRS"
        }
        region_key = region_map.get(region, "US‑GAAP")
        compliance = [c for c in all_compliance if region_key in c.get("Standard", "")]
        col1, col2 = st.columns([2, 1])
        with col1:
            st.subheader("📋 Audit Summary")
            st.code(summary)
        with col2:
            st.subheader("📊 Key Financials")
            for k, v in ratios.items():
                st.markdown(f"<span style='font-size:1.2em'><b>{k}:</b> <span style='color:#007acc'>{v:,.2f}</span></span>", unsafe_allow_html=True)
        st.markdown(":bulb: **What does this mean?** Revenue is money coming in. Expenses are money going out. Net Profit = Revenue - Expenses.")
        st.markdown("---")
        # Step 4: Issues & Red Flags
        st.markdown("## 4️⃣ Issues & Red Flags")
        with st.expander("Audit Issues", expanded=True):
            if issues:
                for i, tbl in enumerate(issues, 1):
                    st.markdown(f"**Issue {i}**")
                    st.dataframe(tbl, use_container_width=True)
                    # Add plain-language explanation for each issue type
                    if tbl.equals(df[df.duplicated(subset=["date", "description", "amount"], keep=False)]):
                        st.info("Duplicate transaction: The same transaction appears more than once. This could be a data entry error or a duplicate upload.")
                    elif tbl.equals(df.sort_values("date")[df.sort_values("date")["date"].diff().dt.days > 30]):
                        st.info("Date gap: There is a long gap between transactions. This could mean missing data or periods with no activity.")
                    else:
                        st.info("Outlier: Some transactions are much larger or smaller than usual. This could be a mistake or an unusual event.")
            else:
                st.success("✅ No core audit issues detected.")
        with st.expander("Red Flag Warnings", expanded=False):
            if red_flags:
                for i, flagged in enumerate(red_flags, 1):
                    st.markdown(f"**Red Flag {i} — {flagged['Flag'].iloc[0]}**")
                    st.dataframe(flagged.drop(columns='Flag'), use_container_width=True)
                    # Add plain-language explanation for each red flag type
                    flag_type = flagged['Flag'].iloc[0] if 'Flag' in flagged.columns else ''
                    if flag_type == "Weekend":
                        st.info("Weekend entry: This transaction happened on a weekend, which is unusual for many businesses.")
                    elif flag_type == "Rounded cash":
                        st.info("Rounded amount: This is a large, round-number transaction (like -20,000). These can sometimes be used to hide fraud.")
                    elif flag_type == "Missing desc":
                        st.info("Missing description: This transaction has no description, making it hard to understand its purpose.")
                    else:
                        st.info("This is a potential red flag. Please review carefully.")
            else:
                st.success("✅ No red-flag patterns detected.")
        st.markdown(":bulb: **What does this mean?** Issues are potential problems found in your data. Red flags are patterns that may indicate risk or fraud. Each explanation above is written in plain language for clarity.")
        st.markdown("---")
        # Step 5: ML Fraud Risk Table
        st.markdown("## 5️⃣ ML Fraud Risk Table")
        # Highlight 0% risk transactions if they have red flags
        flagged_indices = set()
        for flagged in red_flags or []:
            flagged_indices.update(flagged.index.tolist())
        def highlight_row(row):
            if row["Fraud\u202fRisk\u202f%"] == 0.0 and row.name in flagged_indices:
                return ["background-color: #f0ad4e; color: black"] * len(row)
            return [""] * len(row)
        df_scores_disp = add_fraud_scores(df).copy()
        df_scores_disp['Risk Level'] = df_scores_disp["Fraud\u202fRisk\u202f%"].apply(lambda x: risk_badge(x))
        # Only show transactions with Fraud Risk % >= 40
        at_risk_df = df_scores_disp[df_scores_disp["Fraud\u202fRisk\u202f%"] >= 40]
        st.markdown("Fraud risk is color-coded for quick review. Only transactions with Medium or higher risk (≥ 40%) are shown:", help="Red=Critical, Orange=High, Yellow=Medium, Green=Low, Orange row=0% risk but red flag present")
        st.write(at_risk_df.style.apply(highlight_row, axis=1).to_html(escape=False, index=False), unsafe_allow_html=True)
        st.markdown(":bulb: **What does this mean?** The AI model estimates the risk of fraud for each transaction. High risk means more likely to be problematic.")
        st.markdown("---")
        # Step 4: AI Audit Opinion (LLM)
        st.markdown("## 4️⃣ AI Audit Opinion & Explanation")
        opinion = llm_opinion(summary, ratios, compliance, region=region)
        st.info(opinion)
        st.markdown(":bulb: **What does this mean?** This is a plain-language summary and risk assessment generated by the AI, based on your data and compliance checks.")
        st.markdown("---")
        # Step 7: Financial Statements
        st.markdown("## 7️⃣ Financial Statements & Compliance")
        with st.expander("Income Statement"):
            st.dataframe(income_statement(df), use_container_width=True)
        with st.expander("Cash Flow Statement"):
            st.dataframe(cash_flow(df), use_container_width=True)
        with st.expander("Balance Sheet Estimate"):
            st.dataframe(balance_sheet(df), use_container_width=True)
        with st.expander("Compliance Flags"):
            st.json(compliance)
        st.markdown(":bulb: **What does this mean?** These are standard financial reports. Income Statement shows profit/loss. Cash Flow shows money movement. Balance Sheet shows assets/liabilities.")
        st.markdown("---")
        # Step 8: Download Report
        st.markdown("## 8️⃣ Download Full PDF Report")
        test_pdf_mode = st.checkbox("Test PDF generation with minimal data (for debugging)")
        if st.button("📄 Download PDF Report"):
            all_tables = issues + red_flags
            high_risk = df_scores_disp[df_scores_disp["Fraud\u202fRisk\u202f%"] >= 70]
            if not high_risk.empty:
                high_risk["Flag"] = "ML Fraud‑Risk ≥ 70%"
                all_tables += [high_risk]
            # Prepare ML fraud table and advisory notes
            ml_fraud_table = at_risk_df
            advisory_notes = get_advisory_messages(df, region=region)
            # Get company name and period from data or user
            company_name = st.text_input("Company Name for Report:", value="[Company Name]", key="company_name_pdf")
            period = st.text_input("Period (e.g., FY 2023) for Report:", value="[Period]", key="period_pdf")
            try:
                if test_pdf_mode:
                    # Minimal PDF: only summary and placeholder text
                    pdf_bytes = generate_pdf_report(
                        summary,
                        [],
                        "Test Opinion",
                        {},
                        inc=None,
                        cf=None,
                        bs=None,
                        compliance=[],
                        ml_fraud_table=None,
                        red_flags=[],
                        advisory_notes=["Test advisory note"],
                        company_name=company_name,
                        period=period
                    )
                else:
                    pdf_bytes = generate_pdf_report(
                        summary,
                        all_tables,
                        llm_opinion(summary, ratios, compliance, region=region),
                        ratios,
                        income_statement(df),
                        cash_flow(df),
                        balance_sheet(df),
                        compliance,
                        ml_fraud_table=ml_fraud_table,
                        red_flags=red_flags,
                        advisory_notes=advisory_notes,
                        company_name=company_name,
                        period=period
                    )
                st.download_button(
                    "💾 Save Full Audit Report",
                    data=pdf_bytes,
                    file_name="nxera_audit_report.pdf",
                    mime="application/pdf",
                )
            except Exception as e:
                st.error(f"PDF generation failed: {e}")
        st.markdown(":bulb: **What does this mean?** Download a full, professional audit report for your records or to share with others.")
        st.markdown("---")
        # Step 9: AI Chat Integration
        # Store audit context for chatbot
        st.session_state.audit_context = {
            'summary': summary,
            'compliance_count': len(compliance),
            'region': region,
            'has_data': True
        }
    except Exception as e:
        st.exception(e)
else:
    st.info("📂 Please upload one or more CSV or Excel files to begin auditing.")

# Chat window (appears when chat is open)
if st.session_state.chat_open:
    st.markdown("---")
    st.markdown("### 🤖 AI Auditor Chat")
    
    # Chat container with border
    chat_container = st.container()
    with chat_container:
        st.markdown("""
        <style>
        .chat-container {
            border: 2px solid #007acc;
            border-radius: 10px;
            padding: 20px;
            background-color: #f8f9fa;
            margin: 10px 0;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Show chat history
        if st.session_state.chat_messages:
            for message in st.session_state.chat_messages:
                if message["role"] == "user":
                    st.markdown(f"**You:** {message['content']}")
                else:
                    st.markdown(f"**AI:** {message['content']}")
        else:
            st.info("Hello! I'm your AI Auditor assistant. Ask me anything about your audit, compliance, or financial data!")
        
        # Chat input
        col1, col2 = st.columns([4, 1])
        with col1:
            user_input = st.text_input("Ask me about your audit:", key="chat_input", placeholder="Type your question here...")
        with col2:
            if st.button("Send", key="send_button") and user_input:
                # Add user message
                st.session_state.chat_messages.append({"role": "user", "content": user_input})
                
                # Generate AI response
                ai_response = generate_ai_response(user_input)
                st.session_state.chat_messages.append({"role": "assistant", "content": ai_response})
                
                # Rerun to show new messages
                st.rerun()