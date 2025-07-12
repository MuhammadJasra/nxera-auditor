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
    compliance=None
) -> bytes:
    """
    Generate a full audit PDF report with Nxera branding.
    """

    html_parts = [
        "<html><head><style>",
        """
        @page {
            size: A4;
            margin: 50px;
        }
        body {
            font-family: Arial, sans-serif;
            font-size: 12px;
            color: #333;
        }
        header {
            border-bottom: 2px solid #007acc;
            padding-bottom: 10px;
            margin-bottom: 20px;
        }
        footer {
            position: fixed;
            bottom: 30px;
            left: 0;
            right: 0;
            text-align: center;
            font-size: 10px;
            color: #777;
        }
        h1, h2, h3 {
            color: #007acc;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 10px;
            margin-bottom: 20px;
        }
        th, td {
            border: 1px solid #ccc;
            padding: 8px;
            text-align: left;
        }
        th {
            background-color: #f0f8ff;
        }
        ul {
            margin-top: 0;
        }
        """,
        "</style></head><body>",

        "<header>",
        "<h1>NXERA — SaaS Audit Solutions</h1>",
        "<p>Empowering transparency, automation & trust in financial systems.</p>",
        "</header>",

        "<h2>📋 Executive Summary</h2>",
        f"<pre>{summary}</pre>"
    ]

    if ratios:
        html_parts.append("<h2>📊 Financial Ratios</h2>")
        html_parts.append("<ul>")
        for key, value in ratios.items():
            html_parts.append(f"<li><strong>{key}:</strong> {value:,.2f}</li>")
        html_parts.append("</ul>")

    html_parts.append("<h2>🧠 AI Audit Opinion</h2>")
    html_parts.append(f"<p>{opinion}</p>")

    # Compliance Table
    if compliance:
        html_parts.append("<h2>🛡️ Compliance Findings</h2>")
        html_parts.append("<table><tr>"
                          "<th>Rule ID</th>"
                          "<th>Standard</th>"
                          "<th>Clause</th>"
                          "<th>Description</th>"
                          "<th>Severity</th>"
                          "<th>Breach Count</th>"
                          "</tr>")
        for c in compliance:
            html_parts.append(
                f"<tr>"
                f"<td>{c.get('Rule','')}</td>"
                f"<td>{c.get('Standard','')}</td>"
                f"<td>{c.get('Clause','')}</td>"
                f"<td>{c.get('Detail','')}</td>"
                f"<td>{c.get('Severity','')}</td>"
                f"<td>{c.get('Detail','').split()[0] if 'offending' in c.get('Detail','') else ''}</td>"
                f"</tr>"
            )
        html_parts.append("</table>")

    html_parts.append("<h2>📑 Income Statement</h2>")
    if inc is not None:
        html_parts.append(inc.to_html(index=False, escape=False))
    html_parts.append("<h2>💸 Cash Flow Statement</h2>")
    if cf is not None:
        html_parts.append(cf.to_html(index=False, escape=False))
    html_parts.append("<h2>💼 Balance Sheet Estimate</h2>")
    if bs is not None:
        html_parts.append(bs.to_html(index=False, escape=False))

    for i, df in enumerate(issues, 1):
        html_parts.append(f"<h3>⚠️ Issue {i}</h3>")
        html_parts.append(df.to_html(index=False, escape=False))

    html_parts.append("""
        <footer>
            © Nxera — SaaS Solutions | This is a system-generated audit report.
        </footer>
    """)

    html_parts.append("</body></html>")

    html = "".join(html_parts)

    buffer = io.BytesIO()
    pisa_status = pisa.CreatePDF(html, dest=buffer)
    buffer.seek(0)
    return buffer.read()