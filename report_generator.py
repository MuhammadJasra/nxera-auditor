# report_generator.py — Final version with full audit, ratios, statements, and compliance

import io
from typing import List, Dict
import pandas as pd
from xhtml2pdf import pisa


def generate_pdf_report(
    summary: str,
    issues: list,
    opinion: str,
    ratios: dict = {},
    inc=None,
    cf=None,
    bs=None,
    compliance=None,
    ml_fraud_table=None,
    red_flags=None,
    advisory_notes=None,
    company_name: str = "[Company Name]",
    period: str = "[Period]"
) -> bytes:
    """
    Generate a full, professional audit PDF report with Nxera branding and all standard audit sections.
    """
    html_parts = [
        "<html><head><style>",
        """
        @page { size: A4; margin: 50px; }
        body { font-family: Arial, sans-serif; font-size: 12px; color: #333; }
        header { border-bottom: 2px solid #007acc; padding-bottom: 10px; margin-bottom: 20px; }
        footer { position: fixed; bottom: 30px; left: 0; right: 0; text-align: center; font-size: 10px; color: #777; }
        h1, h2, h3 { color: #007acc; }
        table { width: 100%; border-collapse: collapse; margin-top: 10px; margin-bottom: 20px; }
        th, td { border: 1px solid #ccc; padding: 8px; text-align: left; }
        th { background-color: #f0f8ff; }
        ul { margin-top: 0; }
        .section { margin-bottom: 32px; }
        .cover { text-align: center; margin-top: 100px; }
        .opinion { font-style: italic; margin: 20px 0; }
        .advisory { background: #f9f9e3; border-left: 4px solid #ffd700; padding: 10px; margin: 10px 0; }
        .ml-section { background: #f0f8ff; border-left: 4px solid #007acc; padding: 10px; margin: 10px 0; }
        """,
        "</style></head><body>",
        # Cover Page
        f"<div class='cover'><h1>Independent Audit Report</h1><h2>{company_name}</h2><h3>For the period ended {period}</h3><p>Prepared by Nxera AI Auditor</p></div>",
        "<div class='section'><h2>Table of Contents</h2><ol>"
        "<li>Auditor’s Opinion</li>"
        "<li>Executive Summary</li>"
        "<li>Financial Statements</li>"
        "<li>Compliance & Internal Controls</li>"
        "<li>ML/AI Fraud Risk Analysis</li>"
        "<li>Red Flags & Anomalies</li>"
        "<li>Advisory Notes</li>"
        "<li>Appendices</li>"
        "</ol></div>",
        # Auditor's Opinion
        "<div class='section'><h2>1. Auditor’s Opinion</h2>",
        f"<div class='opinion'>{opinion}</div></div>",
        # Executive Summary
        "<div class='section'><h2>2. Executive Summary</h2>",
        f"<pre>{summary}</pre></div>",
        # Financial Statements
        "<div class='section'><h2>3. Financial Statements</h2>",
        "<h3>Income Statement</h3>",
        inc.to_html(index=False, escape=False) if inc is not None else "",
        "<h3>Cash Flow Statement</h3>",
        cf.to_html(index=False, escape=False) if cf is not None else "",
        "<h3>Balance Sheet Estimate</h3>",
        bs.to_html(index=False, escape=False) if bs is not None else "",
        "</div>",
        # Compliance & Internal Controls
        "<div class='section'><h2>4. Compliance & Internal Controls</h2>",
        "<table><tr><th>Rule ID</th><th>Standard</th><th>Clause</th><th>Description</th><th>Severity</th><th>Breach Count</th><th>Law/Standard</th><th>Jurisdiction</th><th>Law Description</th><th>Applicability</th></tr>",
        *(f"<tr><td>{c.get('Rule','')}</td>"
          f"<td>{c.get('Standard','')}</td>"
          f"<td>{c.get('Clause','')}</td>"
          f"<td>{c.get('Detail','')}</td>"
          f"<td>{c.get('Severity','')}</td>"
          f"<td>{c.get('Detail','').split()[0] if 'offending' in c.get('Detail','') else ''}</td>"
          f"<td>{c.get('LawStandard','')}</td>"
          f"<td>{c.get('Jurisdiction','')}</td>"
          f"<td>{c.get('LawDescription','')}</td>"
          f"<td>{c.get('Applicability','')}</td>"
          "</tr>" for c in (compliance or []) if c.get('LawStandard')),  # Only show if LawStandard present
        "</table></div>",
        # ML/AI Fraud Risk Analysis
        "<div class='section ml-section'><h2>5. ML/AI Fraud Risk Analysis</h2>",
        ml_fraud_table.to_html(index=False, escape=False) if ml_fraud_table is not None else "",
        "</div>",
        # Red Flags & Anomalies
        "<div class='section'><h2>6. Red Flags & Anomalies</h2>",
        *(f"<h3>Red Flag {i+1}</h3>" + flagged.to_html(index=False, escape=False) for i, flagged in enumerate(red_flags or [])),
        "</div>",
        # Advisory Notes
        "<div class='section advisory'><h2>7. Advisory Notes</h2>",
        "<ul>",
        *(f"<li>{note}</li>" for note in (advisory_notes or [])),
        "</ul></div>",
        # Appendices (optional)
        "<div class='section'><h2>8. Appendices</h2><p>Additional supporting documents and data can be included here.</p></div>",
        "<footer>© Nxera — SaaS Solutions | This is a system-generated audit report.</footer>",
        "</body></html>"
    ]
    print("[PDF DEBUG] Starting PDF generation...")
    print(f"[PDF DEBUG] Summary: {summary}")
    print(f"[PDF DEBUG] Issues: {type(issues)}, length: {len(issues) if hasattr(issues, 'len') else 'n/a'}")
    print(f"[PDF DEBUG] Opinion: {opinion}")
    print(f"[PDF DEBUG] Ratios: {ratios}")
    if inc is not None:
        print(f"[PDF DEBUG] Income Statement shape: {inc.shape}")
    if cf is not None:
        print(f"[PDF DEBUG] Cash Flow shape: {cf.shape}")
    if bs is not None:
        print(f"[PDF DEBUG] Balance Sheet shape: {bs.shape}")
    if compliance is not None:
        print(f"[PDF DEBUG] Compliance: {type(compliance)}, length: {len(compliance)}")
    if ml_fraud_table is not None:
        print(f"[PDF DEBUG] ML Fraud Table shape: {ml_fraud_table.shape}")
    if red_flags is not None:
        print(f"[PDF DEBUG] Red Flags: {type(red_flags)}, length: {len(red_flags)}")
    if advisory_notes is not None:
        print(f"[PDF DEBUG] Advisory Notes: {type(advisory_notes)}, length: {len(advisory_notes)}")
    print("[PDF DEBUG] Building HTML...")
    html = "".join(html_parts)
    print("[PDF DEBUG] HTML built. Length:", len(html))
    # Optionally print a snippet of the HTML
    print("[PDF DEBUG] HTML Preview:", html[:1000])
    buffer = io.BytesIO()
    print("[PDF DEBUG] Calling pisa.CreatePDF...")
    pisa_status = pisa.CreatePDF(html, dest=buffer)
    print("[PDF DEBUG] pisa_status.err:", getattr(pisa_status, 'err', None))
    if getattr(pisa_status, 'err', 0):
        print("[PDF DEBUG] PDF generation failed!")
        error_html = f"<h1>PDF Generation Failed</h1><p>There was an error creating the PDF. Please check your data and try again.</p>"
        buffer = io.BytesIO()
        pisa.CreatePDF(error_html, dest=buffer)
        buffer.seek(0)
        return buffer.read()
    buffer.seek(0)
    print("[PDF DEBUG] PDF generation succeeded.")
    return buffer.read()