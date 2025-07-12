# app.py — Nxera AI Auditor v4.1 (Final)

import streamlit as st
import pandas as pd

from audit_logic import (
    normalise_df,
    run_audit,
    detect_red_flags,
    income_statement,
    cash_flow,
    balance_sheet,
    compliance_checks,
    llm_opinion,
)
from report_generator import generate_pdf_report

st.set_page_config(page_title="Nxera AI Auditor", page_icon="🧾", layout="centered")
st.title("🧾 Nxera — AI Auditor Agent")

uploaded_file = st.file_uploader("Upload your financial file (CSV or Excel)", type=["csv", "xlsx"])

if uploaded_file:
    try:
        # ── 1. Load and normalize file ───────────────
        if uploaded_file.name.lower().endswith(".csv"):
            df_raw = pd.read_csv(uploaded_file)
        else:
            df_raw = pd.read_excel(uploaded_file)

        df = normalise_df(df_raw)
        if df.empty:
            st.error("The uploaded file has no valid transactions.")
            st.stop()

        st.success(f"✅ Loaded {len(df):,} transactions.")
        st.subheader("📄 Uploaded Transactions")
        st.dataframe(df, use_container_width=True)

        # ── 2. Run Audit Logic ───────────────────────
        summary, issues = run_audit(df)
        red_flags = detect_red_flags(df)

        ratios = {
            "Total Revenue": df[df["amount"] > 0]["amount"].sum(),
            "Total Expenses": abs(df[df["amount"] < 0]["amount"].sum()),
            "Net Profit": df["amount"].sum(),
        }

        # ── 3. Financials + Compliance ───────────────
        inc = income_statement(df)
        cf = cash_flow(df)
        bs = balance_sheet(df)
        compliance = compliance_checks(df)

        # ── 4. LLM Audit Opinion ─────────────────────
        opinion = llm_opinion(summary, ratios, compliance)

        # ── 5. Display Results ───────────────────────
        st.subheader("📋 Summary")
        st.code(summary)

        st.subheader("📊 Financial Ratios")
        for k, v in ratios.items():
            st.markdown(f"**{k}**: {v:,.2f}")

        st.subheader("🧠 AI Audit Opinion (via Mistral)")
        st.markdown(opinion)

        st.subheader("⚠️ Audit Issues")
        if issues:
            for i, tbl in enumerate(issues, 1):
                st.markdown(f"**Issue {i}**")
                st.dataframe(tbl, use_container_width=True)
        else:
            st.success("✅ No core audit issues detected.")

        st.subheader("🚨 Red Flag Warnings")
        if red_flags:
            for i, flagged in enumerate(red_flags, 1):
                st.markdown(f"**Red Flag {i} — {flagged['Flag'].iloc[0]}**")
                st.dataframe(flagged.drop(columns='Flag'), use_container_width=True)
        else:
            st.success("✅ No red-flag patterns detected.")

        # ── 6. Financial Statements + Compliance ─────
        st.subheader("📊 Financial Statements")

        with st.expander("Income Statement"):
            st.dataframe(inc, use_container_width=True)

        with st.expander("Cash Flow Statement"):
            st.dataframe(cf, use_container_width=True)

        with st.expander("Balance Sheet Estimate"):
            st.dataframe(bs, use_container_width=True)

        with st.expander("Compliance Flags"):
            st.json(compliance)

        # ── 7. PDF Report Export ─────────────────────
        if st.button("📄 Download PDF Report"):
            all_tables = issues + red_flags
            pdf_bytes = generate_pdf_report(summary, all_tables, opinion, ratios, inc, cf, bs, compliance)
            st.download_button(
                "💾 Save Full Audit Report",
                data=pdf_bytes,
                file_name="nxera_audit_report.pdf",
                mime="application/pdf",
            )

    except Exception as e:
        st.exception(e)

else:
    st.info("📂 Please upload a CSV or Excel file to begin auditing.")
