"""Builds the synthetic test set with known planted defects. All people and policies are fictional.

dev: standard wording, used for tuning. holdout: different labels and DD/MM/YYYY dates, kept unseen.
"""
import io
import json
import random
import shutil
from copy import deepcopy
from dataclasses import dataclass, field
from datetime import date, timedelta
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

OUT = Path(__file__).parent / "folders"
AS_OF = date(2026, 11, 1)
CRITICAL = {"STR-002", "SIG-001", "SIG-002", "POL-001"}

STYLES = {
    "dev": {"policy": "Policy Number", "proposer": "Proposer", "location": "Risk Location", "sum": "Sum Insured",
            "effective": "Effective Date", "doc_date": "Date", "fmt": "%Y-%m-%d", "grade": "Risk Grade", "under": "Underwriter",
            "condition": "Property Condition", "fire": "Fire Protection", "surveyor": "Surveyor", "form": "Form Version",
            "app": "INSURANCE APPLICATION", "risk": "RISK ASSESSMENT REPORT", "insp": "INSPECTION REPORT", "disc": "DISCLOSURE AGREEMENT"},
    "holdout": {"policy": "Proposal Ref No.", "proposer": "Name of Insured", "location": "Premises Address", "sum": "Amount Insured (INR)",
                "effective": "Cover Commences On", "doc_date": "Dated", "fmt": "%d/%m/%Y", "grade": "Hazard Classification", "under": "Assessed By",
                "condition": "State of Premises", "fire": "Fire Safety Arrangements", "surveyor": "Surveyed By", "form": "Form Ref",
                "app": "PROPOSAL FOR COMMERCIAL PROPERTY COVER", "risk": "UNDERWRITING RISK NOTE", "insp": "SURVEYOR'S REPORT", "disc": "KEY INFORMATION AND ACKNOWLEDGEMENT"},
}
COMPANIES = ["Sahyog Textiles Pvt Ltd", "Narmada Cold Storage LLP", "Kaveri Auto Components Ltd", "Deccan Paper Mills Ltd",
             "Ganga Food Processors Pvt Ltd", "Malabar Spice Traders", "Aravalli Ceramics Ltd", "Konkan Packaging Works",
             "Vindhya Steel Fabricators", "Nilgiri Tea Exports", "Satpura Plastics Pvt Ltd", "Godavari Garments LLP"]
CITIES = ["Plot 14, MIDC Bhosari, Pune", "Unit 7, Peenya Industrial Area, Bengaluru", "Survey 212, Sanand GIDC, Ahmedabad",
          "Shed 9, Ambattur Estate, Chennai", "Block C, Noida Sector 63", "Plot 3, Patancheru, Hyderabad"]


@dataclass
class Doc:
    kind: str
    filename: str = ""
    policy: str = ""
    when: date = None
    signed: bool = True
    scanned: bool = False
    values: dict = field(default_factory=dict)


def build_docs(policy, rng):
    company, location = rng.choice(COMPANIES), rng.choice(CITIES)
    applied = date(2026, 1, 5) + timedelta(days=rng.randint(0, 200))
    effective = applied + timedelta(days=30)
    shared = {"proposer": company, "location": location, "sum": f"{rng.randint(5, 90) * 10_000_000:,}"}
    docs = {
        "Application": Doc("Application", when=applied, values={**shared, "effective": effective}),
        "Risk_Assessment": Doc("Risk_Assessment", when=applied + timedelta(days=4), values={**shared, "grade": rng.choice(["Low", "Medium"]), "under": "R. Menon"}),
        "Inspection_Report": Doc("Inspection_Report", when=applied + timedelta(days=9), values={**shared, "condition": "Good, well maintained", "fire": "Hydrants and sprinklers tested", "surveyor": "A. Kulkarni"}),
        "Signed_Disclosure": Doc("Signed_Disclosure", when=applied + timedelta(days=14), values={"proposer": company, "form": "DF-2025", "exclusions": True}),
    }
    for doc in docs.values():
        doc.policy = policy
    return docs


def name_docs(policy, docs):
    for doc_type, doc in docs.items():
        doc.filename = doc.filename or f"{policy}_{doc_type}_{doc.when.isoformat()}.pdf"


def shift_all(docs, days):
    for doc in docs.values():
        doc.when += timedelta(days=days)
    docs["Application"].values["effective"] += timedelta(days=days)


def _missing_doc(p, d): del d["Inspection_Report"]; return ["STR-002"]
def _bad_name(p, d): d["Application"].filename = f"{p}_App_{d['Application'].when}.pdf"; return ["NAM-001"]
def _legacy_name(p, d): d["Risk_Assessment"].filename = f"{p}_UW Risk Sheet_{d['Risk_Assessment'].when}.pdf"; return ["NAM-001"]
def _foreign_name(p, d): d["Inspection_Report"].filename = "survey_final_v2.pdf"; return ["NAM-001", "STR-001"]
def _duplicate(p, d):
    copy = deepcopy(d["Signed_Disclosure"]); copy.filename = f"{p}_Signed_Disclosure_{copy.when}_v2.pdf"
    d["Signed_Disclosure_copy"] = copy
    return ["STR-003", "NAM-001"]
def _unsigned(kind, rule):
    def apply(p, d): d[kind].signed = False; return [rule]
    return apply
def _wrong_policy(p, d): d["Risk_Assessment"].policy = "POL888888"; return ["POL-001"]
def _date_order(p, d): d["Risk_Assessment"].when = d["Application"].when - timedelta(days=3); return ["DAT-001"]
def _after_effective(p, d): d["Signed_Disclosure"].when = d["Application"].values["effective"] + timedelta(days=5); return ["DAT-002"]
def _expired(p, d): shift_all(d, -1250); return ["DAT-003"]
def _old_form(p, d): d["Signed_Disclosure"].values["form"] = "DF-2021"; return ["FRM-001"]
def _missing_sum(p, d): d["Application"].values["sum"] = ""; return ["CNT-001"]
def _missing_exclusions(p, d): d["Signed_Disclosure"].values["exclusions"] = False; return ["CNT-002"]
def _missing_grade(p, d): d["Risk_Assessment"].values["grade"] = ""; return ["CNT-003"]
def _no_fire(p, d): d["Inspection_Report"].values["fire"] = ""; return ["CNT-004"]
def _name_conflict(p, d): d["Risk_Assessment"].values["proposer"] = "Tapti Chemicals Ltd"; return ["POL-002"]
def _filename_date(p, d): d["Inspection_Report"].filename = f"{p}_Inspection_Report_{d['Inspection_Report'].when + timedelta(days=30)}.pdf"; return ["NAM-002"]
def _high_grade(p, d): d["Risk_Assessment"].values["grade"] = "High"; return []
def _scanned(p, d):
    for doc in d.values():
        doc.scanned = True
    return []


DEFECTS = {
    "missing_doc": _missing_doc, "bad_name": _bad_name, "legacy_name": _legacy_name, "foreign_name": _foreign_name, "duplicate": _duplicate,
    "unsigned_app": _unsigned("Application", "SIG-001"), "unsigned_disclosure": _unsigned("Signed_Disclosure", "SIG-002"),
    "unsigned_risk": _unsigned("Risk_Assessment", "SIG-003"), "unsigned_inspection": _unsigned("Inspection_Report", "SIG-004"),
    "wrong_policy": _wrong_policy, "date_order": _date_order, "after_effective": _after_effective, "expired": _expired,
    "old_form": _old_form, "missing_sum": _missing_sum, "missing_exclusions": _missing_exclusions, "missing_grade": _missing_grade,
    "no_fire": _no_fire, "name_conflict": _name_conflict, "filename_date": _filename_date, "high_grade": _high_grade, "scanned": _scanned,
}
PLANS = {
    "dev": [[], ["scanned"], ["missing_doc"], ["bad_name", "unsigned_app"], ["wrong_policy"], ["date_order", "old_form"],
            ["unsigned_disclosure", "scanned"], ["expired"], ["missing_sum", "name_conflict"], ["duplicate"], ["high_grade"],
            ["after_effective", "missing_exclusions"]],
    "holdout": [[], ["scanned"], ["high_grade"], ["legacy_name", "unsigned_risk"], ["foreign_name"], ["filename_date", "no_fire"],
                ["wrong_policy", "date_order", "scanned"], ["unsigned_inspection"], ["missing_grade", "old_form"],
                ["missing_doc", "name_conflict"], ["unsigned_app", "scanned"], ["expired", "missing_exclusions"]],
}


def page_lines(doc, s):
    v = doc.values
    head = {"Application": s["app"], "Risk_Assessment": s["risk"], "Inspection_Report": s["insp"], "Signed_Disclosure": s["disc"]}[doc.kind]
    lines = [head, "", f"{s['policy']}: {doc.policy}", f"{s['proposer']}: {v['proposer']}"]
    fmt = lambda d: d.strftime(s["fmt"])
    if "location" in v:
        lines += [f"{s['location']}: {v['location']}", f"{s['sum']}: {v['sum']}"]
    lines.append(f"{s['doc_date']}: {fmt(doc.when)}")
    if doc.kind == "Application":
        lines += [f"{s['effective']}: {fmt(v['effective'])}", "I declare that the above information is true."]
    elif doc.kind == "Risk_Assessment":
        lines += [f"{s['grade']}: {v['grade']}", f"{s['under']}: {v['under']}"]
    elif doc.kind == "Inspection_Report":
        lines += [f"{s['condition']}: {v['condition']}", f"{s['fire']}: {v['fire']}", f"{s['surveyor']}: {v['surveyor']}"]
    else:
        lines.insert(2, f"{s['form']}: {v['form']}")
        if v["exclusions"]:
            lines += ["Exclusions:", "1. War and nuclear perils", "2. Wilful misconduct", "3. Gradual deterioration"]
        lines.append("I acknowledge receipt of this disclosure and accept its terms.")
    return lines


def scribble(rng, x, y):
    points, px = [], x
    for _ in range(9):
        px += rng.randint(8, 16)
        points.append((px, y + rng.randint(-11, 11)))
    return [(x, y)] + points


def render_digital(doc, s, rng):
    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer)
    y = 790
    for line in page_lines(doc, s):
        pdf.drawString(80, y, line)
        y -= 22
    y -= 26
    pdf.drawString(80, y, "Signature: ____________________")
    if doc.signed:
        path = pdf.beginPath()
        points = scribble(rng, 150, y + 8)
        path.moveTo(*points[0])
        for point in points[1:]:
            path.lineTo(*point)
        pdf.drawPath(path)
    pdf.save()
    return buffer.getvalue()


def render_scanned(doc, s, rng):
    image = Image.new("L", (1240, 1754), 248)
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default(size=30)
    y = 130
    for line in page_lines(doc, s):
        draw.text((130, y), line, fill=25, font=font)
        y += 50
    y += 60
    draw.text((130, y), "Signature: ____________________", fill=25, font=font)
    if doc.signed:
        draw.line(scribble(rng, 300, y + 8), fill=20, width=3)
    image = image.rotate(rng.uniform(-1.2, 1.2), fillcolor=248)
    pixels = image.load()
    for _ in range(9000):
        pixels[rng.randrange(1240), rng.randrange(1754)] = rng.choice((120, 200))
    png = io.BytesIO()
    image.save(png, "PNG")
    png.seek(0)
    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer)
    pdf.drawImage(ImageReader(png), 0, 0, width=595, height=842)
    pdf.save()
    return buffer.getvalue()


def expected_renewal(rules, high):
    if CRITICAL & set(rules):
        return "Recommend Hold - Compliance Escalation"
    if rules or high:
        return "Recommend Manual Underwriter Review"
    return "Recommend Renewal - Underwriter Approval Required"


def main():
    shutil.rmtree(OUT, ignore_errors=True)
    truth = {"as_of": AS_OF.isoformat(), "folders": {}}
    rng = random.Random(11)
    for split, base in (("dev", 100001), ("holdout", 200001)):
        for index, plan in enumerate(PLANS[split]):
            policy = f"POL{base + index}"
            docs = build_docs(policy, rng)
            rules = []
            ordered = sorted(plan, key=lambda name: name == "scanned")  # scan flag must reach duplicates too
            naming = {"bad_name", "legacy_name", "foreign_name", "duplicate", "filename_date"}
            for name in sorted(ordered, key=lambda n: n in naming):
                rules += DEFECTS[name](policy, docs)
            name_docs(policy, docs)
            folder = OUT / split / policy
            folder.mkdir(parents=True)
            for doc in docs.values():
                render = render_scanned if doc.scanned else render_digital
                (folder / doc.filename).write_bytes(render(doc, STYLES[split], rng))
            truth["folders"][policy] = {"split": split, "defects": plan, "expected_rules": sorted(set(rules)),
                                        "expected_renewal": expected_renewal(rules, "high_grade" in plan)}
    (Path(__file__).parent / "ground_truth.json").write_text(json.dumps(truth, indent=2))
    print(f"Wrote {len(truth['folders'])} folders to {OUT}")


if __name__ == "__main__":
    main()
