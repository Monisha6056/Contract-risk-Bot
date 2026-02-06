import streamlit as st
import PyPDF2
import docx
import re


def extract_text(file):
    if file.name.endswith(".pdf"):
        reader = PyPDF2.PdfReader(file)
        return " ".join(page.extract_text() or "" for page in reader.pages)

    if file.name.endswith(".docx"):
        document = docx.Document(file)
        return " ".join(p.text for p in document.paragraphs)

    if file.name.endswith(".txt"):
        return file.read().decode("utf-8")

    return ""


def classify_contract(text):
    t = text.lower()
    if "employment" in t:
        return "Employment Contract"
    if "lease" in t or "rent" in t:
        return "Lease Agreement"
    if "service" in t or "vendor" in t:
        return "Service Agreement"
    if "confidential" in t or "nda" in t:
        return "Non-Disclosure Agreement"
    return "Commercial Contract"



def extract_clauses(text):
    clauses = []
    for line in text.split("\n"):
        line = line.strip()
        if len(line) > 40:
            clauses.append(line)
    return clauses


def identify_clause_type(clause):
    c = clause.lower()
    if "terminate" in c:
        return "Termination Clause"
    if "penalty" in c:
        return "Penalty Clause"
    if "liable" in c or "indemn" in c:
        return "Liability / Indemnity Clause"
    if "jurisdiction" in c or "governed by" in c:
        return "Jurisdiction Clause"
    if "non compete" in c or "intellectual property" in c:
        return "IP / Non-Compete Clause"
    return "General Obligation Clause"


def extract_entities(text):
    return {
        "Parties": re.findall(r"\b[A-Z][a-zA-Z]+\s(?:Services|Solutions|Ltd|Private)\b", text),
        "Dates": re.findall(r"\b\d{1,2}\s\w+\s\d{4}\b", text),
        "Amounts": re.findall(r"INR\s?\d+[,\d]*", text),
        "Jurisdiction": "India" if "india" in text.lower() else "Not Specified"
    }



def assess_risk(clause):
    c = clause.lower()
    risks = []
    suggestions = []

    if "without notice" in c:
        risks.append("Unilateral termination")
        suggestions.append("Add mutual notice period")

    if "sole discretion" in c:
        risks.append("One-sided discretion")
        suggestions.append("Balance rights of both parties")

    if "penalty" in c:
        risks.append("Financial penalty")
        suggestions.append("Cap penalty amount")

    if "fully liable" in c or "unlimited liability" in c:
        risks.append("Unlimited liability")
        suggestions.append("Introduce liability cap")

    if not risks:
        return "Low", [], ["Clause appears balanced"]

    if len(risks) >= 2:
        return "High", risks, suggestions

    return "Medium", risks, suggestions


def overall_risk_score(risks):
    if "High" in risks:
        return "High"
    if "Medium" in risks:
        return "Medium"
    return "Low"


def contract_summary(contract_type, entities, risk):
    return f"""
This document is identified as a **{contract_type}**.

The system extracted key legal entities such as **parties, dates, monetary amounts, and jurisdiction** using rule-based NLP.

The **overall contract risk level** is assessed as **{risk}**.

High-risk or medium-risk clauses may expose SMEs to legal or financial disadvantage and should be renegotiated before execution.
"""



st.set_page_config(page_title="Contract Analysis & Risk Assessment Bot")
st.title(" Contract Analysis & Risk Assessment Bot")

uploaded_file = st.file_uploader(
    "Upload Contract (PDF / DOCX / TXT)",
    type=["pdf", "docx", "txt"]
)

if uploaded_file:
    text = extract_text(uploaded_file)

    if not text.strip():
        st.error("Unable to extract text from document.")
        st.stop()

    contract_type = classify_contract(text)
    entities = extract_entities(text)
    clauses = extract_clauses(text)

    st.subheader(" Contract Type")
    st.write(contract_type)

    st.subheader(" Named Entity Recognition")
    st.json(entities)

    st.subheader(" Clause-by-Clause Risk Assessment")

    risk_levels = []

    for i, clause in enumerate(clauses, 1):
        clause_type = identify_clause_type(clause)
        risk, issues, suggestions = assess_risk(clause)
        risk_levels.append(risk)

        st.markdown(f"### Clause {i}")
        st.write(clause)
        st.write("**Clause Type:**", clause_type)
        st.write("**Risk Level:**", risk)
        st.write("**Detected Issues:**", ", ".join(issues) if issues else "None")

        st.write("**Suggested Renegotiation:**")
        for s in suggestions:
            st.write("- ", s)

        st.markdown("---")

    overall_risk = overall_risk_score(risk_levels)

    st.subheader(" Overall Contract Risk Score")
    st.metric("Contract Risk Level", overall_risk)

    st.subheader(" Simplified Contract Summary")
    st.write(contract_summary(contract_type, entities, overall_risk))
