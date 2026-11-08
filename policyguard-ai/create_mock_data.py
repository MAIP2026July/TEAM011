import os
from reportlab.pdfgen import canvas

def create_pdf(filename, content):
    c = canvas.Canvas(filename)
    y = 800
    for line in content:
        c.drawString(100, y, line)
        y -= 20
    c.save()

os.makedirs("mock_data/compliant_folder", exist_ok=True)
os.makedirs("mock_data/non_compliant_folder", exist_ok=True)

# 1. Compliant Folder
create_pdf("mock_data/compliant_folder/POL123456_Application_2023-10-27.pdf", [
    "INSURANCE APPLICATION",
    "Policy Number: POL123456",
    "Applicant: John Doe",
    "Effective Date: 2023-10-27",
    "All information is accurate.",
    "Signature: [John Doe Signed]"
])
create_pdf("mock_data/compliant_folder/POL123456_Risk_Assessment_2023-10-25.pdf", [
    "RISK ASSESSMENT REPORT",
    "Policy Number: POL123456",
    "Assessment Date: 2023-10-25",
    "Risk Level: Low",
    "Signature: [Underwriter Signed]"
])
create_pdf("mock_data/compliant_folder/POL123456_Inspection_Report_2023-10-26.pdf", [
    "INSPECTION REPORT",
    "Policy Number: POL123456",
    "Inspection Date: 2023-10-26",
    "Property Condition: Excellent",
    "Signature: [Inspector Signed]"
])
create_pdf("mock_data/compliant_folder/POL123456_Signed_Disclosure_2023-10-27.pdf", [
    "DISCLOSURE AGREEMENT",
    "Policy Number: POL123456",
    "Date: 2023-10-27",
    "I acknowledge the terms.",
    "Signature: [John Doe Signed]"
])

# 2. Non-Compliant Folder (Missing docs, bad names, content issues)
create_pdf("mock_data/non_compliant_folder/POL999999_App_2023-11-01.pdf", [ # Bad name, no signature
    "INSURANCE APPLICATION",
    "Policy Number: POL999999",
    "Applicant: Jane Smith",
    "Effective Date: 2023-11-01",
    "All information is accurate.",
    "Signature: "
])
create_pdf("mock_data/non_compliant_folder/POL999999_Risk_Assessment_2023-11-01.pdf", [ # Wrong policy number inside
    "RISK ASSESSMENT REPORT",
    "Policy Number: POL888888", 
    "Assessment Date: 2023-11-01",
    "Risk Level: High",
    "Signature: [Underwriter Signed]"
])
create_pdf("mock_data/non_compliant_folder/POL999999_Signed_Disclosure_2023-11-01.pdf", [ # Date inconsistency
    "DISCLOSURE AGREEMENT",
    "Policy Number: POL999999",
    "Date: 2020-01-01", 
    "I acknowledge the terms.",
    "Signature: [Jane Smith Signed]"
])
# Missing Inspection Report

print("Mock data generated in mock_data/")
