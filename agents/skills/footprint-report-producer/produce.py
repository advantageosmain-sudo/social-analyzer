#!/usr/bin/env python3
"""
footprint-report-producer — turn social-analyzer scan JSON into a customer
deliverable (PDF + Markdown source).

Gate behaviour (owner approval preserved):
  * If the engagement's `production` gate is APPROVED in the ledger, the PDF is
    marked FINAL and registered as a `final` deliverable.
  * Otherwise the PDF carries a DRAFT / INTERNAL REVIEW watermark and is
    registered as `draft`. The script never upgrades a draft on its own.
  * The file is written to 20_Deliverables/<engagement>/ (draft) or
    20_Deliverables/<engagement>/outbox/ (final). Nothing is sent anywhere —
    customer communication is a separate, human-executed gate.

Usage:
  python3 agents/skills/footprint-report-producer/produce.py \
      --engagement eng-xxxx --customer "Acme Legal" --subject "johndoe" \
      --scan agents/workspace/10_Engagements/eng-xxxx/scan-johndoe.json \
      [--actor agent:production-agent] [--analyst "Jane Doe"]
"""
import argparse
import datetime as _dt
import json
import os
import re
import sys

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle)

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, os.path.join(REPO, "agents", "skills", "business-records-ledger"))
import ledger  # noqa: E402

DELIV = os.path.join(REPO, "agents", "workspace", "20_Deliverables")


def rate_num(r):
    m = re.search(r"([\d.]+)", str(r or ""))
    return float(m.group(1)) if m else 0.0


def band(r):
    n = rate_num(r)
    return "High" if n >= 90 else "Medium" if n >= 50 else "Low"


def esc(s):
    return (str(s or "")).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def build_markdown(ctx):
    d = ctx["scan"]
    det = sorted(d.get("detected", []), key=lambda x: -rate_num(x.get("rate")))
    unk = d.get("unknown", [])
    fail = d.get("failed", [])
    L = []
    L += [f"# Digital Footprint Report — {ctx['subject']}", "",
          f"**Prepared for:** {ctx['customer']}  ", f"**Engagement:** {ctx['engagement']}  ",
          f"**Status:** {ctx['status']}  ", f"**Date:** {ctx['date']}  ", f"**Analyst:** {ctx['analyst']}", ""]
    L += ["## 1. Summary", "",
          f"A fast-mode public-profile sweep was run for the identifier **{ctx['subject']}** against "
          f"{ctx['sites_desc']} using social-analyzer. "
          f"**{len(det)}** profile(s) were detected, **{len(unk)}** returned inconclusive, and **{len(fail)}** could not be checked.", ""]
    L += ["| Confidence band | Count |", "|---|---|"]
    for b in ("High", "Medium", "Low"):
        L.append(f"| {b} | {sum(1 for x in det if band(x.get('rate')) == b)} |")
    L += ["", "## 2. Detected profiles", ""]
    if det:
        L += ["| # | Profile | Rate | Band | Page title |", "|---|---|---|---|---|"]
        for i, x in enumerate(det, 1):
            L.append(f"| {i} | {x.get('link','')} | {x.get('rate','')} | {band(x.get('rate'))} | {(x.get('title') or '').strip()[:80]} |")
    else:
        L.append("_No profiles detected for this identifier in the selected scope._")
    L += ["", "## 3. Inconclusive / unreachable", ""]
    if unk or fail:
        L += ["| Site | Outcome |", "|---|---|"]
        L += [f"| {x.get('link','')} | inconclusive |" for x in unk]
        L += [f"| {x.get('link','')} | unreachable / failed |" for x in fail]
    else:
        L.append("_None._")
    L += ["", "## 4. Method & limitations", "",
          "- Source: publicly reachable pages only; no authentication, no private data, no account access.",
          "- Detection rate is social-analyzer's heuristic score (0–100). It indicates a page matching the identifier exists — **not** that the same person owns every account.",
          "- Username reuse by unrelated people is common; medium/low bands require human corroboration before any conclusion.",
          "- Fast mode (HTTP) was used; sites requiring JavaScript rendering may appear as inconclusive/failed.",
          "- Results are a point-in-time snapshot (" + ctx["captured"] + ").", "",
          "## 5. Use restrictions", "",
          "This report is provided for the lawful purpose stated in the engagement record. It must not be used for harassment, discrimination, "
          "or any decision regulated by consumer-reporting or employment law without the required legal basis and notices.", ""]
    if ctx["status"].startswith("DRAFT"):
        L += ["> **DRAFT — INTERNAL REVIEW.** Not approved for release. Production gate: " + ctx["gate"]["status"] + ".", ""]
    return "\n".join(L), det, unk, fail


def build_pdf(path, ctx, det, unk, fail):
    styles = getSampleStyleSheet()
    H1 = ParagraphStyle("H1", parent=styles["Title"], fontSize=20, spaceAfter=6)
    H2 = ParagraphStyle("H2", parent=styles["Heading2"], textColor=colors.HexColor("#1f3b57"), spaceBefore=12)
    B = styles["BodyText"]; B.leading = 14
    small = ParagraphStyle("small", parent=B, fontSize=8, leading=10, textColor=colors.grey)
    cell = ParagraphStyle("cell", parent=B, fontSize=8, leading=10)
    draft = ctx["status"].startswith("DRAFT")

    def on_page(canvas, doc):
        canvas.saveState()
        canvas.setFont("Helvetica", 8); canvas.setFillColor(colors.grey)
        canvas.drawString(0.75 * inch, 0.5 * inch, f"{ctx['customer']} · {ctx['engagement']} · {ctx['status']}")
        canvas.drawRightString(letter[0] - 0.75 * inch, 0.5 * inch, f"Page {doc.page}")
        if draft:
            canvas.setFont("Helvetica-Bold", 60); canvas.setFillColor(colors.Color(0.85, 0.2, 0.2, alpha=0.12))
            canvas.translate(letter[0] / 2, letter[1] / 2); canvas.rotate(35)
            canvas.drawCentredString(0, 0, "DRAFT — INTERNAL REVIEW")
        canvas.restoreState()

    doc = SimpleDocTemplate(path, pagesize=letter, leftMargin=0.75 * inch, rightMargin=0.75 * inch,
                            topMargin=0.8 * inch, bottomMargin=0.8 * inch,
                            title=f"Digital Footprint Report — {ctx['subject']}", author=ctx["analyst"])
    S = []
    S += [Spacer(1, 1.6 * inch), Paragraph("Digital Footprint Report", H1),
          Paragraph(f"Subject identifier: <b>{esc(ctx['subject'])}</b>", ParagraphStyle("c", parent=B, alignment=TA_CENTER, fontSize=13)),
          Spacer(1, 0.4 * inch)]
    meta = [["Prepared for", ctx["customer"]], ["Engagement", ctx["engagement"]], ["Status", ctx["status"]],
            ["Date", ctx["date"]], ["Analyst", ctx["analyst"]], ["Tool", ctx["scan"].get("_meta", {}).get("tool", "social-analyzer")]]
    t = Table([[Paragraph(f"<b>{esc(a)}</b>", B), Paragraph(esc(b), B)] for a, b in meta], colWidths=[1.6 * inch, 4.4 * inch])
    t.setStyle(TableStyle([("LINEBELOW", (0, 0), (-1, -1), 0.25, colors.lightgrey), ("VALIGN", (0, 0), (-1, -1), "TOP")]))
    S += [t, PageBreak()]

    S += [Paragraph("1. Summary", H2),
          Paragraph(f"A fast-mode public-profile sweep was run for <b>{esc(ctx['subject'])}</b> against {esc(ctx['sites_desc'])}. "
                    f"<b>{len(det)}</b> profile(s) detected, <b>{len(unk)}</b> inconclusive, <b>{len(fail)}</b> unreachable.", B), Spacer(1, 6)]
    bands = [["Confidence band", "Count", "Meaning"],
             ["High (≥90)", sum(1 for x in det if band(x.get("rate")) == "High"), "Strong page-level match"],
             ["Medium (50–89)", sum(1 for x in det if band(x.get("rate")) == "Medium"), "Needs corroboration"],
             ["Low (<50)", sum(1 for x in det if band(x.get("rate")) == "Low"), "Weak signal"]]
    bt = Table(bands, colWidths=[1.7 * inch, 0.8 * inch, 3.5 * inch])
    bt.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f3b57")), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                            ("GRID", (0, 0), (-1, -1), 0.25, colors.lightgrey), ("FONTSIZE", (0, 0), (-1, -1), 9)]))
    S += [bt]

    S += [Paragraph("2. Detected profiles", H2)]
    if det:
        rows = [["#", "Profile", "Rate", "Band", "Page title"]]
        for i, x in enumerate(det, 1):
            rows.append([str(i), Paragraph(esc(x.get("link", "")), cell), x.get("rate", ""), band(x.get("rate")),
                         Paragraph(esc((x.get("title") or "").strip()[:90]), cell)])
        dt = Table(rows, colWidths=[0.3 * inch, 2.7 * inch, 0.7 * inch, 0.7 * inch, 1.6 * inch], repeatRows=1)
        dt.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f3b57")), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                                ("GRID", (0, 0), (-1, -1), 0.25, colors.lightgrey), ("FONTSIZE", (0, 0), (-1, -1), 8), ("VALIGN", (0, 0), (-1, -1), "TOP")]))
        S += [dt]
    else:
        S += [Paragraph("<i>No profiles detected for this identifier in the selected scope.</i>", B)]

    S += [Paragraph("3. Inconclusive / unreachable", H2)]
    if unk or fail:
        rows = [["Site", "Outcome"]] + [[Paragraph(esc(x.get("link", "")), cell), "inconclusive"] for x in unk] + \
               [[Paragraph(esc(x.get("link", "")), cell), "unreachable / failed"] for x in fail]
        ut = Table(rows, colWidths=[4.2 * inch, 1.8 * inch], repeatRows=1)
        ut.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#5a6b7b")), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                                ("GRID", (0, 0), (-1, -1), 0.25, colors.lightgrey), ("FONTSIZE", (0, 0), (-1, -1), 8)]))
        S += [ut]
    else:
        S += [Paragraph("<i>None.</i>", B)]

    S += [Paragraph("4. Method &amp; limitations", H2)]
    for li in ["Source: publicly reachable pages only; no authentication, no private data, no account access.",
               "The rate is social-analyzer's heuristic score (0–100). It means a matching page exists — not that one person owns every account.",
               "Username reuse by unrelated people is common; medium/low bands require human corroboration.",
               "Fast (HTTP) mode was used; JavaScript-only sites may show as inconclusive or failed.",
               f"Point-in-time snapshot captured {ctx['captured']}."]:
        S += [Paragraph("• " + esc(li), B)]
    S += [Paragraph("5. Use restrictions", H2),
          Paragraph("Provided for the lawful purpose stated in the engagement record. Not for harassment, discrimination, or regulated "
                    "consumer-reporting / employment decisions without the required legal basis and notices.", B),
          Spacer(1, 12), Paragraph(f"Generated by footprint-report-producer · ledger gate production={ctx['gate']['status']}", small)]
    doc.build(S, onFirstPage=on_page, onLaterPages=on_page)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--engagement", required=True)
    ap.add_argument("--customer", required=True)
    ap.add_argument("--subject", required=True, help="identifier that was scanned")
    ap.add_argument("--scan", required=True, help="scan JSON from scan.sh")
    ap.add_argument("--analyst", default="Analyst")
    ap.add_argument("--actor", default="agent:production-agent")
    ap.add_argument("--ledger", default=ledger.DEFAULT_LEDGER)
    ap.add_argument("--out-dir", default=None)
    a = ap.parse_args(argv)

    scan = json.load(open(a.scan, encoding="utf-8"))
    gate = ledger.gate_status(a.ledger, a.engagement, "production")
    final = gate["status"] == "approved"
    status = "FINAL" if final else f"DRAFT — INTERNAL REVIEW"
    meta = scan.get("_meta", {})
    sites = meta.get("websites", "all")
    sites_desc = "the full social-analyzer site catalogue" if sites == "all" else f"the selected sites ({sites})"
    today = _dt.date.today().isoformat()
    ctx = dict(scan=scan, engagement=a.engagement, customer=a.customer, subject=a.subject, analyst=a.analyst, status=status,
               date=today, gate=gate, sites_desc=sites_desc, captured=meta.get("captured", "unknown"))

    out_dir = a.out_dir or os.path.join(DELIV, a.engagement, "outbox" if final else "")
    os.makedirs(out_dir, exist_ok=True)
    safe = re.sub(r"[^A-Za-z0-9_.-]", "_", a.subject)
    base = os.path.join(out_dir, f"footprint-report-{safe}-{today}-{'FINAL' if final else 'DRAFT'}")
    md, det, unk, fail = build_markdown(ctx)
    open(base + ".md", "w", encoding="utf-8").write(md)
    build_pdf(base + ".pdf", ctx, det, unk, fail)

    rec = ledger.append(a.ledger, "deliverable",
                        {"path": os.path.relpath(base + ".pdf", REPO), "sha256": ledger.sha256_file(base + ".pdf"),
                         "status": "final" if final else "draft", "kind": "pdf", "bytes": os.path.getsize(base + ".pdf"),
                         "subject": a.subject, "detected": len(det), "unknown": len(unk), "failed": len(fail)},
                        a.actor, a.engagement)
    print(f"status     : {status}")
    print(f"pdf        : {os.path.relpath(base + '.pdf', REPO)}")
    print(f"markdown   : {os.path.relpath(base + '.md', REPO)}")
    print(f"ledger rec : {rec['id']}  (production gate = {gate['status']})")
    if not final:
        print("NOTE: draft only. Owner must run `ledger.py approve <engagement> production --actor owner:<name>` and re-run to produce FINAL.")
    print("NOTE: nothing has been sent. Customer delivery requires the customer_communication gate and a human action.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
